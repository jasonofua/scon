#!/usr/bin/env python3
"""
SCONIA – Qdrant Cloud ingestion script.

Reads all .txt files from docs/assets/, generates Gemini embeddings
(text-embedding-004 → 768-dim) and upserts them into the Qdrant Cloud
collection 'sconia_legal_documents'.

Usage:
    python scripts/ingest_to_qdrant.py
"""
import asyncio
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

# ── CONFIG ──────────────────────────────────────────────────────────────────
QDRANT_URL    = "https://4fd0031d-c5f4-4783-9bca-f10c8151dfcf.us-central1-0.gcp.cloud.qdrant.io"
QDRANT_KEY    = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZjZlNGI2NzQtN2U1ZS00OTRjLWI4YzAtZTk3ODJjMzk0MjBjIn0.yvjQYV9Mz9arqElPZkEOQxb2bgqQIHadqiHh4pCN57I"
GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")
COLLECTION    = "sconia_legal_documents"
VECTOR_SIZE   = 3072         # gemini-embedding-001 output dimension
BATCH_SIZE    = 5            # chunks per Qdrant upsert call (smaller = safer rate limit)
CHUNK_WORDS   = 600          # target words per chunk
OVERLAP_WORDS = 80           # overlap between chunks
# Model candidates — tried in order until one works
EMBED_MODELS  = ["text-embedding-004", "models/text-embedding-004", "embedding-001"]

DOCS_DIR = Path(__file__).parent.parent / "docs" / "assets"

DOCUMENTS = [
    {"file": "nigeria_constitution_provisions.txt",    "type": "constitution",      "title": "Nigerian Constitution Provisions"},
    {"file": "nigeria_court_hierarchy_and_judges.txt", "type": "judicial_structure","title": "Nigeria Court Hierarchy and Judges"},
    {"file": "nigeria_criminal_code_provisions.txt",   "type": "legislation",       "title": "Nigerian Criminal Code Provisions"},
    {"file": "nigeria_current_judges_profiles.txt",    "type": "judicial_profiles", "title": "Current Nigerian Judges Profiles"},
    {"file": "nigeria_electoral_act_2022.txt",         "type": "legislation",       "title": "Electoral Act 2022 – Federal Republic of Nigeria"},
    {"file": "nigeria_supreme_court_landmark_cases.txt","type": "case_law",         "title": "Nigerian Supreme Court Landmark Cases"},
]

# ── HELPERS ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, max_words: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS):
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    start = 0
    idx = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk = " ".join(words[start:end])
        chunks.append({"text": chunk, "chunk_index": idx})
        idx += 1
        if end == len(words):
            break
        start = end - overlap
    return chunks


EMBED_MODEL = None  # resolved at runtime

async def resolve_embed_model(client) -> str:
    """Try each model candidate and return the first that works."""
    candidates = [
        "models/gemini-embedding-001",
        "models/gemini-embedding-2",
        "models/text-embedding-004",
    ]
    for model in candidates:
        try:
            r = await client.aio.models.embed_content(model=model, contents="test")
            if r.embeddings:
                dim = len(r.embeddings[0].values)
                print(f"  ✅ Embedding model resolved: {model} (dim={dim})")
                return model
        except Exception as e:
            print(f"  ⚠️  Model '{model}' failed: {e}")
    raise RuntimeError("No working Gemini embedding model found.")


async def embed_texts(client, texts: list[str]) -> list[list[float]]:
    """Generate Gemini embeddings for a list of texts (one at a time to be safe)."""
    global EMBED_MODEL
    results = []
    for text in texts:
        response = await client.aio.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
        )
        results.append(response.embeddings[0].values)
        await asyncio.sleep(0.05)  # stay within rate limits
    return results


async def ensure_collection(qclient):
    """Create Qdrant collection if it doesn't exist."""
    from qdrant_client.http import models as qm
    try:
        info = qclient.get_collection(COLLECTION)
        print(f"  ✅ Collection '{COLLECTION}' exists ({info.points_count} points)")
    except Exception:
        print(f"  📦 Creating collection '{COLLECTION}' (size={VECTOR_SIZE}, cosine)…")
        qclient.create_collection(
            collection_name=COLLECTION,
            vectors_config=qm.VectorParams(size=VECTOR_SIZE, distance=qm.Distance.COSINE),
        )
        # payload indexes for fast filtering
        for field, schema in [
            ("document_type", qm.PayloadSchemaType.KEYWORD),
            ("document_id",   qm.PayloadSchemaType.KEYWORD),
        ]:
            qclient.create_payload_index(
                collection_name=COLLECTION,
                field_name=field,
                field_schema=schema,
            )
        print("  ✅ Collection created.")


