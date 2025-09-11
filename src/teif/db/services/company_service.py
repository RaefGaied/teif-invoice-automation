from datetime import date, datetime
from typing import Dict, List, Optional, Any, Union

from sqlalchemy.orm import Session

from ..models.company import Company, CompanyContact, ContactCommunication
from ..models.invoice import InvoiceStatus
from ..repositories.company_repository import CompanyRepository
from ..repositories.invoice_repository import InvoiceRepository
from ..schemas.company import CompanyCreate, CompanyUpdate, CompanyContactCreate
from .base import BaseService

class CompanyService(BaseService[Company, CompanyCreate, CompanyUpdate]):
    """Service for handling company business logic."""
    
    def __init__(self, db: Session):
        """Initialize the company service with database session."""
        self.company_repo = CompanyRepository(db)
        self.invoice_repo = InvoiceRepository(db)
        super().__init__(self.company_repo)
    
    def get_company_with_details(self, company_id: int) -> Optional[Company]:
        """Get a company with all related data."""
        return self.company_repo.get_with_details(company_id)
    
    def get_company_by_identifier(self, identifier: str) -> Optional[Company]:
        """Get a company by its unique identifier."""
        return self.company_repo.get_by_identifier(identifier)
    
    def get_company_by_vat_number(self, vat_number: str) -> Optional[Company]:
        """Get a company by VAT number."""
        return self.company_repo.get_by_vat_number(vat_number)
    
    def search_companies(
        self, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Company]:
        """
        Search for companies by name, identifier, VAT number, or tax ID.
        
        Args:
            query: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching companies
        """
        return self.company_repo.search_companies(query, skip=skip, limit=limit)
    
    def create_company(
        self, 
        company_data: CompanyCreate,
        created_by: str = "system"
    ) -> Company:
        """
        Create a new company.
        
        Args:
            company_data: The company data
            created_by: Username or identifier of the creator
            
        Returns:
            The created company
        """
        # Set created_by and updated_by if not provided
        if not hasattr(company_data, 'created_by'):
            company_data.created_by = created_by
        if not hasattr(company_data, 'updated_by'):
            company_data.updated_by = created_by
            
        return self.company_repo.create(company_data)
    
    def add_contact(
        self,
        company_id: int,
        contact_data: CompanyContactCreate,
        communications: Optional[List[Dict[str, str]]] = None,
        created_by: str = "system"
    ) -> CompanyContact:
        """
        Add a contact person to a company.
        
        Args:
            company_id: The ID of the company
            contact_data: The contact data
            communications: Optional list of communication methods
            created_by: Username or identifier of who is adding the contact
            
        Returns:
            The created contact
        """
        # Set created_by and updated_by if not provided
        if not hasattr(contact_data, 'created_by'):
            contact_data.created_by = created_by
        if not hasattr(contact_data, 'updated_by'):
            contact_data.updated_by = created_by
            
        return self.company_repo.add_contact(
            company_id=company_id,
            contact_in=contact_data,
            communications=communications
        )
    
    def get_company_financial_overview(
        self,
        company_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get financial overview for a company.
        
        Args:
            company_id: The ID of the company
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Dictionary containing financial overview
        """
        overview = {
            'total_invoices': 0,
            'total_receivable': 0,
            'total_payable': 0,
            'overdue_amount': 0,
            'by_status': {},
            'by_month': {}
        }
        
        # Get company
        company = self.get_company_with_details(company_id)
        if not company:
            raise ValueError(f"Company with ID {company_id} not found")
        
        # Build base query for supplier invoices
        supplier_query = self.invoice_repo.db.query(Invoice).filter(
            Invoice.supplier_id == company_id
        )
        
        # Build base query for customer invoices
        customer_query = self.invoice_repo.db.query(Invoice).filter(
            Invoice.customer_id == company_id
        )
        
        # Apply date filters if provided
        if start_date and end_date:
            supplier_query = supplier_query.filter(
                Invoice.invoice_date.between(start_date, end_date)
            )
            customer_query = customer_query.filter(
                Invoice.invoice_date.between(start_date, end_date)
            )
        
        # Process supplier invoices (payables)
        for invoice in supplier_query.all():
            overview['total_invoices'] += 1
            overview['total_payable'] += invoice.total_amount_ttc or 0
            
            if invoice.due_date and invoice.due_date < date.today() and invoice.status != InvoiceStatus.PAID:
                overview['overdue_amount'] += invoice.total_amount_ttc or 0
            
            # Group by status
            status = invoice.status.value if invoice.status else 'UNKNOWN'
            if status not in overview['by_status']:
                overview['by_status'][status] = 0
            overview['by_status'][status] += 1
            
            # Group by month
            month_key = invoice.invoice_date.strftime('%Y-%m')
            if month_key not in overview['by_month']:
                overview['by_month'][month_key] = 0
            overview['by_month'][month_key] += 1
        
        # Process customer invoices (receivables)
        for invoice in customer_query.all():
            overview['total_receivable'] += invoice.total_amount_ttc or 0
        
        return overview
    
    def get_companies_with_outstanding_invoices(
        self,
        company_type: str = 'customer',  # 'customer' or 'supplier'
        days_overdue: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get a list of companies with outstanding invoices.
        
        Args:
            company_type: Type of companies to get ('customer' or 'supplier')
            days_overdue: Number of days after which an invoice is considered overdue
            limit: Maximum number of companies to return
            
        Returns:
            List of companies with their outstanding amounts
        """
        if company_type not in ['customer', 'supplier']:
            raise ValueError("company_type must be either 'customer' or 'supplier'")
        
        # Calculate the cutoff date
        cutoff_date = date.today() - datetime.timedelta(days=days_overdue)
        
        # Build the base query
        if company_type == 'customer':
            query = self.company_repo.db.query(Company).join(
                Invoice, Company.id == Invoice.customer_id
            )
        else:  # supplier
            query = self.company_repo.db.query(Company).join(
                Invoice, Company.id == Invoice.supplier_id
            )
        
        # Filter for unpaid or overdue invoices
        query = query.filter(
            Invoice.status != InvoiceStatus.PAID,
            Invoice.due_date <= cutoff_date
        )
        
        # Group by company and calculate totals
        results = query.with_entities(
            Company.id,
            Company.name,
            func.count(Invoice.id).label('outstanding_invoices'),
            func.sum(Invoice.total_amount_ttc).label('total_outstanding')
        ).group_by(Company.id).order_by(
            func.sum(Invoice.total_amount_ttc).desc()
        ).limit(limit).all()
        
        # Format the results
        return [
            {
                'id': r.id,
                'name': r.name,
                'outstanding_invoices': r.outstanding_invoices,
                'total_outstanding': float(r.total_outstanding or 0)
            }
            for r in results
        ]
