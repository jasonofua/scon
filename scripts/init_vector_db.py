"""
Initialize vector database and process sample legal documents for SCONIA.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.services.vector_db import vector_db_service
from app.services.embeddings import embedding_service
from app.database import AsyncSessionLocal


async def create_sample_legal_documents():
    """Create sample legal documents for embedding."""
    
    sample_documents = [
        {
            "document_id": "constitution_chapter_iv",
            "document_type": "constitution",
            "title": "Chapter IV - Fundamental Rights",
            "content": """
            Chapter IV of the Nigerian Constitution contains the fundamental rights provisions.
            
            Section 33: Right to Life
            Every person has a right to life, and no one shall be deprived intentionally of his life, save in execution of the sentence of a court in respect of a criminal offence of which he has been found guilty in Nigeria.
            
            Section 34: Right to Dignity of Human Person
            Every individual is entitled to respect for the dignity of his person, and accordingly:
            (a) no person shall be subjected to torture or to inhuman or degrading treatment;
            (b) no person shall be held in slavery or servitude; and
            (c) no person shall be required to perform forced or compulsory labour.
            
            Section 35: Right to Personal Liberty
            Every person shall be entitled to his personal liberty and no person shall be deprived of such liberty save in accordance with a procedure permitted by law.
            
            Section 36: Right to Fair Hearing
            In the determination of his civil rights and obligations, including any question or determination by or against any government or authority, a person shall be entitled to a fair hearing within a reasonable time by a court or other tribunal established by law.
            
            Section 37: Right to Private and Family Life
            The privacy of citizens, their homes, correspondence, telephone conversations and telegraphic communications is hereby guaranteed and protected.
            
            Section 38: Right to Freedom of Thought, Conscience and Religion
            Every person shall be entitled to freedom of thought, conscience and religion, including freedom to change his religion or belief, and freedom (either alone or in community with others, and in public or in private) to manifest and propagate his religion or belief in worship, teaching, practice and observance.
            
            Section 39: Right to Freedom of Expression and the Press
            Every person shall be entitled to freedom of expression, including freedom to hold opinions and to receive and impart ideas and information without interference.
            
            Section 40: Right to Peaceful Assembly and Association
            Every person shall be entitled to assemble freely and associate with other persons, and in particular he may form or belong to any political party, trade union or any other association for the protection of his interests.
            
            Section 41: Right to Freedom of Movement
            Every citizen of Nigeria is entitled to move freely throughout Nigeria and to reside in any part thereof, and no citizen of Nigeria shall be expelled from Nigeria or refused entry thereby or exit therefrom.
            
            Section 42: Right to Freedom from Discrimination
            A citizen of Nigeria of a particular community, ethnic group, place of origin, sex, religion or political opinion shall not, by reason only that he is such a person, be subjected to any form of discrimination.
            
            Section 43: Right to Acquire and Own Immovable Property
            Subject to the provisions of this Constitution, every citizen of Nigeria shall have the right to acquire and own immovable property anywhere in Nigeria.
            
            Section 44: Compulsory Acquisition of Property
            No movable property or any interest in an immovable property shall be taken compulsorily by any authority unless the taking is necessary for a public purpose and in the interest of defence, public safety, public order, public morality or public health.
            """
        },
        {
            "document_id": "supreme_court_structure",
            "document_type": "court_info",
            "title": "Supreme Court of Nigeria Structure and Jurisdiction",
            "content": """
            The Supreme Court of Nigeria is the highest court in Nigeria and the final court of appeal.
            
            Composition:
            The Supreme Court consists of the Chief Justice of Nigeria and such number of Justices of the Supreme Court, not exceeding twenty-one, as may be prescribed by an Act of the National Assembly.
            
            Jurisdiction:
            The Supreme Court has original jurisdiction in disputes between the Federation and a State or between States if and in so far as that dispute involves any question (whether of law or fact) on which the existence or extent of a legal right depends.
            
            The Supreme Court has appellate jurisdiction to hear and determine appeals from the Court of Appeal, and such jurisdiction and powers as may be conferred on it by this Constitution or any Act of the National Assembly.
            
            Current Chief Justice:
            The current Chief Justice of Nigeria is Hon. Justice Olukayode Ariwoola, who was appointed on June 27, 2022.
            
            Court Sessions:
            The Supreme Court sits in Abuja and may sit in any other place in Nigeria as the Chief Justice may, from time to time, appoint.
            
            Filing Requirements:
            Appeals to the Supreme Court must be filed within three months of the judgment of the Court of Appeal, except in criminal matters where leave must be obtained.
            
            Court Fees:
            Filing fees vary depending on the type of case and are prescribed by the Supreme Court Rules.
            """
        },
        {
            "document_id": "court_procedures_filing",
            "document_type": "procedure",
            "title": "Court Filing Procedures and Requirements",
            "content": """
            Filing Procedures at the Supreme Court of Nigeria
            
            1. Preparation of Documents:
            - All documents must be properly typed and formatted
            - Original documents must be accompanied by certified true copies
            - Documents must be bound in the prescribed manner
            
            2. Filing Requirements:
            - Notice of Appeal must be filed within the prescribed time limit
            - Statement of case must accompany the Notice of Appeal
            - All relevant lower court records must be included
            - Proof of service on all parties must be provided
            
            3. Fees and Payments:
            - Filing fees must be paid at the time of filing
            - Fees can be paid by bank draft, certified cheque, or online payment
            - Fee schedules are available at the court registry
            
            4. Service of Process:
            - All parties must be properly served with court documents
            - Proof of service must be filed with the court
            - Service can be personal, by post, or through legal representatives
            
            5. Time Limits:
            - Appeals must be filed within three months of the lower court judgment
            - Extensions of time may be granted in exceptional circumstances
            - Criminal appeals require leave of the court
            
            6. Legal Representation:
            - Parties may appear in person or through legal counsel
            - Legal practitioners must be properly enrolled and in good standing
            - Power of attorney may be required for representation
            
            7. Court Registry:
            - The court registry is open Monday to Friday, 8:00 AM to 4:00 PM
            - Documents can be filed in person or through authorized agents
            - Electronic filing may be available for certain document types
            """
        },
        {
            "document_id": "landmark_cases",
            "document_type": "case",
            "title": "Landmark Supreme Court Cases",
            "content": """
            Notable Supreme Court of Nigeria Cases
            
            1. Attorney General of Ondo State v. Attorney General of the Federation (2002)
            This case dealt with the constitutional powers of state governments versus federal government, particularly regarding the creation of local government areas.
            
            2. Marwa v. Nyako (2012)
            A significant case on electoral law and the powers of the Independent National Electoral Commission (INEC) in conducting elections.
            
            3. Amaechi v. INEC (2008)
            This case established important precedents regarding the substitution of candidates in elections and the role of political parties.
            
            4. Uwais v. State (1982)
            A landmark case on criminal law and the rights of accused persons under the Nigerian legal system.
            
            5. Okogie v. Attorney General of Lagos State (1981)
            This case dealt with religious freedom and the establishment of religious institutions under the Nigerian Constitution.
            
            Legal Principles Established:
            - Separation of powers between federal and state governments
            - Electoral law and democratic processes
            - Fundamental rights protection
            - Criminal justice and due process
            - Religious freedom and tolerance
            
            These cases have shaped Nigerian jurisprudence and continue to be cited in contemporary legal proceedings.
            """
        }
    ]
    
    return sample_documents


async def process_and_embed_documents():
    """Process sample documents and create embeddings."""
    print("Creating sample legal documents...")
    documents = await create_sample_legal_documents()
    
    print("Processing documents and generating embeddings...")
    
    for doc in documents:
        try:
            print(f"Processing: {doc['title']}")
            
            # Generate embeddings for the document
            embedding_records = await embedding_service.embed_document(
                text=doc['content'],
                document_id=doc['document_id'],
                document_type=doc['document_type'],
                metadata={
                    'title': doc['title'],
                    'source': 'sample_data',
                    'processed_at': '2024-01-01T00:00:00Z'
                },
                use_openai=True  # Set to False to use local model
            )
            
            # Store embeddings in vector database
            embeddings = [record["embedding"] for record in embedding_records]
            texts = [record["text"] for record in embedding_records]
            metadata_list = [record["metadata"] for record in embedding_records]
            
            point_ids = await vector_db_service.store_embeddings(
                embeddings=embeddings,
                texts=texts,
                metadata_list=metadata_list
            )
            
            print(f"✓ Processed {doc['title']} - {len(point_ids)} chunks created")
            
        except Exception as e:
            print(f"✗ Error processing {doc['title']}: {e}")
            continue
    
    print("Document processing complete!")


async def test_search():
    """Test the search functionality."""
    print("\nTesting search functionality...")
    
    test_queries = [
        "What are fundamental rights?",
        "Tell me about the Chief Justice",
        "How do I file an appeal?",
        "What are landmark cases?"
    ]
    
    for query in test_queries:
        try:
            print(f"\nQuery: {query}")
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_query_embedding(query)
            
            # Search vector database
            results = await vector_db_service.search_similar(
                query_embedding=query_embedding,
                limit=3,
                score_threshold=0.5
            )
            
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['document_type']} - Score: {result['score']:.3f}")
                print(f"     {result['text'][:100]}...")
            
        except Exception as e:
            print(f"✗ Error testing query '{query}': {e}")


async def main():
    """Main initialization function."""
    print("Initializing SCONIA Vector Database...")
    
    try:
        # Initialize vector database collections
        print("1. Initializing vector database collections...")
        await vector_db_service.initialize_collections()
        print("✓ Vector database collections initialized")
        
        # Process and embed sample documents
        print("\n2. Processing sample legal documents...")
        await process_and_embed_documents()
        
        # Test search functionality
        print("\n3. Testing search functionality...")
        await test_search()
        
        # Get collection info
        print("\n4. Vector database status:")
        info = await vector_db_service.get_collection_info()
        print(f"   Collection: {info}")
        
        print("\n✅ Vector database initialization complete!")
        print("\nYou can now:")
        print("- Start the SCONIA API server")
        print("- Test the chat endpoints")
        print("- Upload additional legal documents")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
