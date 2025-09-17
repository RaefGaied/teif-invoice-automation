"""
Script to insert test data into the database for testing the invoice API.
"""
import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from src.teif.db.session import SessionLocal, engine
from src.teif.db.models.invoice import (
    Invoice as InvoiceModel, 
    InvoiceLine, 
    InvoiceStatus,
    InvoiceDate,
    InvoiceReference,
    InvoiceType
)
from src.teif.db.models.company import Company, CompanyContact, ContactCommunication
from src.teif.db.models.tax import LineTax

def create_test_companies(db: Session):
    """Create test companies if they don't exist."""
    # Check if test companies already exist
    supplier = db.query(Company).filter(Company.name == "Test Supplier Co.").first()
    customer = db.query(Company).filter(Company.name == "Test Customer Inc.").first()
    
    if not supplier:
        supplier = Company(
            identifier="SUP-001",
            name="Test Supplier Co.",
            vat_number="12345678",
            tax_id="T12345678",
            commercial_register="A12345",
            address_street="123 Supplier St",
            address_city="Tunis",
            address_postal_code="1000",
            address_country_code="TN",
            address_language="FR",
            phone="+21612345678",
            email="supplier@example.com",
            fax="+21612345679",
            website="https://supplier.example.com",
            function_code="SUP"
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        
        # Add a contact for the supplier
        contact = CompanyContact(
            company_id=supplier.id,
            function_code="SU",
            contact_name="John Supplier",
            contact_identifier="SUP-CONTACT-001"
        )
        db.add(contact)
        db.commit()
        
        # Add communication methods for the contact
        phone = ContactCommunication(
            contact_id=contact.id,
            communication_type="TE",
            communication_value="+21612345678"
        )
        email = ContactCommunication(
            contact_id=contact.id,
            communication_type="EM",
            communication_value="john@supplier.example.com"
        )
        db.add_all([phone, email])
        db.commit()
    
    if not customer:
        customer = Company(
            identifier="CUST-001",
            name="Test Customer Inc.",
            vat_number="87654321",
            tax_id="T87654321",
            commercial_register="B67890",
            address_street="456 Customer Ave",
            address_city="Sfax",
            address_postal_code="3000",
            address_country_code="TN",
            address_language="FR",
            phone="+21687654321",
            email="info@customer.example.com",
            function_code="CUST"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        # Add a contact for the customer
        contact = CompanyContact(
            company_id=customer.id,
            function_code="BU",
            contact_name="Jane Customer",
            contact_identifier="CUST-CONTACT-001"
        )
        db.add(contact)
        db.commit()
        
        # Add communication methods for the contact
        phone = ContactCommunication(
            contact_id=contact.id,
            communication_type="TE",
            communication_value="+21687654321"
        )
        email = ContactCommunication(
            contact_id=contact.id,
            communication_type="EM",
            communication_value="jane@customer.example.com"
        )
        db.add_all([phone, email])
        db.commit()
    
    return supplier, customer

def create_test_invoice(db: Session, supplier_id: int, customer_id: int):
    """Create a test invoice with sample data."""
    # Create invoice
    invoice = InvoiceModel(
        teif_version="1.8.8",
        controlling_agency="TTN",
        sender_identifier=f"SENDER-{supplier_id}",
        receiver_identifier=f"RECEIVER-{customer_id}",
        message_identifier=f"MSG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        message_datetime=datetime.utcnow(),
        document_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-001",
        document_type=InvoiceType.INVOICE,
        document_type_label="Facture",
        document_status=InvoiceStatus.PROCESSING,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        period_start_date=date.today().replace(day=1),
        period_end_date=(date.today().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        supplier_id=supplier_id,
        customer_id=customer_id,
        currency="TND",
        total_without_tax=Decimal("1000.000"),
        tax_amount=Decimal("190.000"),
        total_with_tax=Decimal("1190.000"),
        tax_base_amount=Decimal("1000.000"),
        payment_terms="Paiement à 30 jours",
        payment_means_code="I-30",  # Bank transfer
        payment_means_text="Virement bancaire"
    )
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    # Add invoice dates
    dates = [
        {"date_text": date.today().strftime("%d%m%y"), "function_code": "I-31", "description": "Date de facture"},
        {"date_text": (date.today() + timedelta(days=30)).strftime("%d%m%y"), "function_code": "I-32", "description": "Date d'échéance"}
    ]
    
    for date_data in dates:
        inv_date = InvoiceDate(
            invoice_id=invoice.id,
            date_text=date_data["date_text"],
            function_code=date_data["function_code"],
            date_format="ddMMyy",
            description=date_data["description"]
        )
        db.add(inv_date)
    
    # Add invoice lines
    lines = [
        {
            "line_number": 1,
            "description": "Service de développement logiciel",
            "quantity": 10,
            "unit": "JOUR",
            "unit_price": Decimal("100.000"),
            "line_total_ht": Decimal("1000.000"),
            "taxes": [
                {"tax_type": "TVA", "rate": Decimal("19.000"), "amount": Decimal("190.000")}
            ]
        }
    ]
    
    for line_data in lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data["line_number"],
            description=line_data["description"],
            quantity=line_data["quantity"],
            unit=line_data["unit"],
            unit_price=line_data["unit_price"],
            line_total_ht=line_data["line_total_ht"]
        )
        db.add(line)
        db.commit()
        db.refresh(line)
        
        # Add line taxes
        for tax_data in line_data.get("taxes", []):
            tax = LineTax(
                line_id=line.id,
                tax_type=tax_data["tax_type"],
                tax_rate=tax_data["rate"],
                tax_code=tax_data.get("tax_code", "I-1602"),
                tax_category=tax_data.get("tax_category", "S"),
                taxable_amount=line.line_total_ht,
                tax_amount=line.line_total_ht * Decimal(str(tax_data["rate"])) / 100
            )
            db.add(tax)
    
    db.commit()
    return invoice

def main():
    db = SessionLocal()
    try:
        print("Creating test data...")
        
        # Create test companies
        print("Creating test companies...")
        supplier, customer = create_test_companies(db)
        
        # Create test invoice
        print(f"Creating test invoice for supplier {supplier.name} and customer {customer.name}...")
        invoice = create_test_invoice(db, supplier.id, customer.id)
        
        print(f"\nSuccessfully created test data!")
        print(f"- Supplier ID: {supplier.id}")
        print(f"- Customer ID: {customer.id}")
        print(f"- Invoice ID: {invoice.id}")
        print(f"- Invoice Number: {invoice.document_number}")
        
    except Exception as e:
        print(f"Error creating test data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
