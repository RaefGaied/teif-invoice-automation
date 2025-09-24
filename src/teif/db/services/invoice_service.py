from datetime import date, datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.invoice import Invoice, InvoiceLine, InvoiceStatus
from ..repositories.invoice_repository import InvoiceRepository
from ..repositories.company_repository import CompanyRepository
from ..schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceLineCreate
from .base import BaseService


class InvoiceService(BaseService[Invoice, InvoiceCreate, InvoiceUpdate]):
    """Service for handling invoice business logic."""
    
    def __init__(self, db: Session):
        """Initialize the invoice service with database session."""
        self.invoice_repo = InvoiceRepository(db)
        self.company_repo = CompanyRepository(db)
        super().__init__(self.invoice_repo)
    
    def get_invoice_with_details(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get an invoice with all related data."""
        invoice = self.invoice_repo.get_with_details(invoice_id)
        if not invoice:
            return None
            
        # Convert SQLAlchemy model to dict
        invoice_dict = {}
        for column in invoice.__table__.columns:
            value = getattr(invoice, column.name)
            # Handle datetime serialization
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            invoice_dict[column.name] = value
        
        # Handle payment_terms as a list of strings
        payment_terms = []
        if hasattr(invoice, 'payment_terms_list') and invoice.payment_terms_list:
            # If we have payment terms objects, extract their descriptions
            payment_terms = [
                term.description for term in invoice.payment_terms_list 
                if term and term.description
            ]
        elif 'payment_terms' in invoice_dict and invoice_dict['payment_terms']:
            # If payment_terms is a string, split it by comma
            payment_terms = [term.strip() for term in invoice_dict['payment_terms'].split(',') if term.strip()]
        
        invoice_dict['payment_terms'] = payment_terms
        
        # Handle relationships
        if hasattr(invoice, 'lines'):
            invoice_dict['lines'] = [
                {
                    'id': line.id,
                    'line_number': line.line_number,
                    'description': line.description,
                    'quantity': float(line.quantity) if line.quantity is not None else 0,
                    'unit': line.unit,
                    'unit_price': float(line.unit_price) if line.unit_price is not None else 0,
                    'line_total_ht': float(line.line_total_ht) if line.line_total_ht is not None else 0,
                    'discount_amount': float(line.discount_amount) if line.discount_amount is not None else 0,
                    'discount_percent': float(line.discount_percent) if line.discount_percent is not None else 0,
                    'discount_reason': line.discount_reason,
                    'currency': line.currency,
                    'additional_info': line.additional_info
                }
                for line in invoice.lines
            ]
        
        return invoice_dict
    
    def get_invoice_by_document_number(self, document_number: str) -> Optional[Invoice]:
        """Get an invoice by its document number."""
        return self.invoice_repo.get_by_document_number(document_number)
    
    def create_invoice(
        self, 
        invoice_data: InvoiceCreate,
        lines_data: List[InvoiceLineCreate],
        created_by: str = "system"
    ) -> Invoice:
        """
        Create a new invoice with line items.
        
        Args:
            invoice_data: The invoice data
            lines_data: List of invoice line items
            created_by: Username or identifier of the creator
            
        Returns:
            The created invoice
        """
        # Set created_by and updated_by if not provided
        if not hasattr(invoice_data, 'created_by'):
            invoice_data.created_by = created_by
        if not hasattr(invoice_data, 'updated_by'):
            invoice_data.updated_by = created_by
        
        # Calculate totals if not provided
        if not invoice_data.total_amount_ht:
            invoice_data.total_amount_ht = sum(
                line.unit_price * line.quantity * (1 - (line.discount or 0) / 100)
                for line in lines_data
            )
        
        # Create the invoice with lines
        return self.invoice_repo.create_with_lines(invoice_data, lines_data)
    
    def update_invoice_status(
        self, 
        invoice_id: int, 
        new_status: InvoiceStatus,
        updated_by: str = "system"
    ) -> Invoice:
        """
        Update the status of an invoice.
        
        Args:
            invoice_id: The ID of the invoice to update
            new_status: The new status
            updated_by: Username or identifier of who is making the update
            
        Returns:
            The updated invoice
        """
        invoice = self.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with ID {invoice_id} not found")
            
        # Add any business rules for status transitions here
        if invoice.status == InvoiceStatus.PAID and new_status != InvoiceStatus.PAID:
            raise ValueError("Cannot change status from PAID to another status")
            
        # Update the status
        invoice.status = new_status
        invoice.updated_by = updated_by
        invoice.updated_at = datetime.utcnow()
        
        self.invoice_repo.db.commit()
        self.invoice_repo.db.refresh(invoice)
        return invoice
    
    def get_invoices_by_date_range(
        self,
        start_date: date,
        end_date: date,
        company_id: Optional[int] = None,
        status: Optional[InvoiceStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get invoices within a date range, optionally filtered by company and status.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            company_id: Optional company ID to filter by (supplier or customer)
            status: Optional status to filter by
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries containing invoice data
        """
        # Start with a base query
        query = self.invoice_repo.db.query(Invoice).filter(
            Invoice.invoice_date.between(start_date, end_date)
        )
        
        # Apply filters
        if company_id:
            query = query.filter(
                (Invoice.supplier_id == company_id) | 
                (Invoice.customer_id == company_id)
            )
            
        if status:
            query = query.filter(Invoice.status == status)
        
        # Execute the query
        invoices = query.order_by(Invoice.invoice_date.desc())\
                      .offset(skip).limit(limit).all()
        
        # Convert SQLAlchemy models to dictionaries and handle payment_terms
        result = []
        for invoice in invoices:
            invoice_dict = {}
            for column in invoice.__table__.columns:
                value = getattr(invoice, column.name)
                # Handle datetime serialization
                if isinstance(value, (datetime, date)):
                    value = value.isoformat()
                invoice_dict[column.name] = value
            
            # Handle payment_terms as a list of strings
            payment_terms = []
            if hasattr(invoice, 'payment_terms_list') and invoice.payment_terms_list:
                payment_terms = [
                    term.description for term in invoice.payment_terms_list 
                    if term and term.description
                ]
            elif 'payment_terms' in invoice_dict and invoice_dict['payment_terms']:
                payment_terms = [term.strip() for term in invoice_dict['payment_terms'].split(',') if term.strip()]
            
            invoice_dict['payment_terms'] = payment_terms
            result.append(invoice_dict)
        
        return result
    
    def get_invoice_statistics(
        self,
        start_date: date,
        end_date: date,
        company_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get invoice statistics for a given period.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            company_id: Optional company ID to filter by
            
        Returns:
            Dictionary containing various statistics
        """
        stats = {
            'total_invoices': 0,
            'total_amount_ht': 0,
            'total_amount_tva': 0,
            'total_amount_ttc': 0,
            'by_status': {},
            'by_company': {},
            'by_month': {}
        }
        
        # Base query
        query = self.invoice_repo.db.query(Invoice).filter(
            Invoice.invoice_date.between(start_date, end_date)
        )
        
        if company_id:
            query = query.filter(
                (Invoice.supplier_id == company_id) | 
                (Invoice.customer_id == company_id)
            )
        
        # Execute query
        invoices = query.all()
        
        # Calculate statistics
        for invoice in invoices:
            stats['total_invoices'] += 1
            stats['total_amount_ht'] += invoice.total_without_tax or 0
            stats['total_amount_tva'] += invoice.tax_amount or 0
            stats['total_amount_ttc'] += invoice.total_with_tax or 0
            
            # Group by status
            status = invoice.status.value if hasattr(invoice.status, 'value') else str(invoice.status)
            if status not in stats['by_status']:
                stats['by_status'][status] = 0
            stats['by_status'][status] += 1
            
            # Group by company
            company_id = invoice.supplier_id
            if company_id not in stats['by_company']:
                company = self.company_repo.get(company_id)
                company_name = company.name if company else f"Company {company_id}"
                stats['by_company'][company_id] = {
                    'name': company_name,
                    'count': 0,
                    'amount': 0
                }
            stats['by_company'][company_id]['count'] += 1
            stats['by_company'][company_id]['amount'] += invoice.total_with_tax or 0
            
            # Group by month
            month_key = invoice.invoice_date.strftime('%Y-%m')
            if month_key not in stats['by_month']:
                stats['by_month'][month_key] = 0
            stats['by_month'][month_key] += 1
        
        return stats
