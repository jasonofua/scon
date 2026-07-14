"""
Initialize SCONIA database with sample Nigerian legal data.
"""
import asyncio
import sys
import os
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.database import AsyncSessionLocal, init_db
from app.models.legal import Judge, ConstitutionalProvision, FeeSchedule, QuickOption, Procedure
from app.models.admin import User


async def create_sample_judges():
    """Create sample Supreme Court judges."""
    judges_data = [
        {
            "full_name": "Hon. Justice Olukayode Ariwoola",
            "title": "Chief Justice of Nigeria",
            "appointment_date": date(2022, 6, 27),
            "background_summary": "Chief Justice of Nigeria, appointed in 2022. Previously served as Justice of the Supreme Court.",
            "education": {
                "law_school": "University of Ife (now Obafemi Awolowo University)",
                "year_graduated": 1980,
                "additional_qualifications": ["Nigerian Law School", "Called to Bar 1981"]
            },
            "previous_positions": [
                "Justice of the Supreme Court (2011-2022)",
                "Justice of the Court of Appeal (2005-2011)",
                "Chief Judge of Oyo State (2010-2011)"
            ],
            "current_status": "Active",
            "is_chief_justice": True
        },
        {
            "full_name": "Hon. Justice Kudirat Motonmori Olatokunbo Kekere-Ekun",
            "title": "Justice of the Supreme Court",
            "appointment_date": date(2013, 11, 6),
            "background_summary": "Justice of the Supreme Court, known for expertise in commercial and constitutional law.",
            "education": {
                "law_school": "University of Lagos",
                "year_graduated": 1977,
                "additional_qualifications": ["Nigerian Law School", "Called to Bar 1978"]
            },
            "previous_positions": [
                "Justice of the Court of Appeal (2004-2013)",
                "Judge of the High Court of Lagos State (1989-2004)"
            ],
            "current_status": "Active",
            "is_chief_justice": False
        },
        {
            "full_name": "Hon. Justice John Inyang Okoro",
            "title": "Justice of the Supreme Court",
            "appointment_date": date(2014, 11, 6),
            "background_summary": "Justice of the Supreme Court with extensive experience in civil and criminal law.",
            "education": {
                "law_school": "University of Nigeria, Nsukka",
                "year_graduated": 1979,
                "additional_qualifications": ["Nigerian Law School", "Called to Bar 1980"]
            },
            "previous_positions": [
                "Justice of the Court of Appeal (2005-2014)",
                "Chief Judge of Akwa Ibom State (2002-2005)"
            ],
            "current_status": "Active",
            "is_chief_justice": False
        }
    ]
    
    async with AsyncSessionLocal() as session:
        for judge_data in judges_data:
            judge = Judge(**judge_data)
            session.add(judge)
        await session.commit()
        print(f"Created {len(judges_data)} sample judges")


async def create_constitutional_provisions():
    """Create sample constitutional provisions."""
    provisions_data = [
        {
            "chapter": "Chapter IV",
            "section": "33",
            "subsection": "1",
            "title": "Right to Life",
            "content": "Every person has a right to life, and no one shall be deprived intentionally of his life, save in execution of the sentence of a court in respect of a criminal offence of which he has been found guilty in Nigeria.",
            "keywords": ["right to life", "fundamental rights", "human rights", "death penalty"],
            "related_sections": ["34", "35", "36"]
        },
        {
            "chapter": "Chapter IV",
            "section": "34",
            "subsection": "1",
            "title": "Right to Dignity of Human Person",
            "content": "Every individual is entitled to respect for the dignity of his person, and accordingly - (a) no person shall be subjected to torture or to inhuman or degrading treatment; (b) no person shall be held in slavery or servitude; and (c) no person shall be required to perform forced or compulsory labour.",
            "keywords": ["human dignity", "torture", "slavery", "forced labour", "fundamental rights"],
            "related_sections": ["33", "35", "36"]
        },
        {
            "chapter": "Chapter IV",
            "section": "35",
            "subsection": "1",
            "title": "Right to Personal Liberty",
            "content": "Every person shall be entitled to his personal liberty and no person shall be deprived of such liberty save in the following cases and in accordance with a procedure permitted by law.",
            "keywords": ["personal liberty", "freedom", "detention", "arrest", "fundamental rights"],
            "related_sections": ["33", "34", "36"]
        },
        {
            "chapter": "Chapter IV",
            "section": "36",
            "subsection": "1",
            "title": "Right to Fair Hearing",
            "content": "In the determination of his civil rights and obligations, including any question or determination by or against any government or authority, a person shall be entitled to a fair hearing within a reasonable time by a court or other tribunal established by law and constituted in such manner as to secure its independence and impartiality.",
            "keywords": ["fair hearing", "due process", "court", "tribunal", "civil rights"],
            "related_sections": ["33", "34", "35"]
        },
        {
            "chapter": "Chapter VI",
            "section": "230",
            "subsection": "1",
            "title": "Supreme Court of Nigeria",
            "content": "There shall be a Supreme Court of Nigeria which shall be the highest court in Nigeria and shall have such jurisdiction and powers as are conferred on it by this Constitution and by any Act of the National Assembly.",
            "keywords": ["Supreme Court", "highest court", "jurisdiction", "National Assembly"],
            "related_sections": ["231", "232", "233"]
        }
    ]
    
    async with AsyncSessionLocal() as session:
        for provision_data in provisions_data:
            provision = ConstitutionalProvision(**provision_data)
            session.add(provision)
        await session.commit()
        print(f"Created {len(provisions_data)} constitutional provisions")


