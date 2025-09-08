-- Schema SQL Server corrigé - Création de la base de données TEIF complète
-- Ordre de création optimisé pour éviter les erreurs de dépendances

USE master;
GO

-- Créer la base de données si elle n'existe pas
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'TEIF_Complete_DB')
BEGIN
    CREATE DATABASE TEIF_Complete_DB;
END
GO

USE TEIF_Complete_DB;
GO

-- =====================================================
-- TABLE DES ENTREPRISES (VENDEURS ET ACHETEURS)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='companies' AND xtype='U')
CREATE TABLE companies (
    id INT IDENTITY(1,1) PRIMARY KEY,
    identifier NVARCHAR(50) UNIQUE NOT NULL, -- Ex: 1234567AAM001, 9876543BBM002
    name NVARCHAR(255) NOT NULL,
    vat_number NVARCHAR(50) NOT NULL, -- Numéro TVA obligatoire
    tax_id NVARCHAR(50), -- Matricule fiscal pour les références
    commercial_register NVARCHAR(50), -- Registre de commerce
    
    -- Adresse complète
    address_street NVARCHAR(500),
    address_city NVARCHAR(100),
    address_postal_code NVARCHAR(20),
    address_country_code NVARCHAR(3) DEFAULT 'TN',
    address_language NVARCHAR(2) DEFAULT 'FR', -- lang field from address
    
    -- Contacts de base
    phone NVARCHAR(50),
    email NVARCHAR(255),
    fax NVARCHAR(50),
    website NVARCHAR(255),
    
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- =====================================================
-- RÉFÉRENCES DES ENTREPRISES (I-815, I-01, I-1602)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='company_references' AND xtype='U')
CREATE TABLE company_references (
    id INT IDENTITY(1,1) PRIMARY KEY,
    company_id INT NOT NULL,
    reference_type NVARCHAR(10) NOT NULL, -- I-815 (Registre), I-01 (Matricule), I-1602 (TVA)
    reference_value NVARCHAR(100) NOT NULL,
    description NVARCHAR(255),
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- CONTACTS DES ENTREPRISES
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='company_contacts' AND xtype='U')
CREATE TABLE company_contacts (
    id INT IDENTITY(1,1) PRIMARY KEY,
    company_id INT NOT NULL,
    function_code NVARCHAR(10), -- I-94
    contact_name NVARCHAR(255), -- Ex: "Service Commercial", "Service Achat"
    contact_identifier NVARCHAR(50), -- Ex: "COMM", "ACHAT"
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- COMMUNICATIONS DES CONTACTS (TÉLÉPHONE, EMAIL, FAX)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='contact_communications' AND xtype='U')
CREATE TABLE contact_communications (
    id INT IDENTITY(1,1) PRIMARY KEY,
    contact_id INT NOT NULL,
    communication_type NVARCHAR(10) NOT NULL, -- I-101 (tel), I-102 (email), I-104 (fax)
    communication_value NVARCHAR(255) NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (contact_id) REFERENCES company_contacts(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- TABLE PRINCIPALE DES FACTURES
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoices' AND xtype='U')
CREATE TABLE invoices (
    id INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Version et agence de contrôle
    teif_version NVARCHAR(10) DEFAULT '1.8.8',
    controlling_agency NVARCHAR(10) DEFAULT 'TTN',
    
    -- En-tête de message (header)
    sender_identifier NVARCHAR(50) NOT NULL, -- Ex: 0736202XAM000
    receiver_identifier NVARCHAR(50) NOT NULL, -- Ex: 0914089JAM000
    message_identifier NVARCHAR(100), -- TTN ID généré
    message_datetime DATETIME2 DEFAULT GETDATE(),
    
    -- BGM Section (Beginning of Message)
    document_number NVARCHAR(100) NOT NULL, -- Ex: FACT-2023-001
    document_type NVARCHAR(10) DEFAULT 'I-11', -- Type de document
    document_type_label NVARCHAR(100) DEFAULT 'Facture',
    
    -- Informations de base
    invoice_date DATE NOT NULL,
    due_date DATE,
    period_start_date DATE,
    period_end_date DATE,
    
    -- Partenaires commerciaux
    supplier_id INT NOT NULL, -- seller
    customer_id INT NOT NULL, -- buyer
    
    -- Devise
    currency NVARCHAR(3) DEFAULT 'TND',
    currency_code_list NVARCHAR(20) DEFAULT 'ISO_4217',
    
    -- Totaux calculés (section totals)
    capital_amount DECIMAL(15,3) DEFAULT 0, -- I-179
    total_with_tax DECIMAL(15,3) DEFAULT 0, -- I-180
    total_without_tax DECIMAL(15,3) DEFAULT 0, -- I-176
    tax_base_amount DECIMAL(15,3) DEFAULT 0, -- I-182
    tax_amount DECIMAL(15,3) DEFAULT 0, -- I-181
    
    -- Statut et traçabilité
    status NVARCHAR(50) DEFAULT 'draft',
    pdf_path NVARCHAR(500),
    xml_path NVARCHAR(500),
    ttn_validation_ref NVARCHAR(100),
    
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (supplier_id) REFERENCES companies(id),
    FOREIGN KEY (customer_id) REFERENCES companies(id)
);
GO

-- =====================================================
-- DATES DE LA FACTURE (DTM SECTION)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoice_dates' AND xtype='U')
CREATE TABLE invoice_dates (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    date_text NVARCHAR(50) NOT NULL, -- Format ddMMyy ou ddMMyy-ddMMyy
    function_code NVARCHAR(10) NOT NULL, -- I-31 (facture), I-32 (échéance), I-36 (période)
    date_format NVARCHAR(20) NOT NULL, -- ddMMyy, ddMMyy-ddMMyy
    description NVARCHAR(255),
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- LIGNES DE FACTURE PRINCIPALES
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoice_lines' AND xtype='U')
CREATE TABLE invoice_lines (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    line_number INT NOT NULL,
    parent_line_id INT NULL, -- Pour les sous-lignes (sub_lines)
    
    -- Identification de l'article
    item_identifier NVARCHAR(100), -- Ex: DDM-001, DDR-001, KIT-001
    item_code NVARCHAR(100), -- Même que item_identifier dans les exemples
    description NVARCHAR(1000) NOT NULL, -- Description détaillée
    
    -- Quantité et prix
    quantity DECIMAL(10,3) NOT NULL,
    unit NVARCHAR(10) DEFAULT 'PCE', -- PCE, KIT, etc.
    unit_price DECIMAL(15,3) NOT NULL,
    
    -- Montants
    line_total_ht DECIMAL(15,3) NOT NULL, -- Calculé : quantity * unit_price
    discount_amount DECIMAL(15,3) DEFAULT 0,
    discount_reason NVARCHAR(255), -- Ex: "Remise spéciale de 10%"
    
    -- Devise
    currency NVARCHAR(3) DEFAULT 'TND',
    currency_code_list NVARCHAR(20) DEFAULT 'ISO_4217',
    
    -- Métadonnées
    line_date DATE,
    
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_line_id) REFERENCES invoice_lines(id)
);
GO

-- =====================================================
-- TAXES DES LIGNES
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='line_taxes' AND xtype='U')
CREATE TABLE line_taxes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    line_id INT NOT NULL,
    tax_code NVARCHAR(10) NOT NULL, -- I-1602 (TVA), I-1601 (Timbre)
    tax_type NVARCHAR(50) NOT NULL, -- TVA, Droit de timbre
    tax_category NVARCHAR(10), -- S, E, Z
    tax_rate DECIMAL(5,2) NOT NULL, -- Ex: 19.0 pour 19%
    taxable_amount DECIMAL(15,3) NOT NULL, -- Montant sur lequel s'applique la taxe
    tax_amount DECIMAL(15,3) NOT NULL, -- Montant de la taxe calculée
    currency_code_list NVARCHAR(20) DEFAULT 'ISO_4217',
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (line_id) REFERENCES invoice_lines(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- MONTANTS MONÉTAIRES DE LA FACTURE (MOA SECTION)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoice_monetary_amounts' AND xtype='U')
CREATE TABLE invoice_monetary_amounts (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount_type_code NVARCHAR(10) NOT NULL, -- I-181, I-182, I-183
    amount DECIMAL(15,3) NOT NULL,
    description NVARCHAR(255), -- Ex: "Total hors taxes", "Total des taxes", "Total toutes taxes comprises"
    currency NVARCHAR(3) DEFAULT 'TND',
    currency_code_list NVARCHAR(20) DEFAULT 'ISO_4217',
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- TAXES GLOBALES DE LA FACTURE
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoice_taxes' AND xtype='U')
CREATE TABLE invoice_taxes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    tax_code NVARCHAR(10) NOT NULL, -- I-1602, I-1601
    tax_type NVARCHAR(50) NOT NULL, -- TVA, Droit de timbre
    tax_category NVARCHAR(10), -- S, E, Z
    tax_rate DECIMAL(5,2) NOT NULL,
    taxable_amount DECIMAL(15,3) NOT NULL,
    tax_amount DECIMAL(15,3) NOT NULL,
    currency_code_list NVARCHAR(20) DEFAULT 'ISO_4217',
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- CONDITIONS DE PAIEMENT
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='payment_terms' AND xtype='U')
CREATE TABLE payment_terms (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    payment_terms_code NVARCHAR(10), -- I-10
    description NVARCHAR(500), -- Ex: "Paiement à 30 jours fin de mois"
    discount_percent DECIMAL(5,2), -- Ex: 2.0 pour 2%
    discount_due_date DATE,
    payment_due_date DATE,
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- MOYENS DE PAIEMENT
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='payment_means' AND xtype='U')
CREATE TABLE payment_means (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    payment_means_code NVARCHAR(10), -- I-30
    payment_id NVARCHAR(100), -- Ex: VIR-2023-001
    due_date DATE,
    
    -- Compte financier du bénéficiaire (payee_financial_account)
    iban NVARCHAR(50), -- Ex: TN5904018104003691234567
    account_holder NVARCHAR(255), -- Ex: NOM_DU_TITULAIRE
    financial_institution NVARCHAR(255), -- Ex: BNA
    branch_code NVARCHAR(50), -- Ex: AGENCE_123
    
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- RÉFÉRENCES ADDITIONNELLES
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoice_references' AND xtype='U')
CREATE TABLE invoice_references (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    reference_type NVARCHAR(10) NOT NULL, -- ON, ABO, etc.
    reference_value NVARCHAR(100) NOT NULL, -- Ex: CMD-2023-456, ABO-2023-789
    description NVARCHAR(255),
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- DOCUMENTS ADDITIONNELS
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='additional_documents' AND xtype='U')
CREATE TABLE additional_documents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    document_id NVARCHAR(100) NOT NULL, -- Ex: DOC-001
    document_type NVARCHAR(10), -- I-201
    document_name NVARCHAR(255), -- Ex: "Facture proforma"
    document_date DATE, -- Format YYYYMMDD converti
    description NVARCHAR(500), -- Ex: "Facture proforma envoyée le 5 jours avant"
    file_path NVARCHAR(500),
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- CONDITIONS SPÉCIALES
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='special_conditions' AND xtype='U')
CREATE TABLE special_conditions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    condition_text NVARCHAR(MAX) NOT NULL,
    language_code NVARCHAR(2) DEFAULT 'fr', -- Peut être spécifié dans l'objet
    sequence_number INT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- SIGNATURES ÉLECTRONIQUES
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoice_signatures' AND xtype='U')
CREATE TABLE invoice_signatures (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    signature_id NVARCHAR(50) NOT NULL,
    signer_role NVARCHAR(50), -- Ex: "Fournisseur"
    signer_name NVARCHAR(255), -- Ex: "Fournisseur Test"
    
    -- Données cryptographiques
    x509_certificate NVARCHAR(MAX), -- Certificat X.509 en base64
    private_key_data NVARCHAR(MAX), -- Clé privée (pour test uniquement)
    key_password NVARCHAR(255), -- Mot de passe de la clé
    
    -- Métadonnées de signature
    signing_time DATETIME2, -- Date de signature ISO format
    signature_value NVARCHAR(MAX), -- Valeur de la signature calculée
    
    -- Statut
    signature_status NVARCHAR(50) DEFAULT 'pending', -- pending, signed, verified, invalid
    verification_date DATETIME2,
    verification_result NVARCHAR(MAX),
    
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- FICHIERS XML GÉNÉRÉS
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='generated_xml_files' AND xtype='U')
CREATE TABLE generated_xml_files (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    xml_content NVARCHAR(MAX) NOT NULL,
    file_path NVARCHAR(500),
    file_size BIGINT,
    xml_version NVARCHAR(10) DEFAULT '1.8.8',
    validation_status NVARCHAR(50) DEFAULT 'pending',
    validation_errors NVARCHAR(MAX),
    schema_validation BIT DEFAULT 0,
    signature_validation BIT DEFAULT 0,
    generated_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
GO

-- =====================================================
-- INDEX POUR AMÉLIORER LES PERFORMANCES
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_companies_identifier')
    CREATE INDEX IX_companies_identifier ON companies(identifier);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_companies_vat_number')
    CREATE INDEX IX_companies_vat_number ON companies(vat_number);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_document_number')
    CREATE INDEX IX_invoices_document_number ON invoices(document_number);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_invoice_date')
    CREATE INDEX IX_invoices_invoice_date ON invoices(invoice_date);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_supplier')
    CREATE INDEX IX_invoices_supplier ON invoices(supplier_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_customer')
    CREATE INDEX IX_invoices_customer ON invoices(customer_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_status')
    CREATE INDEX IX_invoices_status ON invoices(status);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoice_lines_invoice')
    CREATE INDEX IX_invoice_lines_invoice ON invoice_lines(invoice_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoice_lines_parent')
    CREATE INDEX IX_invoice_lines_parent ON invoice_lines(parent_line_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_line_taxes_line')
    CREATE INDEX IX_line_taxes_line ON line_taxes(line_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoice_taxes_invoice')
    CREATE INDEX IX_invoice_taxes_invoice ON invoice_taxes(invoice_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_signatures_invoice')
    CREATE INDEX IX_signatures_invoice ON invoice_signatures(invoice_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_signatures_status')
    CREATE INDEX IX_signatures_status ON invoice_signatures(signature_status);
GO

-- =====================================================
-- PROCÉDURES STOCKÉES
-- =====================================================

-- Calculer les totaux d'une facture selon la structure TEIF
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_calculate_invoice_totals_teif')
    DROP PROCEDURE sp_calculate_invoice_totals_teif;
GO

CREATE PROCEDURE sp_calculate_invoice_totals_teif
    @invoice_id INT
AS
BEGIN
    DECLARE @total_without_tax DECIMAL(15,3) = 0;
    DECLARE @tax_amount DECIMAL(15,3) = 0;
    DECLARE @total_with_tax DECIMAL(15,3) = 0;
    DECLARE @tax_base DECIMAL(15,3) = 0;
    
    -- Calculer les totaux à partir des lignes
    SELECT 
        @total_without_tax = SUM(il.line_total_ht - ISNULL(il.discount_amount, 0)),
        @tax_amount = SUM(ISNULL(lt.tax_amount, 0)),
        @tax_base = SUM(ISNULL(lt.taxable_amount, 0))
    FROM invoice_lines il
    LEFT JOIN line_taxes lt ON il.id = lt.line_id
    WHERE il.invoice_id = @invoice_id;
    
    SET @total_with_tax = @total_without_tax + @tax_amount;
    
    -- Mettre à jour la facture avec la structure totals
    UPDATE invoices 
    SET 
        total_without_tax = ISNULL(@total_without_tax, 0), -- I-176
        tax_amount = ISNULL(@tax_amount, 0), -- I-181
        tax_base_amount = ISNULL(@tax_base, 0), -- I-182
        total_with_tax = ISNULL(@total_with_tax, 0), -- I-180
        updated_at = GETDATE()
    WHERE id = @invoice_id;
    
    -- Mettre à jour ou insérer les montants monétaires (invoice_moa)
    MERGE invoice_monetary_amounts AS target
    USING (
        SELECT @invoice_id as invoice_id, 'I-181' as amount_type_code, @total_without_tax as amount, 'Total hors taxes' as description
        UNION ALL
        SELECT @invoice_id, 'I-182', @tax_amount, 'Total des taxes'
        UNION ALL
        SELECT @invoice_id, 'I-183', @total_with_tax, 'Total toutes taxes comprises'
    ) AS source ON target.invoice_id = source.invoice_id AND target.amount_type_code = source.amount_type_code
    WHEN MATCHED THEN
        UPDATE SET amount = source.amount, description = source.description
    WHEN NOT MATCHED THEN
        INSERT (invoice_id, amount_type_code, amount, description)
        VALUES (source.invoice_id, source.amount_type_code, source.amount, source.description);
END;
GO

-- =====================================================
-- VUES POUR FACILITER LES REQUÊTES
-- =====================================================

-- Vue complète des factures avec structure TEIF
IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_teif_invoice_complete')
    DROP VIEW v_teif_invoice_complete;
GO

CREATE VIEW v_teif_invoice_complete AS
SELECT 
    i.id,
    i.teif_version,
    i.controlling_agency,
    i.document_number,
    i.document_type,
    i.document_type_label,
    i.invoice_date,
    i.due_date,
    i.currency,
    i.sender_identifier,
    i.receiver_identifier,
    
    -- Totaux selon structure TEIF
    i.total_without_tax, -- I-176
    i.tax_amount, -- I-181
    i.tax_base_amount, -- I-182
    i.total_with_tax, -- I-180
    i.capital_amount, -- I-179
    
    i.status,
    
    -- Fournisseur (seller)
    s.name as seller_name,
    s.identifier as seller_identifier,
    s.vat_number as seller_vat,
    s.address_city as seller_city,
    
    -- Client (buyer)
    c.name as buyer_name,
    c.identifier as buyer_identifier,
    c.vat_number as buyer_vat,
    c.address_city as buyer_city,
    
    i.created_at,
    i.updated_at
FROM invoices i
JOIN companies s ON i.supplier_id = s.id
JOIN companies c ON i.customer_id = c.id;
GO

-- Vue des lignes avec sous-lignes et taxes
IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_teif_invoice_lines_complete')
    DROP VIEW v_teif_invoice_lines_complete;
GO

CREATE VIEW v_teif_invoice_lines_complete AS
SELECT 
    il.id,
    il.invoice_id,
    il.line_number,
    il.parent_line_id,
    CASE WHEN il.parent_line_id IS NULL THEN 'MAIN' ELSE 'SUB' END as line_type,
    il.item_identifier,
    il.item_code,
    il.description,
    il.quantity,
    il.unit,
    il.unit_price,
    il.line_total_ht,
    il.discount_amount,
    il.discount_reason,
    il.currency,
    
    -- Total ligne TTC
    (il.line_total_ht - ISNULL(il.discount_amount, 0)) as line_total_ttc
FROM invoice_lines il;
GO

-- =====================================================
-- TRIGGERS POUR MISE À JOUR AUTOMATIQUE
-- =====================================================
IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'tr_companies_updated_at')
    DROP TRIGGER tr_companies_updated_at;
GO

CREATE TRIGGER tr_companies_updated_at
ON companies
AFTER UPDATE
AS
BEGIN
    UPDATE companies 
    SET updated_at = GETDATE()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'tr_invoices_updated_at')
    DROP TRIGGER tr_invoices_updated_at;
GO

CREATE TRIGGER tr_invoices_updated_at
ON invoices
AFTER UPDATE
AS
BEGIN
    UPDATE invoices 
    SET updated_at = GETDATE()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- =====================================================
-- DONNÉES DE TEST BASÉES SUR LE GÉNÉRATEUR
-- =====================================================

-- Vérifier si les données existent déjà
IF NOT EXISTS (SELECT * FROM companies WHERE identifier = '1234567AAM001')
BEGIN
    -- Insérer les entreprises de test exactement comme dans le générateur
    INSERT INTO companies (identifier, name, vat_number, tax_id, address_street, address_city, address_postal_code, address_country_code, address_language, phone, email) VALUES
    ('1234567AAM001', 'SOCIETE FOURNISSEUR SARL', '12345678', '1234567AAM001', 'AVENUE HABIB BOURGUIBA', 'TUNIS', '1000', 'TN', 'FR', '+216 70 000 000', 'commercial@fournisseur.tn'),
    ('9876543BBM002', 'SOCIETE CLIENTE SARL', '87654321', '9876543BBM002', 'AVENUE MOHAMED V', 'SOUSSE', '4000', 'TN', 'FR', '+216 71 000 001', 'achat@client.tn');
    
    -- Insérer les références exactement comme dans le générateur
    DECLARE @supplier_id INT, @customer_id INT;
    SELECT @supplier_id = id FROM companies WHERE identifier = '1234567AAM001';
    SELECT @customer_id = id FROM companies WHERE identifier = '9876543BBM002';
    
    INSERT INTO company_references (company_id, reference_type, reference_value, description) VALUES
    (@supplier_id, 'I-815', 'B1234567', 'Registre de commerce'),
    (@supplier_id, 'I-01', '12345678', 'Matricule fiscal'),
    (@supplier_id, 'I-1602', '12345678', 'Numéro TVA'),
    (@customer_id, 'I-815', 'B9876543', 'Registre de commerce'),
    (@customer_id, 'I-01', '87654321', 'Matricule fiscal'),
    (@customer_id, 'I-1602', '87654321', 'Numéro TVA');
    
    -- Insérer les contacts
    INSERT INTO company_contacts (company_id, function_code, contact_name, contact_identifier) VALUES
    (@supplier_id, 'I-94', 'Service Commercial', 'COMM'),
    (@customer_id, 'I-94', 'Service Achat', 'ACHAT');
    
    -- Insérer les communications des contacts
    DECLARE @contact_supplier_id INT, @contact_customer_id INT;
    SELECT @contact_supplier_id = id FROM company_contacts WHERE company_id = @supplier_id;
    SELECT @contact_customer_id = id FROM company_contacts WHERE company_id = @customer_id;
    
    INSERT INTO contact_communications (contact_id, communication_type, communication_value) VALUES
    (@contact_supplier_id, 'I-101', '+216 70 000 000'),
    (@contact_supplier_id, 'I-102', 'commercial@fournisseur.tn'),
    (@contact_customer_id, 'I-101', '+216 71 000 001'),
    (@contact_customer_id, 'I-104', 'achat@client.tn');
END;
GO

PRINT 'Schema TEIF complet créé avec succès !';
PRINT 'Base de données: TEIF_Complete_DB';
DECLARE @table_count INT, @view_count INT;
SELECT @table_count = COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';
SELECT @view_count = COUNT(*) FROM INFORMATION_SCHEMA.VIEWS;
PRINT 'Tables créées: ' + CAST(@table_count AS NVARCHAR(10));
PRINT 'Vues créées: ' + CAST(@view_count AS NVARCHAR(10));
PRINT 'Données de test insérées basées sur le générateur TEIF';
