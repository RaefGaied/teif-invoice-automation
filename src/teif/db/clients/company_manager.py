"""
Gestionnaire avancé des opérations sur les entreprises TEIF
Version 2.1 - Améliorations de performance et de typage
"""
from typing import List, Dict, Any, Optional, Tuple, Union, TypeVar, Type, cast
from datetime import datetime, timedelta
from decimal import Decimal
import re
import logging
from contextlib import contextmanager

from sqlalchemy import func, desc, or_, and_, select
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..models.company import Company, CompanyContact, CompanyReference, CompanyCommunication
from ..models.invoice import Invoice
from ..models.audit import AuditLog
from ...config import CONFIG
from ...exceptions import TEIFValidationError, TEIFDatabaseError

# Type aliases
T = TypeVar('T')
CompanyData = Dict[str, Any]
CompanyList = List[Company]
SearchResult = Tuple[CompanyList, int]

logger = logging.getLogger(__name__)

class CompanyManager:
    """
    Gestionnaire avancé pour les opérations CRUD sur les entreprises
    
    Cette classe fournit une interface complète pour gérer les entreprises
    dans le système TEIF, avec support pour la validation, le cache, et 
    les opérations par lots.
    
    Attributes:
        session: Session SQLAlchemy pour les opérations de base de données
        config: Configuration de l'application
        _cache: Dictionnaire pour le cache en mémoire
        _cache_ttl: Dictionnaire pour les durées de vie du cache
    """
    
    def __init__(self, session: Session):
        """
        Initialise le gestionnaire d'entreprises.
        
        Args:
            session: Session SQLAlchemy à utiliser pour les opérations de base de données
        """
        self.session = session
        self.config = CONFIG
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
    
    # Cache methods with type hints
    def _is_cache_valid(self, key: str) -> bool:
        """
        Vérifie si une entrée du cache est encore valide.
        
        Args:
            key: Clé de l'entrée du cache
            
        Returns:
            bool: True si le cache est valide, False sinon
        """
        if key not in self._cache or key not in self._cache_ttl:
            return False
        return datetime.utcnow() < self._cache_ttl[key]
    
    def _set_cache(self, key: str, value: Any, ttl_minutes: int = 60) -> None:
        """
        Stocke une valeur dans le cache avec une durée de vie.
        
        Args:
            key: Clé de l'entrée du cache
            value: Valeur à mettre en cache
            ttl_minutes: Durée de vie en minutes (par défaut: 60)
        """
        self._cache[key] = value
        self._cache_ttl[key] = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache si elle est valide.
        
        Args:
            key: Clé de l'entrée du cache
            
        Returns:
            La valeur mise en cache ou None si invalide ou absente
        """
        if self._is_cache_valid(key):
            return self._cache[key]
        return None
    
    def _validate_company_data(self, company_data: CompanyData) -> List[str]:
        """
        Valide les données d'entreprise selon les règles TEIF 1.8.8.
        
        Args:
            company_data: Dictionnaire contenant les données de l'entreprise
            
        Returns:
            Liste des messages d'erreur de validation, vide si valide
            
        Raises:
            TEIFValidationError: Si les données sont invalides
        """
        errors = []
        
        # Vérification des champs obligatoires
        required_fields = ['name', 'vat_number', 'identifier', 'tax_id']
        for field in required_fields:
            if not company_data.get(field):
                errors.append(f"Le champ {field} est obligatoire")
        
        # Validation du numéro de TVA (format tunisien: 8 chiffres)
        vat_number = company_data.get('vat_number', '')
        if vat_number and not re.match(r'^\d{8}$', str(vat_number)):
            errors.append("Le numéro de TVA doit contenir 8 chiffres")
        
        # Validation de l'identifiant fiscal (format: 7 chiffres + 3 lettres + 3 chiffres)
        identifier = company_data.get('identifier', '')
        if identifier and not re.match(r'^\d{7}[A-Za-z]{3}\d{3}$', identifier):
            errors.append("L'identifiant fiscal doit être au format 1234567XXX123")
        
        # Validation de l'email
        email = company_data.get('email', '')
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append("Format d'email invalide")
        
        # Validation du téléphone (format international simplifié)
        phone = company_data.get('phone', '')
        if phone and not re.match(r'^\+?[\d\s-]{8,20}$', phone):
            errors.append("Format de téléphone invalide")
        
        # Validation du code pays (2 lettres majuscules)
        country_code = company_data.get('address_country_code', '')
        if country_code and not re.match(r'^[A-Z]{2}$', country_code):
            errors.append("Le code pays doit être sur 2 lettres majuscules")
        
        return errors
    
    @contextmanager
    def _transaction_scope(self) -> None:
        """Gère la portée d'une transaction avec rollback automatique en cas d'erreur."""
        try:
            yield
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Transaction error: {e}")
            raise
    
    def create_company(self, company_data: CompanyData) -> Company:
        """Crée une nouvelle entreprise avec validation complète"""
        try:
            # Validation des données
            validation_errors = self._validate_company_data(company_data)
            if validation_errors:
                raise TEIFValidationError(f"Erreurs de validation: {'; '.join(validation_errors)}")
            
            # Vérifier l'unicité du numéro de TVA
            existing_vat = self.session.query(Company).filter(
                Company.vat_number == company_data['vat_number']
            ).first()
            if existing_vat:
                raise TEIFValidationError(f"Une entreprise avec le numéro de TVA {company_data['vat_number']} existe déjà")
            
            # Vérifier l'unicité de l'identifiant fiscal
            existing_id = self.session.query(Company).filter(
                Company.identifier == company_data['identifier']
            ).first()
            if existing_id:
                raise TEIFValidationError(f"Une entreprise avec l'identifiant {company_data['identifier']} existe déjà")
            
            # Extraire les données des sous-objets
            references_data = company_data.pop('references', [])
            contacts_data = company_data.pop('contacts', [])
            
            # Créer l'entreprise
            company = Company(**company_data)
            self.session.add(company)
            self.session.flush()  # Pour obtenir l'ID
            
            # Ajouter les références
            for ref_data in references_data:
                reference = CompanyReference(
                    company_id=company.id,
                    **ref_data
                )
                self.session.add(reference)
            
            # Ajouter les contacts
            for contact_data in contacts_data:
                communications = contact_data.pop('communications', [])
                contact = CompanyContact(
                    company_id=company.id,
                    **contact_data
                )
                self.session.add(contact)
                self.session.flush()
                
                # Ajouter les moyens de communication
                for comm_data in communications:
                    communication = CompanyCommunication(
                        contact_id=contact.id,
                        **comm_data
                    )
                    self.session.add(communication)
            
            # Audit log
            audit = AuditLog(
                table_name='companies',
                record_id=company.id,
                action='CREATE',
                old_values=None,
                new_values=company_data,
                user_id=company_data.get('created_by', 'system')
            )
            self.session.add(audit)
            
            self.session.commit()
            
            # Invalider le cache
            self._cache.clear()
            
            logger.info(f"Entreprise créée: {company.name} (ID: {company.id})")
            return company
            
        except IntegrityError as e:
            self.session.rollback()
            raise TEIFValidationError(f"Violation de contrainte d'unicité: {e}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erreur lors de la création de l'entreprise: {e}")
            raise TEIFDatabaseError(f"Erreur lors de la création de l'entreprise: {e}")
    
    def get_company(self, company_id: int, include_details: bool = False) -> Optional[Company]:
        """Récupère une entreprise par son ID avec options de chargement"""
        cache_key = f"company_{company_id}_{include_details}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        query = self.session.query(Company).filter(Company.id == company_id)
        
        if include_details:
            query = query.options(
                selectinload(Company.references),
                selectinload(Company.contacts).selectinload(CompanyContact.communications),
                selectinload(Company.supplier_invoices),
                selectinload(Company.customer_invoices)
            )
        
        company = query.first()
        if company:
            self._set_cache(cache_key, company)
        
        return company
    
    def get_company_by_vat(self, vat_number: str) -> Optional[Company]:
        """Récupère une entreprise par son numéro de TVA"""
        cache_key = f"company_vat_{vat_number}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        company = self.session.query(Company).filter(
            Company.vat_number == vat_number,
            Company.is_active == True
        ).first()
        
        if company:
            self._set_cache(cache_key, company)
        
        return company
    
    def get_company_by_identifier(self, identifier: str) -> Optional[Company]:
        """Récupère une entreprise par son identifiant fiscal"""
        cache_key = f"company_id_{identifier}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        company = self.session.query(Company).filter(
            Company.identifier == identifier,
            Company.is_active == True
        ).first()
        
        if company:
            self._set_cache(cache_key, company)
        
        return company
    
    def search_companies(self, 
                        name: str = None, 
                        city: str = None, 
                        vat_number: str = None,
                        identifier: str = None,
                        active_only: bool = True,
                        limit: int = 50,
                        offset: int = 0,
                        order_by: str = 'name') -> SearchResult:
        """Recherche avancée des entreprises avec pagination"""
        
        query = self.session.query(Company)
        count_query = self.session.query(func.count(Company.id))
        
        # Filtres
        filters = []
        if active_only:
            filters.append(Company.is_active == True)
        
        if name:
            filters.append(Company.name.ilike(f'%{name}%'))
        
        if city:
            filters.append(Company.address_city.ilike(f'%{city}%'))
        
        if vat_number:
            filters.append(Company.vat_number.like(f'%{vat_number}%'))
        
        if identifier:
            filters.append(Company.identifier.like(f'%{identifier}%'))
        
        if filters:
            query = query.filter(and_(*filters))
            count_query = count_query.filter(and_(*filters))
        
        # Tri
        order_mapping = {
            'name': Company.name,
            'city': Company.address_city,
            'created_at': Company.created_at,
            'vat_number': Company.vat_number
        }
        
        if order_by in order_mapping:
            query = query.order_by(order_mapping[order_by])
        
        # Pagination
        total = count_query.scalar()
        companies = query.offset(offset).limit(limit).all()
        
        return companies, total
    
    def update_company(self, company_id: int, update_data: CompanyData) -> Company:
        """Met à jour une entreprise avec audit"""
        try:
            company = self.get_company(company_id)
            if not company:
                raise TEIFValidationError(f"Entreprise {company_id} non trouvée")
            
            # Sauvegarder les anciennes valeurs pour l'audit
            old_values = {
                field: getattr(company, field) 
                for field in update_data.keys() 
                if hasattr(company, field)
            }
            
            # Validation des nouvelles données
            validation_errors = self._validate_company_data(update_data)
            if validation_errors:
                raise TEIFValidationError(f"Erreurs de validation: {'; '.join(validation_errors)}")
            
            # Mettre à jour les champs
            for field, value in update_data.items():
                if hasattr(company, field):
                    setattr(company, field, value)
            
            company.updated_at = datetime.utcnow()
            
            # Audit log
            audit = AuditLog(
                table_name='companies',
                record_id=company.id,
                action='UPDATE',
                old_values=old_values,
                new_values=update_data,
                user_id=update_data.get('updated_by', 'system')
            )
            self.session.add(audit)
            
            self.session.commit()
            
            # Invalider le cache
            self._cache.clear()
            
            logger.info(f"Entreprise mise à jour: {company.name} (ID: {company.id})")
            return company
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erreur lors de la mise à jour: {e}")
            raise TEIFDatabaseError(f"Erreur lors de la mise à jour: {e}")
    
    def delete_company(self, company_id: int, force_delete: bool = False) -> bool:
        """Supprime une entreprise (soft delete par défaut)"""
        try:
            company = self.get_company(company_id)
            if not company:
                return False
            
            # Vérifier s'il y a des factures liées
            invoice_count = self.session.query(Invoice).filter(
                or_(Invoice.supplier_id == company_id, Invoice.customer_id == company_id)
            ).count()
            
            if invoice_count > 0 and not force_delete:
                # Soft delete si des factures existent
                company.is_active = False
                company.deleted_at = datetime.utcnow()
                action = 'SOFT_DELETE'
            else:
                # Hard delete si aucune facture ou force_delete=True
                self.session.delete(company)
                action = 'DELETE'
            
            # Audit log
            audit = AuditLog(
                table_name='companies',
                record_id=company.id,
                action=action,
                old_values={'is_active': True},
                new_values={'is_active': False} if action == 'SOFT_DELETE' else None,
                user_id='system'
            )
            self.session.add(audit)
            
            self.session.commit()
            
            # Invalider le cache
            self._cache.clear()
            
            logger.info(f"Entreprise supprimée ({action}): {company.name} (ID: {company.id})")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erreur lors de la suppression: {e}")
            raise TEIFDatabaseError(f"Erreur lors de la suppression: {e}")
    
    def get_company_statistics(self, company_id: int) -> Dict[str, Any]:
        """Récupère les statistiques complètes d'une entreprise"""
        try:
            company = self.get_company(company_id)
            if not company:
                raise TEIFValidationError(f"Entreprise {company_id} non trouvée")
            
            # Statistiques en tant que fournisseur
            supplier_stats = self.session.query(
                func.count(Invoice.id).label('invoice_count'),
                func.coalesce(func.sum(Invoice.total_with_tax), 0).label('total_amount'),
                func.coalesce(func.avg(Invoice.total_with_tax), 0).label('average_amount'),
                func.max(Invoice.invoice_date).label('last_invoice_date'),
                func.min(Invoice.invoice_date).label('first_invoice_date')
            ).filter(Invoice.supplier_id == company_id).first()
            
            # Statistiques en tant que client
            customer_stats = self.session.query(
                func.count(Invoice.id).label('invoice_count'),
                func.coalesce(func.sum(Invoice.total_with_tax), 0).label('total_amount'),
                func.coalesce(func.avg(Invoice.total_with_tax), 0).label('average_amount'),
                func.max(Invoice.invoice_date).label('last_invoice_date'),
                func.min(Invoice.invoice_date).label('first_invoice_date')
            ).filter(Invoice.customer_id == company_id).first()
            
            # Statistiques par mois (12 derniers mois)
            monthly_stats = self.session.query(
                func.date_trunc('month', Invoice.invoice_date).label('month'),
                func.count(Invoice.id).label('count'),
                func.sum(Invoice.total_with_tax).label('amount')
            ).filter(
                Invoice.supplier_id == company_id,
                Invoice.invoice_date >= datetime.utcnow() - timedelta(days=365)
            ).group_by(
                func.date_trunc('month', Invoice.invoice_date)
            ).order_by('month').all()
            
            return {
                'company': company,
                'as_supplier': {
                    'invoice_count': supplier_stats.invoice_count or 0,
                    'total_amount': float(supplier_stats.total_amount or 0),
                    'average_amount': float(supplier_stats.average_amount or 0),
                    'first_invoice_date': supplier_stats.first_invoice_date,
                    'last_invoice_date': supplier_stats.last_invoice_date
                },
                'as_customer': {
                    'invoice_count': customer_stats.invoice_count or 0,
                    'total_amount': float(customer_stats.total_amount or 0),
                    'average_amount': float(customer_stats.average_amount or 0),
                    'first_invoice_date': customer_stats.first_invoice_date,
                    'last_invoice_date': customer_stats.last_invoice_date
                },
                'monthly_evolution': [
                    {
                        'month': stat.month.strftime('%Y-%m'),
                        'count': stat.count,
                        'amount': float(stat.amount or 0)
                    }
                    for stat in monthly_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            raise TEIFDatabaseError(f"Erreur lors du calcul des statistiques: {e}")
    
    def get_top_suppliers(self, limit: int = 10, period_days: int = 365) -> List[Dict[str, Any]]:
        """Récupère le top des fournisseurs par chiffre d'affaires"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            results = self.session.query(
                Company,
                func.count(Invoice.id).label('invoice_count'),
                func.sum(Invoice.total_with_tax).label('total_amount'),
                func.avg(Invoice.total_with_tax).label('average_amount')
            ).join(
                Invoice, Company.id == Invoice.supplier_id
            ).filter(
                Invoice.invoice_date >= cutoff_date,
                Company.is_active == True
            ).group_by(
                Company.id
            ).order_by(
                desc('total_amount')
            ).limit(limit).all()
            
            return [
                {
                    'company': result[0],
                    'invoice_count': result[1],
                    'total_amount': float(result[2] or 0),
                    'average_amount': float(result[3] or 0)
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du top fournisseurs: {e}")
            raise TEIFDatabaseError(f"Erreur lors de la récupération du top fournisseurs: {e}")
    
    def get_top_customers(self, limit: int = 10, period_days: int = 365) -> List[Dict[str, Any]]:
        """Récupère le top des clients par montant d'achats"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            results = self.session.query(
                Company,
                func.count(Invoice.id).label('invoice_count'),
                func.sum(Invoice.total_with_tax).label('total_amount'),
                func.avg(Invoice.total_with_tax).label('average_amount')
            ).join(
                Invoice, Company.id == Invoice.customer_id
            ).filter(
                Invoice.invoice_date >= cutoff_date,
                Company.is_active == True
            ).group_by(
                Company.id
            ).order_by(
                desc('total_amount')
            ).limit(limit).all()
            
            return [
                {
                    'company': result[0],
                    'invoice_count': result[1],
                    'total_amount': float(result[2] or 0),
                    'average_amount': float(result[3] or 0)
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du top clients: {e}")
            raise TEIFDatabaseError(f"Erreur lors de la récupération du top clients: {e}")
    
    def bulk_import_companies(self, companies_data: List[CompanyData]) -> Dict[str, Any]:
        """Import en masse d'entreprises avec rapport détaillé"""
        results = {
            'success': [],
            'errors': [],
            'duplicates': [],
            'total': len(companies_data)
        }
        
        try:
            for i, company_data in enumerate(companies_data):
                try:
                    # Vérifier les doublons
                    existing = self.get_company_by_vat(company_data.get('vat_number', ''))
                    if existing:
                        results['duplicates'].append({
                            'index': i,
                            'data': company_data,
                            'existing_id': existing.id,
                            'message': f"Entreprise avec TVA {company_data.get('vat_number')} existe déjà"
                        })
                        continue
                    
                    # Créer l'entreprise
                    company = self.create_company(company_data)
                    results['success'].append({
                        'index': i,
                        'company_id': company.id,
                        'name': company.name
                    })
                    
                except Exception as e:
                    results['errors'].append({
                        'index': i,
                        'data': company_data,
                        'error': str(e)
                    })
            
            logger.info(f"Import terminé: {len(results['success'])} succès, {len(results['errors'])} erreurs, {len(results['duplicates'])} doublons")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import en masse: {e}")
            raise TEIFDatabaseError(f"Erreur lors de l'import en masse: {e}")
    
    def export_companies_teif_format(
        self,
        company_ids: Optional[List[int]] = None,
        include_inactive: bool = False,
        batch_size: int = 1000,
        fields: Optional[List[str]] = None,
        modified_since: Optional[datetime] = None,
        **filters
    ) -> Dict[str, Any]:
        """
        Exporte les entreprises au format TEIF 1.8.8 avec des options avancées.
        
        Args:
            company_ids: Liste des IDs d'entreprises à exporter (toutes si None)
            include_inactive: Inclure les entreprises inactives (désactivées)
            batch_size: Nombre d'entreprises à traiter par lot (optimisation mémoire)
            fields: Liste des champs à inclure dans l'export (tous si None)
            modified_since: Filtrer les entreprises modifiées depuis cette date
            **filters: Filtres supplémentaires (ex: name_contains='SARL')
            
        Returns:
            Dictionnaire contenant les données d'export et des métadonnées
            
        Example:
            >>> # Exporter les entreprises actives modifiées ce mois-ci
            >>> last_month = datetime.utcnow() - timedelta(days=30)
            >>> result = manager.export_companies_teif_format(
            ...     include_inactive=False,
            ...     modified_since=last_month,
            ...     name_contains='SARL'
            ... )
            >>> print(f"Exporté {len(result['data'])} entreprises")
        """
        try:
            # Construction de la requête de base
            query = self.session.query(Company).options(
                selectinload(Company.references),
                selectinload(Company.contacts).selectinload(CompanyContact.communications)
            )
            
            # Filtrage par IDs
            if company_ids is not None:
                query = query.filter(Company.id.in_(company_ids))
            
            # Filtre d'état actif/inactif
            if not include_inactive:
                query = query.filter(Company.is_active == True)
            
            # Filtre de date de modification
            if modified_since is not None:
                query = query.filter(Company.updated_at >= modified_since)
            
            # Filtres dynamiques (ex: name_contains='SARL' -> WHERE name LIKE '%SARL%')
            for key, value in filters.items():
                if key.endswith('_contains') and value:
                    field = key[:-9]  # Enlève '_contains' de la clé
                    if hasattr(Company, field):
                        query = query.filter(
                            getattr(Company, field).ilike(f'%{value}%')
                        )
                elif hasattr(Company, key):
                    query = query.filter(getattr(Company, key) == value)
            
            # Compte total pour la pagination
            total_companies = query.count()
            
            # Fonction pour générer les lots
            def generate_batches():
                offset = 0
                while offset < total_companies:
                    batch = query.offset(offset).limit(batch_size).all()
                    if not batch:
                        break
                    for company in batch:
                        yield company.to_teif_dict(fields=fields)
                    offset += batch_size
            
            # Préparation du résultat
            result = {
                'metadata': {
                    'format': 'TEIF-1.8.8',
                    'export_date': datetime.utcnow().isoformat(),
                    'company_count': total_companies,
                    'included_fields': fields or 'all',
                    'filters': {
                        'include_inactive': include_inactive,
                        'modified_since': modified_since.isoformat() if modified_since else None,
                        **filters
                    }
                },
                'data': list(generate_batches())  # Conversion en liste pour évaluation immédiate
            }
            
            logger.info(
                f"Export TEIF réussi: {total_companies} entreprises "
                f"(champs: {len(fields) if fields else 'tous'})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export TEIF: {e}", exc_info=True)
            raise TEIFDatabaseError(f"Erreur lors de l'export TEIF: {e}")

def create_sample_companies(session: Session) -> List[Company]:
    """Crée des entreprises d'exemple compatibles avec le générateur de test"""
    manager = CompanyManager(session)
    
    companies_data = [
        {
            'identifier': '1234567AAM001',
            'name': 'SOCIETE FOURNISSEUR SARL',
            'vat_number': '12345678',
            'tax_id': '1234567AAM001',
            'commercial_register': 'B1234567',
            'address_street': 'AVENUE HABIB BOURGUIBA',
            'address_city': 'TUNIS',
            'address_postal_code': '1000',
            'address_country_code': 'TN',
            'phone': '+216 70 000 000',
            'email': 'commercial@fournisseur.tn',
            'capital': Decimal('50000.000'),
            'references': [
                {
                    'reference_type': 'I-815',
                    'reference_value': 'FOURNISSEUR_REF_815',
                    'description': 'Référence I-815 du fournisseur'
                },
                {
                    'reference_type': 'I-01',
                    'reference_value': 'ACTIVITE_PRINCIPALE',
                    'description': 'Code activité principale'
                }
            ],
            'contacts': [
                {
                    'contact_type': 'commercial',
                    'first_name': 'Ahmed',
                    'last_name': 'Ben Ali',
                    'title': 'Directeur Commercial',
                    'communications': [
                        {
                            'communication_type': 'email',
                            'communication_value': 'ahmed.benali@fournisseur.tn',
                            'is_primary': True
                        },
                        {
                            'communication_type': 'phone',
                            'communication_value': '+216 70 000 001',
                            'is_primary': False
                        }
                    ]
                }
            ]
        },
        {
            'identifier': '9876543BBM002',
            'name': 'SOCIETE CLIENTE SARL',
            'vat_number': '87654321',
            'tax_id': '9876543BBM002',
            'commercial_register': 'B9876543',
            'address_street': 'AVENUE MOHAMED V',
            'address_city': 'SOUSSE',
            'address_postal_code': '4000',
            'address_country_code': 'TN',
            'phone': '+216 71 000 001',
            'email': 'achat@client.tn',
            'capital': Decimal('100000.000'),
            'references': [
                {
                    'reference_type': 'I-1602',
                    'reference_value': 'CLIENT_REF_1602',
                    'description': 'Référence I-1602 du client'
                }
            ],
            'contacts': [
                {
                    'contact_type': 'achat',
                    'first_name': 'Fatma',
                    'last_name': 'Trabelsi',
                    'title': 'Responsable Achats',
                    'communications': [
                        {
                            'communication_type': 'email',
                            'communication_value': 'fatma.trabelsi@client.tn',
                            'is_primary': True
                        }
                    ]
                }
            ]
        }
    ]
    
    companies = []
    for company_data in companies_data:
        try:
            # Vérifier si l'entreprise existe déjà
            existing = manager.get_company_by_vat(company_data['vat_number'])
            if existing:
                companies.append(existing)
                logger.info(f"Entreprise existante trouvée: {existing.name}")
            else:
                company = manager.create_company(company_data)
                companies.append(company)
                logger.info(f"Entreprise créée: {company.name}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'entreprise {company_data['name']}: {e}")
    
    return companies

def get_or_create_company_from_teif_data(session: Session, teif_data: Dict[str, Any]) -> Company:
    """Récupère ou crée une entreprise à partir des données TEIF"""
    manager = CompanyManager(session)
    
    # Extraire les informations de l'entreprise depuis les données TEIF
    vat_number = teif_data.get('vat_number') or teif_data.get('identifier', '')
    
    # Chercher d'abord par numéro de TVA
    company = manager.get_company_by_vat(vat_number)
    if company:
        return company
    
    # Chercher par identifiant fiscal
    identifier = teif_data.get('identifier', '')
    if identifier:
        company = manager.get_company_by_identifier(identifier)
        if company:
            return company
    
    # Créer une nouvelle entreprise si elle n'existe pas
    company_data = {
        'identifier': teif_data.get('identifier', ''),
        'name': teif_data.get('name', ''),
        'vat_number': vat_number,
        'tax_id': teif_data.get('tax_id', identifier),
        'commercial_register': teif_data.get('commercial_register', ''),
        'address_street': teif_data.get('address', {}).get('street', ''),
        'address_city': teif_data.get('address', {}).get('city', ''),
        'address_postal_code': teif_data.get('address', {}).get('postal_code', ''),
        'address_country_code': teif_data.get('address', {}).get('country_code', 'TN'),
        'phone': teif_data.get('phone', ''),
        'email': teif_data.get('email', ''),
        'capital': Decimal(str(teif_data.get('capital', 0)))
    }
    
    # Ajouter les références si présentes
    if 'references' in teif_data:
        company_data['references'] = teif_data['references']
    
    # Ajouter les contacts si présents
    if 'contacts' in teif_data:
        company_data['contacts'] = teif_data['contacts']
    
    return manager.create_company(company_data)
