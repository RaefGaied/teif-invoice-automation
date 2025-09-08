"""
Gestionnaire de base de données SQLAlchemy optimisé pour SQL Server
Gère la création, configuration et maintenance de la base TEIF
Version mise à jour pour supporter les structures TEIF complètes
"""
import os
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Generator, Union
from sqlalchemy import create_engine, event, text, and_, or_
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import json

from .models import (
    Base, TEIFReferenceCode, Company, CompanyReference, CompanyContact, 
    ContactCommunication, Invoice, InvoiceLine, InvoiceTax, InvoicePayment,
    InvoiceReference, InvoiceSignature
)
from ..config import get_database_config

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLServerDatabaseManager:
    """
    Gestionnaire spécialisé pour SQL Server avec support TEIF complet
    Optimisé pour les performances et la compatibilité TEIF 1.8.8
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialise le gestionnaire SQL Server
        
        Args:
            database_url: URL de connexion SQL Server
        """
        if database_url is None:
            config = get_database_config()
            database_url = config['url']
        
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Configure le moteur SQLAlchemy pour SQL Server"""
        try:
            # Configuration optimisée pour SQL Server
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=15,  # Augmenté pour les tests
                max_overflow=25,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
                connect_args={
                    "timeout": 30,
                    "autocommit": False,
                    "isolation_level": "READ_COMMITTED"
                }
            )
            
            # Configuration de la session
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"✅ Moteur SQL Server configuré avec pool étendu")
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration moteur SQL Server: {e}")
            raise
    
    def create_database(self):
        """
        Crée la base de données complète avec toutes les tables et données TEIF
        """
        try:
            logger.info("🚀 Création de la base de données TEIF sur SQL Server...")
            
            # Étape 1: Créer toutes les tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Tables créées avec succès")
            
            # Étape 2: Insérer les données de référence TEIF
            self._insert_teif_reference_data()
            
            # Étape 3: Créer les entreprises de test
            self._create_sample_companies()
            
            # Étape 4: Créer des factures de test
            self._create_sample_invoices()
            
            # Étape 5: Optimiser les performances
            self._optimize_database()
            
            logger.info("🎉 Base de données TEIF créée avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de la base: {e}")
            raise
    
    def _insert_teif_reference_data(self):
        """
        Insère tous les codes de référence TEIF 1.8.8
        Basé sur les spécifications officielles tunisiennes
        """
        with self.get_session() as session:
            try:
                # Vérifier si les données existent déjà
                if session.query(TEIFReferenceCode).first():
                    logger.info("📋 Codes de référence TEIF déjà présents")
                    return
                
                logger.info("📝 Insertion des codes de référence TEIF 1.8.8...")
                
                # Codes de référence TEIF complets
                reference_codes = [
                    # I-0: Types d'Identifiants Partenaires
                    ('PARTNER_ID_TYPE', 'I-01', 'Matricule Fiscal Tunisien', 'Matricule fiscal tunisien obligatoire', True),
                    ('PARTNER_ID_TYPE', 'I-02', 'Carte d\'identité nationale', 'Carte d\'identité nationale', False),
                    ('PARTNER_ID_TYPE', 'I-03', 'Carte de séjour', 'Carte de séjour pour non-résidents', False),
                    ('PARTNER_ID_TYPE', 'I-04', 'Matricule Fiscal non tunisien', 'Matricule fiscal étranger', False),
                    
                    # I-1: Types de Documents
                    ('DOCUMENT_TYPE', 'I-11', 'Facture', 'Facture commerciale standard', True),
                    ('DOCUMENT_TYPE', 'I-12', 'Facture d\'avoir', 'Note de crédit', False),
                    ('DOCUMENT_TYPE', 'I-13', 'Note d\'honoraire', 'Note d\'honoraire professionnelle', False),
                    ('DOCUMENT_TYPE', 'I-14', 'Décompte', 'Décompte marché public', False),
                    ('DOCUMENT_TYPE', 'I-15', 'Facture Export', 'Facture d\'exportation', False),
                    ('DOCUMENT_TYPE', 'I-16', 'Bon de commande', 'Bon de commande', False),
                    
                    # I-2: Codes de Langue
                    ('LANGUAGE_CODE', 'ar', 'Arabe', 'Langue arabe', True),
                    ('LANGUAGE_CODE', 'fr', 'Français', 'Langue française', True),
                    ('LANGUAGE_CODE', 'en', 'Anglais', 'Langue anglaise', False),
                    ('LANGUAGE_CODE', 'or', 'Autre', 'Autre langue', False),
                    
                    # I-3: Fonctions de Date
                    ('DATE_FUNCTION', 'I-31', 'Date d\'émission du document', 'Date d\'émission de la facture', True),
                    ('DATE_FUNCTION', 'I-32', 'Date limite de paiement', 'Date d\'échéance de paiement', True),
                    ('DATE_FUNCTION', 'I-33', 'Date de confirmation', 'Date de confirmation du document', False),
                    ('DATE_FUNCTION', 'I-34', 'Date d\'expiration', 'Date d\'expiration', False),
                    ('DATE_FUNCTION', 'I-35', 'Date du fichier joint', 'Date du fichier attaché', False),
                    ('DATE_FUNCTION', 'I-36', 'Période de facturation', 'Période de facturation', False),
                    ('DATE_FUNCTION', 'I-37', 'Date de génération de référence', 'Date de génération de la référence', False),
                    ('DATE_FUNCTION', 'I-38', 'Autre', 'Autre type de date', False),
                    
                    # I-6: Fonctions Partenaires
                    ('PARTNER_FUNCTION', 'I-61', 'Acheteur', 'Partie acheteuse', True),
                    ('PARTNER_FUNCTION', 'I-62', 'Fournisseur', 'Partie vendeuse', True),
                    ('PARTNER_FUNCTION', 'I-63', 'Vendeur', 'Vendeur', False),
                    ('PARTNER_FUNCTION', 'I-64', 'Client', 'Client', False),
                    ('PARTNER_FUNCTION', 'I-65', 'Receveur de la facture', 'Destinataire facture', False),
                    ('PARTNER_FUNCTION', 'I-66', 'Émetteur de la facture', 'Émetteur facture', False),
                    
                    # I-8: Qualifiants de Référence
                    ('REFERENCE_QUALIFIER', 'I-815', 'Registre de commerce', 'Registre de commerce', True),
                    ('REFERENCE_QUALIFIER', 'I-88', 'Référence TTN de la facture', 'Référence TTN', True),
                    ('REFERENCE_QUALIFIER', 'I-82', 'Référence Banque', 'Référence bancaire', False),
                    ('REFERENCE_QUALIFIER', 'I-83', 'Numéro bon de commande', 'N° bon de commande', False),
                    ('REFERENCE_QUALIFIER', 'I-84', 'Numéro bon de livraison', 'N° bon de livraison', False),
                    ('REFERENCE_QUALIFIER', 'I-85', 'Numéro autorisation suspension TVA', 'N° autorisation TVA', False),
                    
                    # I-9: Fonctions de Contact
                    ('CONTACT_FUNCTION', 'I-91', 'Contact Technique', 'Contact technique', False),
                    ('CONTACT_FUNCTION', 'I-92', 'Contact juridique', 'Contact juridique', False),
                    ('CONTACT_FUNCTION', 'I-93', 'Contact Commercial', 'Contact commercial', True),
                    ('CONTACT_FUNCTION', 'I-94', 'Autre', 'Autre contact', False),
                    
                    # I-10: Moyens de Communication
                    ('COMMUNICATION_MEANS', 'I-101', 'Téléphone', 'Numéro de téléphone', True),
                    ('COMMUNICATION_MEANS', 'I-102', 'Fax', 'Numéro de fax', False),
                    ('COMMUNICATION_MEANS', 'I-103', 'Email', 'Adresse email', True),
                    ('COMMUNICATION_MEANS', 'I-104', 'Autre', 'Autre moyen', False),
                    
                    # I-11 & I-12: Conditions de Paiement
                    ('PAYMENT_CONDITION', 'I-111', 'Basic', 'Paiement de base', True),
                    ('PAYMENT_CONDITION', 'I-114', 'Par virement bancaire', 'Virement bancaire', True),
                    ('PAYMENT_METHOD', 'I-121', 'Paiement direct', 'Paiement direct', True),
                    
                    # I-13: Moyens de Paiement
                    ('PAYMENT_MEANS', 'I-131', 'Espèce', 'Paiement en espèces', False),
                    ('PAYMENT_MEANS', 'I-132', 'Chèque', 'Paiement par chèque', True),
                    ('PAYMENT_MEANS', 'I-135', 'Virement bancaire', 'Virement bancaire', True),
                    
                    # I-14: Institutions Financières
                    ('FINANCIAL_INSTITUTION', 'I-142', 'Banque', 'Institution bancaire', True),
                    
                    # I-15: Types d'Allocation
                    ('ALLOCATION_TYPE', 'I-151', 'Réduction', 'Réduction commerciale', True),
                    ('ALLOCATION_TYPE', 'I-152', 'Ristourne', 'Ristourne', False),
                    ('ALLOCATION_TYPE', 'I-153', 'Rabais', 'Rabais', False),
                    
                    # I-16: Types de Taxes
                    ('TAX_TYPE', 'I-1601', 'Droit de timbre', 'Droit de timbre', False),
                    ('TAX_TYPE', 'I-1602', 'TVA', 'Taxe sur la valeur ajoutée', True),
                    ('TAX_TYPE', 'I-1603', 'Autre', 'Autre taxe', False),
                    ('TAX_TYPE', 'I-1604', 'Retenue à la source', 'Retenue source', False),
                    
                    # I-17: Types de Montants
                    ('AMOUNT_TYPE', 'I-176', 'Montant total HT facture', 'Total HT facture', True),
                    ('AMOUNT_TYPE', 'I-178', 'Montant Taxe', 'Montant des taxes', True),
                    ('AMOUNT_TYPE', 'I-180', 'Montant Total TTC facture', 'Total TTC facture', True),
                    ('AMOUNT_TYPE', 'I-181', 'Montant total Taxe', 'Total des taxes', True),
                    ('AMOUNT_TYPE', 'I-182', 'Montant total base taxe', 'Total base taxable', False),
                    ('AMOUNT_TYPE', 'I-183', 'Montant HT article unitaire', 'HT unitaire article', True),
                    ('AMOUNT_TYPE', 'I-184', 'Montant total TTC charges/Services', 'Total TTC charges', False),
                    ('AMOUNT_TYPE', 'I-185', 'Montant total exonéré', 'Total exonéré', False),
                    
                    # Catégories de taxes
                    ('TAX_CATEGORY', 'S', 'Standard', 'Taux standard', True),
                    ('TAX_CATEGORY', 'E', 'Exonéré', 'Exonéré de taxe', False),
                    ('TAX_CATEGORY', 'Z', 'Zéro', 'Taux zéro', False),
                    
                    # Unités de mesure
                    ('UNIT', 'PCE', 'Pièce', 'Unité pièce', True),
                    ('UNIT', 'KIT', 'Kit', 'Kit ou ensemble', False),
                    ('UNIT', 'H', 'Heure', 'Heure de travail', False),
                    ('UNIT', 'KG', 'Kilogramme', 'Kilogramme', False),
                    ('UNIT', 'M', 'Mètre', 'Mètre', False),
                ]
                
                # Insérer tous les codes
                for code_type, code_value, label, description, is_mandatory in reference_codes:
                    ref_code = TEIFReferenceCode(
                        code_type=code_type,
                        code_value=code_value,
                        code_label=label,
                        description=description,
                        is_mandatory=is_mandatory
                    )
                    session.add(ref_code)
                
                session.commit()
                logger.info(f"✅ {len(reference_codes)} codes de référence TEIF insérés")
                
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Erreur insertion codes TEIF: {e}")
                raise
    
    def _create_sample_companies(self):
        """Crée des entreprises d'exemple pour les tests"""
        with self.get_session() as session:
            try:
                # Vérifier si des entreprises existent déjà
                if session.query(Company).first():
                    logger.info("🏢 Entreprises d'exemple déjà présentes")
                    return
                
                logger.info("🏢 Création des entreprises d'exemple...")
                
                # Fournisseur de test
                supplier = Company(
                    identifier='1234567AAM001',
                    name='SOCIETE FOURNISSEUR SARL',
                    vat_number='12345678',
                    tax_id='1234567AAM001',
                    commercial_register='B1234567',
                    address_street='AVENUE HABIB BOURGUIBA',
                    address_city='TUNIS',
                    address_postal_code='1000',
                    address_country_code='TN',
                    address_language='fr',
                    phone='+216 70 000 000',
                    email='commercial@fournisseur.tn',
                    capital=Decimal('50000.000'),
                    company_type='SARL'
                )
                session.add(supplier)
                session.flush()  # Pour obtenir l'ID
                
                # Ajouter des références au fournisseur
                supplier_refs = [
                    CompanyReference(
                        company_id=supplier.id,
                        reference_type='I-815',
                        reference_value='B1234567',
                        description='Registre de commerce'
                    ),
                    CompanyReference(
                        company_id=supplier.id,
                        reference_type='I-82',
                        reference_value='TN5904018104003691234567',
                        description='IBAN principal'
                    )
                ]
                
                for ref in supplier_refs:
                    session.add(ref)
                
                # Ajouter un contact commercial
                supplier_contact = CompanyContact(
                    company_id=supplier.id,
                    function_code='I-93',
                    name='Service Commercial',
                    identifier='COMM',
                    department='Commercial'
                )
                session.add(supplier_contact)
                session.flush()
                
                # Moyens de communication du contact
                supplier_comms = [
                    ContactCommunication(
                        contact_id=supplier_contact.id,
                        communication_type='I-101',
                        value='+216 70 000 000',
                        is_primary=True
                    ),
                    ContactCommunication(
                        contact_id=supplier_contact.id,
                        communication_type='I-103',
                        value='commercial@fournisseur.tn',
                        is_primary=True
                    )
                ]
                
                for comm in supplier_comms:
                    session.add(comm)
                
                # Client de test
                customer = Company(
                    identifier='9876543BBM002',
                    name='SOCIETE CLIENTE SARL',
                    vat_number='87654321',
                    tax_id='9876543BBM002',
                    commercial_register='B9876543',
                    address_street='AVENUE MOHAMED V',
                    address_city='SOUSSE',
                    address_postal_code='4000',
                    address_country_code='TN',
                    address_language='fr',
                    phone='+216 71 000 001',
                    email='achat@client.tn',
                    capital=Decimal('100000.000'),
                    company_type='SARL'
                )
                session.add(customer)
                session.flush()
                
                # Contact client
                customer_contact = CompanyContact(
                    company_id=customer.id,
                    function_code='I-93',
                    name='Service Achat',
                    identifier='ACHAT',
                    department='Achats'
                )
                session.add(customer_contact)
                session.flush()
                
                # Communications client
                customer_comms = [
                    ContactCommunication(
                        contact_id=customer_contact.id,
                        communication_type='I-101',
                        value='+216 71 000 001',
                        is_primary=True
                    ),
                    ContactCommunication(
                        contact_id=customer_contact.id,
                        communication_type='I-103',
                        value='achat@client.tn',
                        is_primary=True
                    )
                ]
                
                for comm in customer_comms:
                    session.add(comm)
                
                session.commit()
                logger.info("✅ Entreprises d'exemple créées avec succès")
                
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Erreur création entreprises: {e}")
                raise
    
    def _create_sample_invoices(self):
        """Crée des factures d'exemple pour les tests"""
        with self.get_session() as session:
            try:
                # Vérifier si des factures existent déjà
                if session.query(Invoice).first():
                    logger.info("📄 Factures d'exemple déjà présentes")
                    return
                
                logger.info("📄 Création des factures d'exemple...")
                
                # Récupérer les entreprises
                supplier = session.query(Company).filter_by(identifier='1234567AAM001').first()
                customer = session.query(Company).filter_by(identifier='9876543BBM002').first()
                
                if not supplier or not customer:
                    logger.warning("⚠️ Entreprises non trouvées, création des factures ignorée")
                    return
                
                # Facture de test 1
                invoice1 = Invoice(
                    invoice_number='FACT-2023-001',
                    document_type='I-11',
                    issue_date=datetime.now().date(),
                    due_date=(datetime.now() + timedelta(days=30)).date(),
                    currency_code='TND',
                    supplier_id=supplier.id,
                    customer_id=customer.id,
                    total_amount_excl_tax=Decimal('602.00'),
                    total_tax_amount=Decimal('114.38'),
                    total_amount_incl_tax=Decimal('716.38'),
                    status='DRAFT',
                    teif_version='1.8.8'
                )
                session.add(invoice1)
                session.flush()
                
                # Lignes de facture
                lines_data = [
                    {
                        'line_number': 1,
                        'item_identifier': 'DDM-001',
                        'item_code': 'DDM-001',
                        'description': 'Dossier Délivrance de Marchandises',
                        'quantity': Decimal('1.0'),
                        'unit_code': 'PCE',
                        'unit_price': Decimal('2.00'),
                        'line_amount': Decimal('2.00'),
                        'tax_rate': Decimal('19.0'),
                        'tax_amount': Decimal('0.38')
                    },
                    {
                        'line_number': 2,
                        'item_identifier': 'KIT-001',
                        'item_code': 'KIT-001',
                        'description': 'Kit d\'installation professionnel',
                        'quantity': Decimal('1.0'),
                        'unit_code': 'KIT',
                        'unit_price': Decimal('600.00'),
                        'line_amount': Decimal('600.00'),
                        'tax_rate': Decimal('19.0'),
                        'tax_amount': Decimal('114.00')
                    }
                ]
                
                for line_data in lines_data:
                    line = InvoiceLine(
                        invoice_id=invoice1.id,
                        **line_data
                    )
                    session.add(line)
                
                # Taxes de la facture
                taxes_data = [
                    {
                        'tax_type_code': 'I-1602',
                        'tax_category': 'S',
                        'tax_rate': Decimal('19.0'),
                        'taxable_amount': Decimal('602.00'),
                        'tax_amount': Decimal('114.38')
                    }
                ]
                
                for tax_data in taxes_data:
                    tax = InvoiceTax(
                        invoice_id=invoice1.id,
                        **tax_data
                    )
                    session.add(tax)
                
                # Références de la facture
                references_data = [
                    {
                        'reference_type': 'I-83',
                        'reference_value': 'CMD-2023-456',
                        'description': 'Numéro bon de commande'
                    }
                ]
                
                for ref_data in references_data:
                    ref = InvoiceReference(
                        invoice_id=invoice1.id,
                        **ref_data
                    )
                    session.add(ref)
                
                # Paiement de la facture
                payment = InvoicePayment(
                    invoice_id=invoice1.id,
                    payment_means_code='I-135',
                    payment_id='VIR-2023-001',
                    due_date=(datetime.now() + timedelta(days=30)).date(),
                    account_iban='TN5904018104003691234567',
                    account_holder='SOCIETE FOURNISSEUR SARL',
                    bank_name='BNA'
                )
                session.add(payment)
                
                session.commit()
                logger.info("✅ Factures d'exemple créées avec succès")
                
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Erreur création factures: {e}")
                raise
    
    def _optimize_database(self):
        """Optimise la base de données SQL Server"""
        try:
            with self.engine.connect() as connection:
                # Mettre à jour les statistiques
                connection.execute(text("EXEC sp_updatestats"))
                
                # Réorganiser les index si nécessaire
                connection.execute(text("""
                    DECLARE @sql NVARCHAR(MAX) = ''
                    SELECT @sql = @sql + 'ALTER INDEX ALL ON ' + QUOTENAME(SCHEMA_NAME(schema_id)) + '.' + QUOTENAME(name) + ' REORGANIZE;' + CHAR(13)
                    FROM sys.tables WHERE is_ms_shipped = 0
                    EXEC sp_executesql @sql
                """))
                
                connection.commit()
                logger.info("✅ Base de données optimisée")
                
        except Exception as e:
            logger.warning(f"⚠️ Optimisation partielle: {e}")
    
    # Nouvelles méthodes pour gérer les factures complètes
    
    def create_invoice_from_teif_data(self, teif_data: Dict[str, Any]) -> Optional[int]:
        """
        Crée une facture complète à partir des données TEIF
        
        Args:
            teif_data: Données de facture au format TEIF
            
        Returns:
            ID de la facture créée ou None en cas d'erreur
        """
        with self.get_session() as session:
            try:
                # Extraire les informations de base
                header = teif_data.get('header', {})
                bgm = teif_data.get('bgm', {})
                seller = teif_data.get('seller', {})
                buyer = teif_data.get('buyer', {})
                totals = teif_data.get('totals', {})
                
                # Créer ou récupérer le fournisseur
                supplier = self._get_or_create_company(session, seller, 'supplier')
                
                # Créer ou récupérer le client
                customer = self._get_or_create_company(session, buyer, 'customer')
                
                # Créer la facture
                invoice = Invoice(
                    invoice_number=bgm.get('document_number', f'INV-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
                    document_type=bgm.get('document_type', 'I-11'),
                    issue_date=datetime.now().date(),
                    due_date=(datetime.now() + timedelta(days=30)).date(),
                    currency_code=totals.get('currency', 'TND'),
                    supplier_id=supplier.id,
                    customer_id=customer.id,
                    total_amount_excl_tax=Decimal(str(totals.get('total_without_tax', 0))),
                    total_tax_amount=Decimal(str(totals.get('tax_amount', 0))),
                    total_amount_incl_tax=Decimal(str(totals.get('total_with_tax', 0))),
                    status='DRAFT',
                    teif_version='1.8.8'
                )
                session.add(invoice)
                session.flush()
                
                # Ajouter les lignes de facture
                lines = teif_data.get('lines', [])
                for idx, line_data in enumerate(lines, 1):
                    line = InvoiceLine(
                        invoice_id=invoice.id,
                        line_number=idx,
                        item_identifier=line_data.get('item_identifier', f'ITEM-{idx}'),
                        item_code=line_data.get('item_code', ''),
                        description=line_data.get('description', ''),
                        quantity=Decimal(str(line_data.get('quantity', 1))),
                        unit_code=line_data.get('unit', 'PCE'),
                        unit_price=Decimal(str(line_data.get('unit_price', 0))),
                        line_amount=Decimal(str(line_data.get('quantity', 1))) * Decimal(str(line_data.get('unit_price', 0))),
                        tax_rate=Decimal(str(line_data.get('taxes', [{}])[0].get('rate', 0) if line_data.get('taxes') else 0)),
                        tax_amount=Decimal(str(line_data.get('taxes', [{}])[0].get('amount', 0) if line_data.get('taxes') else 0))
                    )
                    session.add(line)
                
                # Ajouter les taxes
                taxes = teif_data.get('taxes', [])
                for tax_data in taxes:
                    tax = InvoiceTax(
                        invoice_id=invoice.id,
                        tax_type_code=tax_data.get('code', 'I-1602'),
                        tax_category=tax_data.get('category', 'S'),
                        tax_rate=Decimal(str(tax_data.get('rate', 0))),
                        taxable_amount=Decimal(str(tax_data.get('basis', 0))),
                        tax_amount=Decimal(str(tax_data.get('amount', 0)))
                    )
                    session.add(tax)
                
                # Ajouter les moyens de paiement
                payment_means = teif_data.get('payment_means', {})
                if payment_means:
                    payment = InvoicePayment(
                        invoice_id=invoice.id,
                        payment_means_code=payment_means.get('payment_means_code', 'I-135'),
                        payment_id=payment_means.get('payment_id', ''),
                        due_date=(datetime.now() + timedelta(days=30)).date(),
                        account_iban=payment_means.get('payee_financial_account', {}).get('iban', ''),
                        account_holder=payment_means.get('payee_financial_account', {}).get('account_holder', ''),
                        bank_name=payment_means.get('payee_financial_account', {}).get('financial_institution', '')
                    )
                    session.add(payment)
                
                session.commit()
                logger.info(f"✅ Facture {invoice.invoice_number} créée avec ID {invoice.id}")
                return invoice.id
                
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Erreur création facture TEIF: {e}")
                return None
    
    def _get_or_create_company(self, session: Session, company_data: Dict[str, Any], role: str) -> Company:
        """
        Récupère ou crée une entreprise
        
        Args:
            session: Session de base de données
            company_data: Données de l'entreprise
            role: Rôle (supplier/customer)
            
        Returns:
            Instance de Company
        """
        identifier = company_data.get('identifier', '')
        
        # Chercher l'entreprise existante
        company = session.query(Company).filter_by(identifier=identifier).first()
        
        if not company:
            # Créer une nouvelle entreprise
            address = company_data.get('address', {})
            company = Company(
                identifier=identifier,
                name=company_data.get('name', ''),
                vat_number=company_data.get('vat_number', ''),
                tax_id=identifier,
                commercial_register=company_data.get('commercial_register', ''),
                address_street=address.get('street', ''),
                address_city=address.get('city', ''),
                address_postal_code=address.get('postal_code', ''),
                address_country_code=address.get('country_code', 'TN'),
                address_language=address.get('lang', 'fr'),
                phone=company_data.get('phone', ''),
                email=company_data.get('email', ''),
                capital=Decimal(str(company_data.get('capital', 0))),
                company_type='SARL'
            )
            session.add(company)
            session.flush()
            
            # Ajouter les références
            references = company_data.get('references', [])
            for ref_data in references:
                ref = CompanyReference(
                    company_id=company.id,
                    reference_type=ref_data.get('type', ''),
                    reference_value=ref_data.get('value', ''),
                    description=ref_data.get('description', '')
                )
                session.add(ref)
            
            # Ajouter les contacts
            contacts = company_data.get('contacts', [])
            for contact_data in contacts:
                contact = CompanyContact(
                    company_id=company.id,
                    function_code=contact_data.get('function_code', 'I-93'),
                    name=contact_data.get('name', ''),
                    identifier=contact_data.get('identifier', ''),
                    department=contact_data.get('department', '')
                )
                session.add(contact)
                session.flush()
                
                # Ajouter les communications
                communications = contact_data.get('communications', [])
                for comm_data in communications:
                    comm = ContactCommunication(
                        contact_id=contact.id,
                        communication_type=comm_data.get('type', 'I-103'),
                        value=comm_data.get('value', ''),
                        is_primary=True
                    )
                    session.add(comm)
        
        return company
    
    def get_invoice_with_details(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une facture avec tous ses détails
        
        Args:
            invoice_id: ID de la facture
            
        Returns:
            Dictionnaire avec tous les détails de la facture
        """
        with self.get_session() as session:
            try:
                # Charger la facture avec toutes les relations
                invoice = session.query(Invoice).options(
                    joinedload(Invoice.supplier),
                    joinedload(Invoice.customer),
                    joinedload(Invoice.lines),
                    joinedload(Invoice.taxes),
                    joinedload(Invoice.payments),
                    joinedload(Invoice.references),
                    joinedload(Invoice.signatures)
                ).filter_by(id=invoice_id).first()
                
                if not invoice:
                    return None
                
                # Construire le dictionnaire de retour
                result = {
                    'invoice': {
                        'id': invoice.id,
                        'invoice_number': invoice.invoice_number,
                        'document_type': invoice.document_type,
                        'issue_date': invoice.issue_date.isoformat() if invoice.issue_date else None,
                        'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                        'currency_code': invoice.currency_code,
                        'total_amount_excl_tax': float(invoice.total_amount_excl_tax),
                        'total_tax_amount': float(invoice.total_tax_amount),
                        'total_amount_incl_tax': float(invoice.total_amount_incl_tax),
                        'status': invoice.status,
                        'teif_version': invoice.teif_version
                    },
                    'supplier': {
                        'id': invoice.supplier.id,
                        'identifier': invoice.supplier.identifier,
                        'name': invoice.supplier.name,
                        'vat_number': invoice.supplier.vat_number,
                        'address': {
                            'street': invoice.supplier.address_street,
                            'city': invoice.supplier.address_city,
                            'postal_code': invoice.supplier.address_postal_code,
                            'country_code': invoice.supplier.address_country_code
                        }
                    },
                    'customer': {
                        'id': invoice.customer.id,
                        'identifier': invoice.customer.identifier,
                        'name': invoice.customer.name,
                        'vat_number': invoice.customer.vat_number,
                        'address': {
                            'street': invoice.customer.address_street,
                            'city': invoice.customer.address_city,
                            'postal_code': invoice.customer.address_postal_code,
                            'country_code': invoice.customer.address_country_code
                        }
                    },
                    'lines': [
                        {
                            'line_number': line.line_number,
                            'item_identifier': line.item_identifier,
                            'item_code': line.item_code,
                            'description': line.description,
                            'quantity': float(line.quantity),
                            'unit_code': line.unit_code,
                            'unit_price': float(line.unit_price),
                            'line_amount': float(line.line_amount),
                            'tax_rate': float(line.tax_rate) if line.tax_rate else 0,
                            'tax_amount': float(line.tax_amount) if line.tax_amount else 0
                        }
                        for line in invoice.lines
                    ],
                    'taxes': [
                        {
                            'tax_type_code': tax.tax_type_code,
                            'tax_category': tax.tax_category,
                            'tax_rate': float(tax.tax_rate),
                            'taxable_amount': float(tax.taxable_amount),
                            'tax_amount': float(tax.tax_amount)
                        }
                        for tax in invoice.taxes
                    ],
                    'payments': [
                        {
                            'payment_means_code': payment.payment_means_code,
                            'payment_id': payment.payment_id,
                            'due_date': payment.due_date.isoformat() if payment.due_date else None,
                            'account_iban': payment.account_iban,
                            'account_holder': payment.account_holder,
                            'bank_name': payment.bank_name
                        }
                        for payment in invoice.payments
                    ],
                    'references': [
                        {
                            'reference_type': ref.reference_type,
                            'reference_value': ref.reference_value,
                            'description': ref.description
                        }
                        for ref in invoice.references
                    ]
                }
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Erreur récupération facture {invoice_id}: {e}")
                return None
    
    def validate_teif_data(self, teif_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valide les données TEIF selon les spécifications 1.8.8
        
        Args:
            teif_data: Données à valider
            
        Returns:
            Dictionnaire avec les erreurs trouvées par section
        """
        errors = {
            'header': [],
            'seller': [],
            'buyer': [],
            'lines': [],
            'taxes': [],
            'totals': []
        }
        
        try:
            # Validation du header
            header = teif_data.get('header', {})
            if not header.get('sender_identifier'):
                errors['header'].append('sender_identifier manquant')
            
            # Validation du vendeur
            seller = teif_data.get('seller', {})
            if not seller.get('identifier'):
                errors['seller'].append('identifier manquant')
            if not seller.get('name'):
                errors['seller'].append('name manquant')
            if not seller.get('vat_number'):
                errors['seller'].append('vat_number manquant')
            
            # Validation de l'acheteur
            buyer = teif_data.get('buyer', {})
            if not buyer.get('identifier'):
                errors['buyer'].append('identifier manquant')
            if not buyer.get('name'):
                errors['buyer'].append('name manquant')
            
            # Validation des lignes
            lines = teif_data.get('lines', [])
            if not lines:
                errors['lines'].append('Aucune ligne de facture')
            else:
                for idx, line in enumerate(lines, 1):
                    if not line.get('description'):
                        errors['lines'].append(f'Ligne {idx}: description manquante')
                    if not line.get('quantity') or float(line.get('quantity', 0)) <= 0:
                        errors['lines'].append(f'Ligne {idx}: quantité invalide')
                    if not line.get('unit_price') or float(line.get('unit_price', 0)) < 0:
                        errors['lines'].append(f'Ligne {idx}: prix unitaire invalide')
            
            # Validation des totaux
            totals = teif_data.get('totals', {})
            if 'total_without_tax' not in totals:
                errors['totals'].append('total_without_tax manquant')
            if 'total_with_tax' not in totals:
                errors['totals'].append('total_with_tax manquant')
            
            # Supprimer les sections sans erreurs
            errors = {k: v for k, v in errors.items() if v}
            
        except Exception as e:
            errors['general'] = [f'Erreur de validation: {str(e)}']
        
        return errors
    
    def get_teif_reference_codes(self, code_type: str = None) -> List[Dict[str, Any]]:
        """
        Récupère les codes de référence TEIF
        
        Args:
            code_type: Type de code à filtrer (optionnel)
            
        Returns:
            Liste des codes de référence
        """
        with self.get_session() as session:
            try:
                query = session.query(TEIFReferenceCode)
                
                if code_type:
                    query = query.filter_by(code_type=code_type)
                
                codes = query.all()
                
                return [
                    {
                        'code_type': code.code_type,
                        'code_value': code.code_value,
                        'code_label': code.code_label,
                        'description': code.description,
                        'is_mandatory': code.is_mandatory
                    }
                    for code in codes
                ]
                
            except Exception as e:
                logger.error(f"❌ Erreur récupération codes TEIF: {e}")
                return []
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager pour obtenir une session SQL Server
        
        Usage:
            with db_manager.get_session() as session:
                # Utiliser la session
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur dans la session SQL Server: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Retourne une session directe (à fermer manuellement)"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Teste la connexion à SQL Server"""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT @@VERSION"))
                version = result.scalar()
                logger.info(f"✅ Connexion SQL Server réussie: {version[:50]}...")
                return True
        except Exception as e:
            logger.error(f"❌ Échec connexion SQL Server: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Retourne des informations détaillées sur la base SQL Server"""
        try:
            with self.get_session() as session:
                from .models import Company, Invoice, InvoiceLine, TEIFReferenceCode
                
                # Informations générales
                version_result = session.execute(text("SELECT @@VERSION"))
                version = version_result.scalar()
                
                db_name_result = session.execute(text("SELECT DB_NAME()"))
                db_name = db_name_result.scalar()
                
                # Statistiques des tables
                info = {
                    'database_type': 'SQL Server',
                    'database_name': db_name,
                    'server_version': version[:100] if version else 'Unknown',
                    'connection_url': self.database_url.split('@')[0] + '@***',
                    'tables_count': len(Base.metadata.tables),
                    'companies_count': session.query(Company).count(),
                    'invoices_count': session.query(Invoice).count(),
                    'invoice_lines_count': session.query(InvoiceLine).count(),
                    'reference_codes_count': session.query(TEIFReferenceCode).count(),
                }
                
                # Taille de la base de données
                try:
                    size_result = session.execute(text("""
                        SELECT 
                            SUM(size * 8.0 / 1024) as size_mb
                        FROM sys.master_files 
                        WHERE database_id = DB_ID()
                    """))
                    size_mb = size_result.scalar()
                    info['database_size_mb'] = round(size_mb, 2) if size_mb else 0
                except:
                    info['database_size_mb'] = 'N/A'
                
                # Statistiques des factures par statut
                try:
                    status_stats = session.execute(text("""
                        SELECT status, COUNT(*) as count 
                        FROM invoices 
                        GROUP BY status
                    """)).fetchall()
                    info['invoice_status_stats'] = {row[0]: row[1] for row in status_stats}
                except:
                    info['invoice_status_stats'] = {}
                
                return info
                
        except Exception as e:
            logger.error(f"Erreur récupération infos SQL Server: {e}")
            return {'error': str(e)}
    
    def drop_database(self):
        """Supprime toutes les tables (ATTENTION: perte de données!)"""
        try:
            logger.warning("⚠️ Suppression de toutes les tables SQL Server...")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("✅ Tables supprimées")
        except Exception as e:
            logger.error(f"❌ Erreur suppression: {e}")
            raise
    
    def recreate_database(self):
        """Recrée complètement la base de données"""
        self.drop_database()
        self.create_database()

# Instance globale du gestionnaire
db_manager = None

def get_database_manager() -> SQLServerDatabaseManager:
    """Retourne l'instance globale du gestionnaire SQL Server"""
    global db_manager
    if db_manager is None:
        db_manager = SQLServerDatabaseManager()
    return db_manager

def init_database():
    """Initialise la base de données SQL Server (point d'entrée principal)"""
    manager = get_database_manager()
    manager.create_database()
    return manager

def get_session() -> Session:
    """Raccourci pour obtenir une session SQL Server"""
    manager = get_database_manager()
    return manager.get_session_direct()

# Event listeners pour l'audit automatique
@event.listens_for(Base, 'before_insert', propagate=True)
def before_insert_listener(mapper, connection, target):
    """Listener pour l'audit avant insertion"""
    # Audit automatique si nécessaire
    pass

@event.listens_for(Base, 'before_update', propagate=True)
def before_update_listener(mapper, connection, target):
    """Listener pour l'audit avant mise à jour"""
    # Audit automatique si nécessaire
    pass
