#!/usr/bin/env python3
"""
Add comprehensive legal content to SCONIA database.
Includes Supreme Court cases, procedures, and forms.
"""
import asyncio
import sys
import os
from datetime import date, datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.database import AsyncSessionLocal
from app.models.legal import SupremeCourtCase, Procedure, RequiredForm, FeeSchedule
from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service


async def add_supreme_court_cases():
    """Add landmark Supreme Court cases."""
    
    cases = [
        {
            "case_number": "SC.213/2007",
            "case_title": "Marwa v. Nyako & Ors",
            "judgment_date": date(2012, 12, 14),
            "case_summary": """
            This landmark case established important principles regarding the conduct of elections and the 
            jurisdiction of election petition tribunals. The Supreme Court held that substantial compliance 
            with electoral laws is sufficient where there is no evidence of non-compliance affecting the 
            outcome of elections.
            """,
            "legal_principles": [
                "Substantial compliance with electoral laws",
                "Burden of proof in election petitions",
                "Jurisdiction of election tribunals"
            ],
            "case_status": "decided"
        },
        {
            "case_number": "SC.109/2003",
            "case_title": "Buhari v. Obasanjo & Ors",
            "judgment_date": date(2005, 7, 1),
            "case_summary": """
            A significant constitutional case that clarified the requirements for challenging presidential 
            elections. The Supreme Court emphasized the need for petitioners to prove allegations of 
            non-compliance with electoral laws with credible evidence.
            """,
            "legal_principles": [
                "Presidential election challenges",
                "Standard of proof in election petitions",
                "Constitutional requirements for elections"
            ],
            "case_status": "decided"
        },
        {
            "case_number": "SC.596/2007",
            "case_title": "Atiku v. Yar'Adua & Ors",
            "judgment_date": date(2008, 12, 12),
            "case_summary": """
            This case dealt with the qualification requirements for presidential candidates and the 
            interpretation of constitutional provisions regarding educational qualifications for public office.
            """,
            "legal_principles": [
                "Presidential qualification requirements",
                "Constitutional interpretation",
                "Educational requirements for public office"
            ],
            "case_status": "decided"
        },
        {
            "case_number": "SC.1002/2019",
            "case_title": "Atiku v. Buhari & Ors",
            "judgment_date": date(2019, 10, 30),
            "case_summary": """
            Recent landmark case on the 2019 presidential election petition. The Supreme Court reaffirmed 
            principles of election petition law and the burden of proof required to overturn election results.
            """,
            "legal_principles": [
                "Modern election petition principles",
                "Electronic voting and transmission",
                "Burden of proof in contemporary elections"
            ],
            "case_status": "decided"
        },
        {
            "case_number": "SC.876/2011",
            "case_title": "A.G. Federation v. A.G. Abia State & Ors",
            "judgment_date": date(2012, 4, 20),
            "case_summary": """
            Constitutional case on federal-state relations and the distribution of powers between federal 
            and state governments under the Nigerian Constitution.
            """,
            "legal_principles": [
                "Federal-state relations",
                "Distribution of constitutional powers",
                "Supremacy of federal law"
            ],
            "case_status": "decided"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        print("📚 Adding Supreme Court cases...")
        
        for case_data in cases:
            case = SupremeCourtCase(**case_data)
            db.add(case)
        
        await db.commit()
        print(f"✅ Added {len(cases)} Supreme Court cases")


async def add_court_procedures():
    """Add court procedures and processes."""
    
    procedures = [
        {
            "procedure_name": "Filing an Appeal to the Supreme Court",
            "category": "appeals",
            "step_by_step_guide": {
                "steps": [
                    {
                        "step": 1,
                        "title": "Obtain Certified True Copy",
                        "description": "Obtain certified true copy of the judgment from the Court of Appeal",
                        "timeframe": "Within 3 months of judgment"
                    },
                    {
                        "step": 2,
                        "title": "Prepare Notice of Appeal",
                        "description": "Prepare and file Notice of Appeal within statutory time limit",
                        "timeframe": "Within 3 months of judgment"
                    },
                    {
                        "step": 3,
                        "title": "File Appeal Record",
                        "description": "Compile and file the appeal record with all necessary documents",
                        "timeframe": "Within 3 months of filing notice"
                    },
                    {
                        "step": 4,
                        "title": "Serve Other Parties",
                        "description": "Serve copies of appeal documents on all other parties",
                        "timeframe": "Within 7 days of filing"
                    },
                    {
                        "step": 5,
                        "title": "File Appellant's Brief",
                        "description": "File detailed brief of argument with legal authorities",
                        "timeframe": "Within 3 months of filing record"
                    }
                ]
            },
            "required_documents": [
                "Notice of Appeal",
                "Certified True Copy of Judgment",
                "Appeal Record",
                "Appellant's Brief of Argument",
                "Power of Attorney (if represented)"
            ],
            "estimated_timeline": "6-12 months",
            "contact_departments": ["Registry", "Legal Department"]
        },
        {
            "procedure_name": "Application for Stay of Execution",
            "category": "applications",
            "step_by_step_guide": {
                "steps": [
                    {
                        "step": 1,
                        "title": "File Motion on Notice",
                        "description": "File motion on notice with supporting affidavit",
                        "timeframe": "Immediately after judgment"
                    },
                    {
                        "step": 2,
                        "title": "Show Special Circumstances",
                        "description": "Demonstrate special circumstances warranting stay",
                        "timeframe": "In supporting affidavit"
                    },
                    {
                        "step": 3,
                        "title": "Provide Security",
                        "description": "Provide adequate security for the judgment debt",
                        "timeframe": "As ordered by court"
                    }
                ]
            },
            "required_documents": [
                "Motion on Notice",
                "Supporting Affidavit",
                "Written Address",
                "Security/Undertaking"
            ],
            "estimated_timeline": "2-4 weeks",
            "contact_departments": ["Registry", "Accounts Department"]
        },
        {
            "procedure_name": "Constitutional Interpretation Application",
            "category": "constitutional",
            "step_by_step_guide": {
                "steps": [
                    {
                        "step": 1,
                        "title": "Establish Locus Standi",
                        "description": "Demonstrate sufficient interest in the constitutional question",
                        "timeframe": "In originating process"
                    },
                    {
                        "step": 2,
                        "title": "Identify Constitutional Provision",
                        "description": "Clearly identify the constitutional provision requiring interpretation",
                        "timeframe": "In statement of case"
                    },
                    {
                        "step": 3,
                        "title": "File Originating Summons",
                        "description": "File originating summons with supporting affidavit",
                        "timeframe": "Within limitation period"
                    }
                ]
            },
            "required_documents": [
                "Originating Summons",
                "Statement of Case",
                "Supporting Affidavit",
                "Written Address"
            ],
            "estimated_timeline": "12-18 months",
            "contact_departments": ["Constitutional Division", "Registry"]
        }
    ]
    
    async with AsyncSessionLocal() as db:
        print("⚖️ Adding court procedures...")
        
        for proc_data in procedures:
            procedure = Procedure(**proc_data)
            db.add(procedure)
        
        await db.commit()
        print(f"✅ Added {len(procedures)} court procedures")


async def add_required_forms():
    """Add legal forms and templates."""
    
    forms = [
        {
            "form_name": "Notice of Appeal Form",
            "form_type": "appeal",
            "description": "Standard form for filing notice of appeal to the Supreme Court",
            "requirements": [
                "Case number of lower court",
                "Names of all parties",
                "Date of judgment being appealed",
                "Grounds of appeal",
                "Relief sought"
            ],
            "completion_guide": """
            1. Fill in all party names exactly as they appear in the lower court judgment
            2. State the specific date of the judgment you are appealing
            3. Clearly state your grounds of appeal
            4. Specify the relief you are seeking from the Supreme Court
            5. Sign and date the form
            6. Attach certified true copy of the judgment
            """,
            "related_procedures": ["Filing an Appeal to the Supreme Court"]
        },
        {
            "form_name": "Motion on Notice",
            "form_type": "application",
            "description": "General form for making applications to the Supreme Court",
            "requirements": [
                "Title of case",
                "Nature of application",
                "Grounds for application",
                "Supporting affidavit",
                "Legal authorities"
            ],
            "completion_guide": """
            1. Use the exact case title from the main proceedings
            2. Clearly state what you are asking the court to do
            3. Provide legal and factual grounds for your application
            4. Attach a supporting affidavit with relevant facts
            5. Cite relevant legal authorities
            6. Serve on all other parties
            """,
            "related_procedures": ["Application for Stay of Execution", "Constitutional Interpretation Application"]
        },
        {
            "form_name": "Affidavit Form",
            "form_type": "evidence",
            "description": "Standard affidavit form for sworn statements",
            "requirements": [
                "Full name and address of deponent",
                "Statement of facts",
                "Oath or affirmation",
                "Commissioner for oaths signature"
            ],
            "completion_guide": """
            1. State your full name and address at the beginning
            2. Number each paragraph of your statement
            3. State only facts within your personal knowledge
            4. Use clear and simple language
            5. Swear or affirm before a commissioner for oaths
            6. Sign in the presence of the commissioner
            """,
            "related_procedures": ["Filing an Appeal to the Supreme Court", "Application for Stay of Execution"]
        }
    ]
    
    async with AsyncSessionLocal() as db:
        print("📋 Adding required forms...")
        
        for form_data in forms:
            form = RequiredForm(**form_data)
            db.add(form)
        
        await db.commit()
        print(f"✅ Added {len(forms)} legal forms")


async def add_fee_schedules():
    """Add court fee schedules."""
    
    fees = [
        {
            "service_type": "Notice of Appeal Filing",
            "case_category": "civil",
            "fee_amount": 50000.00,
            "payment_methods": ["Bank Draft", "Certified Cheque", "Online Payment"],
            "effective_date": date(2024, 1, 1),
            "description": "Fee for filing notice of appeal in civil matters"
        },
        {
            "service_type": "Notice of Appeal Filing",
            "case_category": "criminal",
            "fee_amount": 25000.00,
            "payment_methods": ["Bank Draft", "Certified Cheque", "Online Payment"],
            "effective_date": date(2024, 1, 1),
            "description": "Fee for filing notice of appeal in criminal matters"
        },
        {
            "service_type": "Motion on Notice",
            "case_category": "general",
            "fee_amount": 15000.00,
            "payment_methods": ["Bank Draft", "Certified Cheque", "Online Payment"],
            "effective_date": date(2024, 1, 1),
            "description": "Fee for filing motion on notice"
        },
        {
            "service_type": "Certified True Copy",
            "case_category": "general",
            "fee_amount": 5000.00,
            "payment_methods": ["Cash", "Bank Draft", "Online Payment"],
            "effective_date": date(2024, 1, 1),
            "description": "Fee for obtaining certified true copy of judgment"
        },
        {
            "service_type": "Constitutional Application",
            "case_category": "constitutional",
            "fee_amount": 100000.00,
            "payment_methods": ["Bank Draft", "Certified Cheque"],
            "effective_date": date(2024, 1, 1),
            "description": "Fee for constitutional interpretation applications"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        print("💰 Adding fee schedules...")
        
        for fee_data in fees:
            fee = FeeSchedule(**fee_data)
            db.add(fee)
        
        await db.commit()
        print(f"✅ Added {len(fees)} fee schedules")


async def create_embeddings_for_content():
    """Create embeddings for the legal content."""
    
    print("🔄 Creating embeddings for legal content...")
    
    async with AsyncSessionLocal() as db:
        # Get all cases
        from sqlalchemy import select
        
        # Process cases
        result = await db.execute(select(SupremeCourtCase))
        cases = result.scalars().all()
        
        for case in cases:
            case_text = f"""
            Case: {case.case_title}
            Case Number: {case.case_number}
            Judgment Date: {case.judgment_date}
            
            Summary: {case.case_summary}
            
            Legal Principles:
            {chr(10).join(f"- {principle}" for principle in (case.legal_principles or []))}
            """
            
            # Generate embeddings
            embedding_records = await embedding_service.embed_document(
                text=case_text,
                document_id=f"case_{case.id}",
                document_type="case",
                metadata={
                    "case_number": case.case_number,
                    "case_title": case.case_title,
                    "judgment_date": case.judgment_date.isoformat() if case.judgment_date else None,
                    "title": case.case_title
                },
                use_openai=True
            )
            
            # Store embeddings
            vectors = [record["embedding"] for record in embedding_records]
            texts = [record["text"] for record in embedding_records]
            metadata_list = [record["metadata"] for record in embedding_records]
            
            await vector_db_service.store_embeddings(
                embeddings=vectors,
                texts=texts,
                metadata_list=metadata_list
            )
        
        print(f"✅ Created embeddings for {len(cases)} cases")
        
        # Process procedures
        result = await db.execute(select(Procedure))
        procedures = result.scalars().all()
        
        for procedure in procedures:
            steps_text = ""
            if procedure.step_by_step_guide and "steps" in procedure.step_by_step_guide:
                steps_text = "\n".join([
                    f"Step {step['step']}: {step['title']} - {step['description']}"
                    for step in procedure.step_by_step_guide["steps"]
                ])
            
            procedure_text = f"""
            Procedure: {procedure.procedure_name}
            Category: {procedure.category}
            Timeline: {procedure.estimated_timeline}
            
            Steps:
            {steps_text}
            
            Required Documents:
            {chr(10).join(f"- {doc}" for doc in (procedure.required_documents or []))}
            
            Contact Departments:
            {chr(10).join(f"- {dept}" for dept in (procedure.contact_departments or []))}
            """
            
            # Generate embeddings
            embedding_records = await embedding_service.embed_document(
                text=procedure_text,
                document_id=f"procedure_{procedure.id}",
                document_type="procedure",
                metadata={
                    "procedure_name": procedure.procedure_name,
                    "category": procedure.category,
                    "timeline": procedure.estimated_timeline,
                    "title": procedure.procedure_name
                },
                use_openai=True
            )
            
            # Store embeddings
            vectors = [record["embedding"] for record in embedding_records]
            texts = [record["text"] for record in embedding_records]
            metadata_list = [record["metadata"] for record in embedding_records]
            
            await vector_db_service.store_embeddings(
                embeddings=vectors,
                texts=texts,
                metadata_list=metadata_list
            )
        
        print(f"✅ Created embeddings for {len(procedures)} procedures")


async def main():
    """Main function to add all legal content."""
    
    print("🏛️  SCONIA Legal Content Import")
    print("=" * 50)
    
    try:
        await add_supreme_court_cases()
        await add_court_procedures()
        await add_required_forms()
        await add_fee_schedules()
        await create_embeddings_for_content()
        
        print("\n🎉 Legal content import completed successfully!")
        print("\nSummary:")
        print("- ✅ Supreme Court cases added")
        print("- ✅ Court procedures added")
        print("- ✅ Legal forms added")
        print("- ✅ Fee schedules added")
        print("- ✅ Embeddings created for vector search")
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
