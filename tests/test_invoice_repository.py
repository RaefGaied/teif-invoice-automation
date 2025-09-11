import pytest
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

# Import your models and repository
from teif.db.base import Base
from teif.db.repositories.invoice_repository import InvoiceRepository
from teif.db.models.invoice import Invoice, InvoiceStatus
from teif.db.models.company import Company

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Fixtures
@pytest.fixture(scope="module")
def db():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_company_supplier(db: Session):
    company = Company(
        name_ar="شركة المورد التجارية",
        name_fr="Société Fournisseur",
        tax_identification_number="12345678",
        commercial_register_number="CR123456",
        address="123 Supplier St"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@pytest.fixture
def test_company_customer(db: Session):
    company = Company(
        name_ar="شركة الزبون",
        name_fr="Société Client",
        tax_identification_number="87654321",
        commercial_register_number="CR654321",
        address="456 Customer Ave"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@pytest.fixture
def test_invoices(db: Session, test_company_supplier, test_company_customer):
    # Create test data
    invoices = [
        Invoice(
            document_number="INV-2023-001",
            invoice_date=date(2023, 1, 15),
            due_date=date(2023, 2, 15),
            status=InvoiceStatus.PAID,
            total_amount=1000.0,
            total_tax_amount=180.0,
            supplier_id=test_company_supplier.id,
            customer_id=test_company_customer.id,
        ),
        Invoice(
            document_number="INV-2023-002",
            invoice_date=date(2023, 2, 1),
            due_date=date(2023, 3, 1),
            status=InvoiceStatus.UNPAID,
            total_amount=2000.0,
            total_tax_amount=360.0,
            supplier_id=test_company_supplier.id,
            customer_id=test_company_customer.id,
        ),
    ]
    
    db.add_all(invoices)
    db.commit()
    
    for inv in invoices:
        db.refresh(inv)
    
    return invoices

def test_search_invoices_by_document_number(db: Session, test_invoices):
    repo = InvoiceRepository(db)
    
    # Search by exact document number
    results = repo.search_invoices("INV-2023-001")
    assert len(results) == 1
    assert results[0].document_number == "INV-2023-001"
    
    # Search by partial document number
    results = repo.search_invoices("INV-2023")
    assert len(results) == 2  # Should find both test invoices
    
    # Search with no results
    results = repo.search_invoices("NON-EXISTENT")
    assert len(results) == 0

def test_search_invoices_by_company_name_ar(db: Session, test_invoices, test_company_supplier, test_company_customer):
    repo = InvoiceRepository(db)
    
    # Search by Arabic supplier name
    results = repo.search_invoices("المورد")
    assert len(results) > 0
    assert all(inv.supplier_id == test_company_supplier.id for inv in results)
    
    # Search by Arabic customer name
    results = repo.search_invoices("الزبون")
    assert len(results) > 0
    assert all(inv.customer_id == test_company_customer.id for inv in results)

def test_search_invoices_by_company_name_fr(db: Session, test_invoices, test_company_supplier, test_company_customer):
    repo = InvoiceRepository(db)
    
    # Search by French supplier name
    results = repo.search_invoices("Fournisseur")
    assert len(results) > 0
    assert all(inv.supplier_id == test_company_supplier.id for inv in results)
    
    # Search by French customer name
    results = repo.search_invoices("Client")
    assert len(results) > 0
    assert all(inv.customer_id == test_company_customer.id for inv in results)

def test_search_invoices_case_insensitive(db: Session, test_invoices):
    repo = InvoiceRepository(db)
    
    # Case insensitive search for document number
    results_upper = repo.search_invoices("INV-2023-001")
    results_lower = repo.search_invoices("inv-2023-001")
    assert len(results_upper) == 1
    assert len(results_lower) == 1
    assert results_upper[0].id == results_lower[0].id
    
    # Case insensitive search for company name (French)
    results_upper = repo.search_invoices("FOURNISSEUR")
    results_lower = repo.search_invoices("fournisseur")
    assert len(results_upper) > 0
    assert len(results_upper) == len(results_lower)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
