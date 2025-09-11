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
    
    def get_invoice_with_details(self, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice with all related data."""
        return self.invoice_repo.get_with_details(invoice_id)
    
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
    ) -> List[Invoice]:
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
            List of matching invoices
        """
        query = self.invoice_repo.db.query(Invoice).filter(
            Invoice.invoice_date.between(start_date, end_date)
        )
        
        if company_id:
            query = query.filter(
                (Invoice.supplier_id == company_id) | 
                (Invoice.customer_id == company_id)
            )
            
        if status:
            query = query.filter(Invoice.status == status)
            
        return query.order_by(Invoice.invoice_date.desc())\
                   .offset(skip).limit(limit).all()
    
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
            stats['total_amount_ht'] += invoice.total_amount_ht or 0
            stats['total_amount_tva'] += invoice.total_amount_tva or 0
            stats['total_amount_ttc'] += invoice.total_amount_ttc or 0
            
            # Group by status
            status = invoice.status.value if invoice.status else 'UNKNOWN'
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
            stats['by_company'][company_id]['amount'] += invoice.total_amount_ttc or 0
            
            # Group by month
            month_key = invoice.invoice_date.strftime('%Y-%m')
            if month_key not in stats['by_month']:
                stats['by_month'][month_key] = 0
            stats['by_month'][month_key] += 1
        
        return stats