async def create_fee_schedules():
    """Create sample fee schedules."""
    fees_data = [
        {
            "service_type": "Appeal Filing",
            "case_category": "Civil Appeal",
            "fee_amount": 50000.00,
            "payment_methods": ["Bank Transfer", "Certified Bank Draft", "Online Payment"],
            "effective_date": date(2023, 1, 1),
            "description": "Filing fee for civil appeals to the Supreme Court"
        },
        {
            "service_type": "Appeal Filing",
            "case_category": "Criminal Appeal",
            "fee_amount": 25000.00,
            "payment_methods": ["Bank Transfer", "Certified Bank Draft", "Online Payment"],
            "effective_date": date(2023, 1, 1),
            "description": "Filing fee for criminal appeals to the Supreme Court"
        },
        {
            "service_type": "Motion Filing",
            "case_category": "Interlocutory Motion",
            "fee_amount": 10000.00,
            "payment_methods": ["Bank Transfer", "Certified Bank Draft", "Online Payment"],
            "effective_date": date(2023, 1, 1),
            "description": "Filing fee for interlocutory motions"
        },
        {
            "service_type": "Document Certification",
            "case_category": "General",
            "fee_amount": 5000.00,
            "payment_methods": ["Cash", "Bank Transfer", "Online Payment"],
            "effective_date": date(2023, 1, 1),
            "description": "Fee for certifying court documents"
        }
    ]
    
    async with AsyncSessionLocal() as session:
        for fee_data in fees_data:
            fee = FeeSchedule(**fee_data)
            session.add(fee)
        await session.commit()
        print(f"Created {len(fees_data)} fee schedules")


async def create_quick_options():
    """Create quick options for kiosk interface."""
    options_data = [
        {
            "option_text": "File a case or appeal",
            "category": "Filing",
            "target_procedure": "case_filing",
            "display_order": 1,
            "icon_name": "file-text"
        },
        {
            "option_text": "Understand court procedures",
            "category": "Information",
            "target_procedure": "court_procedures",
            "display_order": 2,
            "icon_name": "info"
        },
        {
            "option_text": "Access legal documents",
            "category": "Documents",
            "target_procedure": "document_access",
            "display_order": 3,
            "icon_name": "folder"
        },
        {
            "option_text": "Find court information",
            "category": "Information",
            "target_procedure": "court_info",
            "display_order": 4,
            "icon_name": "map-pin"
        },
        {
            "option_text": "Calculate fees",
            "category": "Fees",
            "target_procedure": "fee_calculation",
            "display_order": 5,
            "icon_name": "calculator"
        },
        {
            "option_text": "Ask a legal question",
            "category": "Chat",
            "target_procedure": "legal_chat",
            "display_order": 6,
            "icon_name": "message-circle"
        }
    ]
    
    async with AsyncSessionLocal() as session:
        for option_data in options_data:
            option = QuickOption(**option_data)
            session.add(option)
        await session.commit()
        print(f"Created {len(options_data)} quick options")


async def create_admin_user():
    """Create default admin user."""
    async with AsyncSessionLocal() as session:
        admin_user = User(
            username="admin",
            email="admin@sconia.gov.ng",
            full_name="SCONIA Administrator",
            is_superuser=True,
            is_staff=True,
            permissions={"all": True}
        )
        admin_user.set_password("admin123")  # Change this in production!
        
        session.add(admin_user)
        await session.commit()
        print("Created admin user (username: admin, password: admin123)")


async def main():
    """Initialize database with sample data."""
    print("Initializing SCONIA database...")
    
    # Initialize database tables
    await init_db()
    print("Database tables created")
    
    # Create sample data
    await create_sample_judges()
    await create_constitutional_provisions()
    await create_fee_schedules()
    await create_quick_options()
    await create_admin_user()
    
    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
