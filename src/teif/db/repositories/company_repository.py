from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from ..models.company import Company, CompanyReference, CompanyContact, ContactCommunication
from .base import BaseRepository
from ..schemas.company import CompanyCreate, CompanyUpdate, CompanyReferenceCreate, CompanyContactCreate

class CompanyRepository(BaseRepository[Company, CompanyCreate, CompanyUpdate]):
    """Repository for company operations."""
    
    def __init__(self, db: Session):
        super().__init__(Company, db)
    
    def get_with_details(self, id: int) -> Optional[Company]:
        """Get a company by ID with all related data loaded."""
        return self.db.query(Company).options(
            joinedload(Company.references),
            joinedload(Company.contacts).joinedload(CompanyContact.communications),
            joinedload(Company.supplier_invoices),
            joinedload(Company.customer_invoices)
        ).filter(Company.id == id).first()
    
    def get_by_identifier(self, identifier: str) -> Optional[Company]:
        """Get a company by its unique identifier."""
        return self.db.query(Company).filter(
            func.lower(Company.identifier) == func.lower(identifier)
        ).first()
    
    def get_by_vat_number(self, vat_number: str) -> Optional[Company]:
        """Get a company by VAT number."""
        return self.db.query(Company).filter(
            func.lower(Company.vat_number) == func.lower(vat_number)
        ).first()
    
    def search_companies(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Company]:
        """Search companies by name, identifier, VAT number, or tax ID."""
        search = f"%{query}%"
        return self.db.query(Company).filter(
            or_(
                Company.name.ilike(search),
                Company.identifier.ilike(search),
                Company.vat_number.ilike(search),
                Company.tax_id.ilike(search) if Company.tax_id is not None else False
            )
        ).order_by(Company.name).offset(skip).limit(limit).all()
    
    def get_companies_by_type(
        self,
        company_type: str,  # 'supplier', 'customer', or 'all'
        skip: int = 0,
        limit: int = 100
    ) -> List[Company]:
        """Get companies by their type (supplier, customer, or all)."""
        query = self.db.query(Company)
        
        if company_type == 'supplier':
            query = query.filter(Company.supplier_invoices.any())
        elif company_type == 'customer':
            query = query.filter(Company.customer_invoices.any())
        
        return query.order_by(Company.name).offset(skip).limit(limit).all()
    
    def create_with_references(
        self, 
        company_in: CompanyCreate, 
        references: Optional[List[CompanyReferenceCreate]] = None
    ) -> Company:
        """Create a company with its references in a transaction."""
        try:
            db_company = Company(**company_in.dict(exclude={"references"}))
            self.db.add(db_company)
            self.db.flush()  # Get the company ID
            
            if references:
                for ref_in in references:
                    db_ref = CompanyReference(
                        **ref_in.dict(),
                        company_id=db_company.id
                    )
                    self.db.add(db_ref)
            
            self.db.commit()
            self.db.refresh(db_company)
            return db_company
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def add_contact(
        self,
        company_id: int,
        contact_in: CompanyContactCreate,
        communications: Optional[List[Dict[str, str]]] = None
    ) -> CompanyContact:
        """Add a contact person to a company with their communications."""
        try:
            db_contact = CompanyContact(
                **contact_in.dict(exclude={"communications"}),
                company_id=company_id
            )
            self.db.add(db_contact)
            self.db.flush()
            
            if communications:
                for comm in communications:
                    db_comm = ContactCommunication(
                        contact_id=db_contact.id,
                        communication_type=comm["type"],
                        communication_value=comm["value"]
                    )
                    self.db.add(db_comm)
            
            self.db.commit()
            self.db.refresh(db_contact)
            return db_contact
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_company_stats(self, company_id: int) -> Dict[str, Any]:
        """Get statistics for a company."""
        stats = {
            'total_invoices': 0,
            'total_supplier_invoices': 0,
            'total_customer_invoices': 0,
            'total_amount_ht': 0,
            'total_amount_ttc': 0,
            'last_invoice_date': None,
            'active': False
        }
        
        company = self.get_with_details(company_id)
        if not company:
            return stats
            
        stats['active'] = company.is_active
        
        # Get supplier invoice stats
        if company.supplier_invoices:
            stats['total_supplier_invoices'] = len(company.supplier_invoices)
            stats['total_invoices'] += stats['total_supplier_invoices']
            
            # Calculate totals
            for inv in company.supplier_invoices:
                stats['total_amount_ht'] += (inv.total_amount_ht or 0)
                stats['total_amount_ttc'] += (inv.total_amount_ttc or 0)
                
                if not stats['last_invoice_date'] or (inv.invoice_date and inv.invoice_date > stats['last_invoice_date']):
                    stats['last_invoice_date'] = inv.invoice_date
        
        # Get customer invoice stats
        if company.customer_invoices:
            stats['total_customer_invoices'] = len(company.customer_invoices)
            stats['total_invoices'] += stats['total_customer_invoices']
            
            # Calculate totals
            for inv in company.customer_invoices:
                stats['total_amount_ht'] += (inv.total_amount_ht or 0)
                stats['total_amount_ttc'] += (inv.total_amount_ttc or 0)
                
                if not stats['last_invoice_date'] or (inv.invoice_date and inv.invoice_date > stats['last_invoice_date']):
                    stats['last_invoice_date'] = inv.invoice_date
        
        return stats