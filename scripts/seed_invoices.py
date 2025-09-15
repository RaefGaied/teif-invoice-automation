#!/usr/bin/env python3
"""
Script to seed the database with test invoice data.
"""
import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from teif.db.session import SQLALCHEMY_DATABASE_URL
from teif.db.models.invoice import Invoice, InvoiceLine, InvoiceTax, InvoiceStatus
from teif.db.models.company import Company

def create_test_companies(db: Session):
    """Create test companies if they don't exist."""
    # Check if companies already exist
    supplier = db.query(Company).filter_by(name="Test Supplier").first()
    customer = db.query(Company).filter_by(name="Test Customer").first()
    
    if not supplier:
        supplier = Company(
            identifier="SUPPLIER001",
            name="Test Supplier",
            vat_number="12345678",
            tax_id="12345678",
            commercial_register="RC123456",
            address_street="123 Supplier St",
            address_city="Tunis",
            address_postal_code="1000",
            address_country_code="TN",
            address_language="FR",
            phone="+216 12 345 678",
            email="supplier@example.com",
            fax="+216 70 123 456",
            website="www.testsupplier.tn"
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        print(f"Created supplier: {supplier.name} (ID: {supplier.id})")
    
    if not customer:
        customer = Company(
            identifier="CUSTOMER001",
            name="Test Customer",
            vat_number="87654321",
            tax_id="87654321",
            commercial_register="RC876543",
            address_street="456 Customer Ave",
            address_city="Sousse",
            address_postal_code="4000",
            address_country_code="TN",
            address_language="FR",
            phone="+216 98 765 432",
            email="customer@example.com",
            fax="+216 70 654 321",
            website="www.testcustomer.tn"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"Created customer: {customer.name} (ID: {customer.id})")
    
    return supplier, customer

def create_test_invoice(db: Session, supplier_id: int, customer_id: int):
    """Create a test invoice with line items."""
    from datetime import datetime, timedelta
    from decimal import Decimal
    
    # Create invoice
    invoice = Invoice(
        teif_version="1.8.8",
        controlling_agency="TTN",
        sender_identifier="SUPPLIER001",
        receiver_identifier="CUSTOMER001",
        message_identifier=f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        message_datetime=datetime.utcnow(),
        document_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-001",
        document_type="INVOICE",
        document_type_label="Facture",
        invoice_date=datetime.utcnow().date(),
        due_date=(datetime.utcnow() + timedelta(days=30)).date(),
        period_start_date=datetime.utcnow().date(),
        period_end_date=(datetime.utcnow() + timedelta(days=30)).date(),
        supplier_id=supplier_id,
        customer_id=customer_id,
        currency="TND",
        currency_code_list="ISO_4217",
        capital_amount=Decimal("0.00"),
        total_with_tax=Decimal("0.00"),
        total_without_tax=Decimal("0.00"),
        tax_base_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        status="processing",  # Changed from 'DRAFT' to 'processing' to match database constraint
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(invoice)
    db.flush()  # Get the invoice ID
    
    # Create line items
    line_items = [
        {
            "item_identifier": "ITEM001",
            "item_code": "LAPTOP-X1",
            "description": "Laptop X1",
            "quantity": Decimal("2"),
            "unit": "PCE",
            "unit_price": Decimal("2500.00"),
            "currency": "TND",
            "currency_code_list": "ISO_4217"
        },
        {
            "item_identifier": "ITEM002",
            "item_code": "MOUSE-M1",
            "description": "Wireless Mouse",
            "quantity": Decimal("5"),
            "unit": "PCE",
            "unit_price": Decimal("150.00"),
            "currency": "TND",
            "currency_code_list": "ISO_4217"
        }
    ]
    
    total_without_tax = Decimal("0.00")
    tax_amount = Decimal("0.00")
    
    for idx, item in enumerate(line_items, 1):
        line_total = item["quantity"] * item["unit_price"]
        line_tax = line_total * Decimal("0.19")  # 19% TVA
        
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=idx,
            item_identifier=item["item_identifier"],
            item_code=item["item_code"],
            description=item["description"],
            quantity=item["quantity"],
            unit=item["unit"],
            unit_price=item["unit_price"],
            line_total_ht=line_total,
            currency=item["currency"],
            currency_code_list=item["currency_code_list"],
            line_date=datetime.utcnow().date(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(line)
        db.flush()
        
        total_without_tax += line_total
        tax_amount += line_tax
    
    # Update invoice totals
    invoice.total_without_tax = total_without_tax
    invoice.tax_amount = tax_amount
    invoice.total_with_tax = total_without_tax + tax_amount
    invoice.tax_base_amount = total_without_tax
    invoice.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(invoice)
    
    print(f"\n✅ Created invoice:")
    print(f"- Document Number: {invoice.document_number}")
    print(f"- Invoice Date: {invoice.invoice_date}")
    print(f"- Due Date: {invoice.due_date}")
    print(f"- Status: {invoice.status}")
    print(f"- Total HT: {invoice.total_without_tax} {invoice.currency}")
    print(f"- TVA: {invoice.tax_amount} {invoice.currency}")
    print(f"- Total TTC: {invoice.total_with_tax} {invoice.currency}")
    
    return invoice

def main():
    """Main function to run the seeding script."""
    print("Starting database seeding...")
    
    # Create database engine and session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    db = Session(engine)
    
    try:
        # Create test companies
        print("\nCreating test companies...")
        supplier, customer = create_test_companies(db)
        
        # Create test invoice
        print("\nCreating test invoice...")
        invoice = create_test_invoice(db, supplier.id, customer.id)
        
        print("\nDatabase seeding completed successfully!")
        
    except Exception as e:
        print(f"\nError during database seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