async def ingest_document(gemini_client, qclient, doc: dict) -> int:
    """Ingest a single document file → Qdrant. Returns number of chunks uploaded."""
    from qdrant_client.http.models import PointStruct

    file_path = DOCS_DIR / doc["file"]
    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}, skipping.")
        return 0

    text = file_path.read_text(encoding="utf-8").strip()
    if not text:
        print(f"  ⚠️  File is empty: {file_path}, skipping.")
        return 0

    doc_id = f"{doc['type']}_{file_path.stem}"
    chunks = chunk_text(text)
    print(f"  📄 {doc['title']} → {len(chunks)} chunks")

    total = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        # Generate embeddings
        vectors = await embed_texts(gemini_client, texts)
        await asyncio.sleep(0.15)  # respect Gemini rate limit

        # Build Qdrant points
        points = []
        for chunk, vector in zip(batch, vectors):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text":          chunk["text"],
                    "document_id":   doc_id,
                    "document_type": doc["type"],
                    "chunk_index":   chunk["chunk_index"],
                    "title":         doc["title"],
                    "file_name":     doc["file"],
                    "source":        "Nigerian Legal Documents",
                    "uploaded_at":   int(datetime.now(timezone.utc).timestamp()),
                },
            ))

        qclient.upsert(collection_name=COLLECTION, points=points)
        total += len(points)
        print(f"    ↳ batch {i//BATCH_SIZE + 1}: {len(points)} vectors upserted")

    return total


# ── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    # Import here so missing deps fail loudly
    try:
        from google import genai
        from qdrant_client import QdrantClient
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install google-genai qdrant-client")
        sys.exit(1)

    # Resolve Gemini key
    key = GEMINI_KEY
    if not key:
        # Try reading from local .env
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        print("❌ GEMINI_API_KEY not found. Set it in .env or export GEMINI_API_KEY=...")
        sys.exit(1)

    print("🏛️  SCONIA – Qdrant Cloud Ingestion")
    print("=" * 55)
    print(f"  Qdrant : {QDRANT_URL}")
    print(f"  Docs   : {DOCS_DIR}")
    print()

    # Force v1 API — text-embedding-004 is not available on v1beta
    from google.genai import types as genai_types
    gemini_client = genai.Client(
        api_key=key,
    )
    qclient = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_KEY,
        timeout=60,
        check_compatibility=False,   # client 1.15 vs server 1.18
    )

    print("🔧 Ensuring Qdrant collection…")
    await ensure_collection(qclient)
    print()

    print("🔍 Resolving Gemini embedding model…")
    global EMBED_MODEL
    EMBED_MODEL = await resolve_embed_model(gemini_client)
    print()

    total_chunks = 0
    for doc in DOCUMENTS:
        print(f"⬆️  Ingesting: {doc['title']}")
        n = await ingest_document(gemini_client, qclient, doc)
        total_chunks += n
        print(f"  ✅ Done ({n} chunks)\n")

    # Final stats
    info = qclient.get_collection(COLLECTION)
    print("=" * 55)
    print(f"🎉 Ingestion complete!")
    print(f"   Chunks uploaded : {total_chunks}")
    print(f"   Total in Qdrant : {info.points_count}")
    print()

    # # Quick sanity search
    # # print("🔍 Sanity check – searching 'fundamental rights'…")
    # # q_vec = await embed_texts(gemini_client, ["fundamental rights"])
    # # results = qclient.search(
    # #     collection_name=COLLECTION,
    # #     query_vector=q_vec[0],
    # #     limit=3,
    # #     score_threshold=0.5,
    # # )
    # # if results:
    # #     for r in results:
    # #         print(f"   score={r.score:.3f} | type={r.payload.get('document_type')} | chunk={r.payload.get('chunk_index')}")
    # #     print("✅ Qdrant search is working!")
    # # else:
    # #     print("⚠️  No results returned — check score_threshold or collection size.")


if __name__ == "__main__":
    asyncio.run(main())
