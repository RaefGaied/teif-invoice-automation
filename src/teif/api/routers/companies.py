from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....db.services import CompanyService
from ....schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    Company as CompanySchema,
    CompanyContactCreate,
    CompanyContact as CompanyContactSchema
)

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/", response_model=List[CompanySchema])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all companies with optional search and pagination.
    """
    service = CompanyService(db)
    if search:
        return service.search_companies(search, skip=skip, limit=limit)
    return service.get_multi(skip=skip, limit=limit)

@router.post("/", response_model=CompanySchema, status_code=status.HTTP_201_CREATED)
async def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new company.
    """
    service = CompanyService(db)
    return service.create(company)

@router.get("/{company_id}", response_model=CompanySchema)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a company by ID.
    """
    service = CompanyService(db)
    company = service.get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )
    return company

@router.put("/{company_id}", response_model=CompanySchema)
async def update_company(
    company_id: int,
    company_in: CompanyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a company.
    """
    service = CompanyService(db)
    company = service.get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )
    return service.update(db_obj=company, obj_in=company_in)

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a company.
    """
    service = CompanyService(db)
    company = service.get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )
    service.remove(id=company_id)
    return None

@router.post("/{company_id}/contacts", response_model=CompanyContactSchema, status_code=status.HTTP_201_CREATED)
async def add_company_contact(
    company_id: int,
    contact: CompanyContactCreate,
    db: Session = Depends(get_db)
):
    """
    Add a contact to a company.
    """
    service = CompanyService(db)
    company = service.get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )
    return service.add_contact(company_id, contact)

@router.get("/{company_id}/financial-overview")
async def get_company_financial_overview(
    company_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get financial overview for a company.
    """
    from datetime import datetime
    
    service = CompanyService(db)
    
    # Parse dates if provided
    start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    
    try:
        return service.get_company_financial_overview(
            company_id=company_id,
            start_date=start,
            end_date=end
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
