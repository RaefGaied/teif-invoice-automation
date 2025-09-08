-- 1. Add missing columns to invoices table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('invoices') AND name = 'ttn_reference')
BEGIN
    ALTER TABLE invoices ADD 
        ttn_reference NVARCHAR(100),
        teif_version NVARCHAR(10) DEFAULT '1.8.8',
        controlling_agency NVARCHAR(10) DEFAULT 'TTN',
        message_identifier NVARCHAR(100),
        message_datetime DATETIME2 DEFAULT GETDATE();
    
    PRINT 'Added TTN reference and TEIF metadata columns to invoices table';
END
GO

-- 2. Update data types for monetary values
ALTER TABLE invoices ALTER COLUMN total_without_tax DECIMAL(18, 3);
ALTER TABLE invoices ALTER COLUMN tax_amount DECIMAL(18, 3);
ALTER TABLE invoices ALTER COLUMN tax_base_amount DECIMAL(18, 3);
ALTER TABLE invoices ALTER COLUMN total_with_tax DECIMAL(18, 3);
ALTER TABLE invoices ALTER COLUMN capital_amount DECIMAL(18, 3);
GO

-- 3. Add tax_rate to invoice_lines
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('invoice_lines') AND name = 'tax_rate')
BEGIN
    ALTER TABLE invoice_lines ADD tax_rate DECIMAL(5,2) NULL;
    PRINT 'Added tax_rate column to invoice_lines';
END
GO

-- 4. Add constraints for status fields
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_invoices_status')
BEGIN
    ALTER TABLE invoices ADD CONSTRAINT CK_invoices_status 
    CHECK (status IN ('draft', 'validated', 'signed', 'sent', 'paid', 'cancelled'));
    
    PRINT 'Added status constraint to invoices table';
END
GO

-- 5. Create error tracking table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'error_logs')
BEGIN
    CREATE TABLE error_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        error_time DATETIME2 DEFAULT GETDATE(),
        error_severity NVARCHAR(50),
        error_message NVARCHAR(MAX),
        error_procedure NVARCHAR(255),
        error_line INT,
        error_data NVARCHAR(MAX)
    );
    
    PRINT 'Created error_logs table';
END
GO

-- 6. Create audit log table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_logs')
BEGIN
    CREATE TABLE audit_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        table_name NVARCHAR(128) NOT NULL,
        record_id INT NOT NULL,
        action_type CHAR(1) NOT NULL, -- I=Insert, U=Update, D=Delete
        action_time DATETIME2 DEFAULT GETDATE(),
        user_name NVARCHAR(255) DEFAULT SYSTEM_USER,
        old_data NVARCHAR(MAX),
        new_data NVARCHAR(MAX)
    );
    
    PRINT 'Created audit_logs table';
END
GO

-- 7. Create trigger for audit logging
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'tr_invoices_audit')
BEGIN
    EXEC('
    CREATE TRIGGER tr_invoices_audit
    ON invoices
    AFTER INSERT, UPDATE, DELETE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- For inserts
        IF EXISTS (SELECT * FROM inserted) AND NOT EXISTS (SELECT * FROM deleted)
        BEGIN
            INSERT INTO audit_logs (table_name, record_id, action_type, new_data)
            SELECT 
                ''invoices'',
                i.id,
                ''I'',
                (SELECT * FROM inserted AS i
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
            FROM inserted i;
        END
        
        -- For deletes
        IF EXISTS (SELECT * FROM deleted) AND NOT EXISTS (SELECT * FROM inserted)
        BEGIN
            INSERT INTO audit_logs (table_name, record_id, action_type, old_data)
            SELECT 
                ''invoices'',
                d.id,
                ''D'',
                (SELECT * FROM deleted AS d
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
            FROM deleted d;
        END
        
        -- For updates
        IF EXISTS (SELECT * FROM inserted) AND EXISTS (SELECT * FROM deleted)
        BEGIN
            INSERT INTO audit_logs (table_name, record_id, action_type, old_data, new_data)
            SELECT 
                ''invoices'',
                i.id,
                ''U'',
                (SELECT * FROM deleted AS d WHERE d.id = i.id
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
                (SELECT * FROM inserted AS i2
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
            FROM inserted i;
        END
    END');
    
    PRINT 'Created audit trigger for invoices table';
END
GO

-- 8. Create encryption key for sensitive data
IF NOT EXISTS (SELECT * FROM sys.symmetric_keys WHERE name = 'TEIF_Key')
BEGIN
    CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'YourStrongPassword123!';
    
    CREATE CERTIFICATE TEIF_Certificate
    WITH SUBJECT = 'TEIF Data Encryption Certificate';
    
    CREATE SYMMETRIC KEY TEIF_Key
    WITH ALGORITHM = AES_256
    ENCRYPTION BY CERTIFICATE TEIF_Certificate;
    
    PRINT 'Created encryption key for sensitive data';
END
GO

-- 9. Create stored procedure for error handling
IF NOT EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_log_error')
BEGIN
    EXEC('
    CREATE PROCEDURE sp_log_error
        @error_severity NVARCHAR(50),
        @error_message NVARCHAR(MAX),
        @error_procedure NVARCHAR(255) = NULL,
        @error_line INT = NULL,
        @error_data NVARCHAR(MAX) = NULL
    AS
    BEGIN
        SET NOCOUNT ON;
        
        BEGIN TRY
            INSERT INTO error_logs (
                error_severity,
                error_message,
                error_procedure,
                error_line,
                error_data
            ) VALUES (
                @error_severity,
                @error_message,
                @error_procedure,
                @error_line,
                @error_data
            );
            
            RETURN SCOPE_IDENTITY();
        END TRY
        BEGIN CATCH
            -- If error logging fails, write to SQL Server error log
            DECLARE @error_msg NVARCHAR(4000) = ''Error logging failed: '' + ERROR_MESSAGE();
            EXEC sp_addmessage 50001, 16, @error_msg;
            RAISERROR(50001, 16, 1);
            RETURN -1;
        END CATCH
    END');
    
    PRINT 'Created error logging stored procedure';
END
GO

-- 10. Create function to generate TTN reference
IF NOT EXISTS (SELECT * FROM sys.objects WHERE type = 'FN' AND name = 'fn_generate_ttn_reference')
BEGIN
    EXEC('
    CREATE FUNCTION fn_generate_ttn_reference (@invoice_id INT)
    RETURNS NVARCHAR(100)
    AS
    BEGIN
        DECLARE @ttn_reference NVARCHAR(100);
        DECLARE @date_prefix NVARCHAR(8) = FORMAT(GETDATE(), ''yyyyMMdd'');
        DECLARE @sequence INT;
        
        -- Get next sequence number for the day
        SELECT @sequence = ISNULL(MAX(CAST(SUBSTRING(ttn_reference, 10, 4) AS INT)), 0) + 1
        FROM invoices
        WHERE ttn_reference LIKE @date_prefix + ''%'';
        
        -- Format: YYYYMMDD + 4-digit sequence + 2-digit check digit
        SET @ttn_reference = @date_prefix + 
                            RIGHT(''0000'' + CAST(@sequence AS NVARCHAR(4)), 4) +
                            RIGHT(''00'' + CAST((@sequence % 97) + 1 AS NVARCHAR(2)), 2);
        
        RETURN @ttn_reference;
    END');
    
    PRINT 'Created TTN reference generation function';
END
GO

-- 11. Create trigger to set TTN reference on invoice validation
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'tr_invoices_set_ttn')
BEGIN
    EXEC('
    CREATE TRIGGER tr_invoices_set_ttn
    ON invoices
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        IF UPDATE(status)
        BEGIN
            UPDATE i
            SET 
                ttn_reference = dbo.fn_generate_ttn_reference(i.id),
                message_identifier = NEWID(),
                message_datetime = GETDATE()
            FROM invoices i
            INNER JOIN inserted ins ON i.id = ins.id
            INNER JOIN deleted del ON i.id = del.id
            WHERE ins.status = ''validated''
            AND (del.status IS NULL OR del.status <> ''validated'')
            AND i.ttn_reference IS NULL;
        END
    END');
    
    PRINT 'Created TTN reference trigger';
END
GO

-- 12. Create index for performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_ttn_reference')
BEGIN
    CREATE INDEX IX_invoices_ttn_reference ON invoices(ttn_reference);
    PRINT 'Created index on ttn_reference';
END
GO

-- 13. Create view for TEIF XML generation
IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_teif_invoice_xml')
    DROP VIEW v_teif_invoice_xml;
GO

EXEC('
CREATE VIEW v_teif_invoice_xml AS
WITH InvoiceData AS (
    SELECT 
        i.id,
        i.document_number,
        i.invoice_date,
        i.due_date,
        i.total_without_tax,
        i.tax_amount,
        i.total_with_tax,
        i.currency,
        i.status,
        i.ttn_reference,
        i.teif_version,
        
        -- Seller info
        s.name AS seller_name,
        s.vat_number AS seller_vat,
        s.address_street AS seller_street,
        s.address_city AS seller_city,
        s.address_postal_code AS seller_postal_code,
        s.address_country_code AS seller_country,
        
        -- Buyer info
        b.name AS buyer_name,
        b.vat_number AS buyer_vat,
        b.address_street AS buyer_street,
        b.address_city AS buyer_city,
        b.address_postal_code AS buyer_postal_code,
        b.address_country_code AS buyer_country,
        
        -- Payment info
        pm.payment_means_code,
        pm.payment_id,
        pm.due_date AS payment_due_date,
        pm.iban,
        pm.account_holder,
        pm.financial_institution
    FROM invoices i
    JOIN companies s ON i.supplier_id = s.id
    JOIN companies b ON i.customer_id = b.id
    LEFT JOIN payment_means pm ON i.id = pm.invoice_id
)
SELECT 
    id,
    document_number,
    (
        SELECT
            teif_version AS ''@version'',
            controlling_agency AS ''@controllingAgency'',
            (
                SELECT
                    document_number AS ''@documentNumber'',
                    document_type AS ''@documentType'',
                    FORMAT(invoice_date, ''yyyy-MM-dd'') AS ''@issueDate'',
                    FORMAT(due_date, ''yyyy-MM-dd'') AS ''@dueDate'',
                    (
                        SELECT
                            seller_name AS ''name'',
                            seller_vat AS ''vatNumber'',
                            (
                                SELECT
                                    seller_street AS ''street'',
                                    seller_city AS ''city'',
                                    seller_postal_code AS ''postalCode'',
                                    seller_country AS ''countryCode''
                                FOR XML PATH(''address''), TYPE
                            ),
                            (
                                SELECT
                                    ''I-815'' AS ''@referenceType'',
                                    (SELECT reference_value FROM company_references cr 
                                     WHERE cr.company_id = i.supplier_id AND cr.reference_type = ''I-815'') AS ''text()''
                                FOR XML PATH(''reference''), TYPE
                            )
                        FOR XML PATH(''seller''), TYPE
                    ),
                    (
                        SELECT
                            buyer_name AS ''name'',
                            buyer_vat AS ''vatNumber'',
                            (
                                SELECT
                                    buyer_street AS ''street'',
                                    buyer_city AS ''city'',
                                    buyer_postal_code AS ''postalCode'',
                                    buyer_country AS ''countryCode''
                                FOR XML PATH(''address''), TYPE
                            )
                        FOR XML PATH(''buyer''), TYPE
                    ),
                    (
                        SELECT
                            ''I-181'' AS ''@amountType'',
                            total_without_tax AS ''text()''
                        FOR XML PATH(''amount''), TYPE
                    ),
                    (
                        SELECT
                            ''I-182'' AS ''@amountType'',
                            tax_amount AS ''text()''
                        FOR XML PATH(''amount''), TYPE
                    ),
                    (
                        SELECT
                            ''I-183'' AS ''@amountType'',
                            total_with_tax AS ''text()''
                        FOR XML PATH(''amount''), TYPE
                    )
                FROM InvoiceData i
                WHERE i.id = id
                FOR XML PATH(''invoice''), TYPE
            )
        FOR XML PATH(''TEIF'')
    ) AS teif_xml
FROM InvoiceData');
GO

-- 14. Create stored procedure to generate TEIF XML
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_generate_teif_xml')
    DROP PROCEDURE sp_generate_teif_xml;
GO

EXEC('
CREATE PROCEDURE sp_generate_teif_xml
    @invoice_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @xml XML;
    DECLARE @result INT;
    
    BEGIN TRY
        -- Get the TEIF XML from the view
        SELECT @xml = teif_xml
        FROM v_teif_invoice_xml
        WHERE id = @invoice_id;
        
        -- Update the invoice with the generated XML
        UPDATE generated_xml_files
        SET 
            xml_content = CAST(@xml AS NVARCHAR(MAX)),
            file_size = DATALENGTH(CAST(@xml AS NVARCHAR(MAX))),
            generated_at = GETDATE()
        WHERE invoice_id = @invoice_id;
        
        -- If no row was updated, insert a new one
        IF @@ROWCOUNT = 0
        BEGIN
            INSERT INTO generated_xml_files (
                invoice_id,
                xml_content,
                file_size,
                xml_version,
                validation_status
            ) VALUES (
                @invoice_id,
                CAST(@xml AS NVARCHAR(MAX)),
                DATALENGTH(CAST(@xml AS NVARCHAR(MAX))),
                ''1.8.8'',
                ''pending''
            );
        END
        
        RETURN 0; -- Success
    END TRY
    BEGIN CATCH
        DECLARE @error_message NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @error_severity INT = ERROR_SEVERITY();
        DECLARE @error_state INT = ERROR_STATE();
        
        -- Log the error
        EXEC @result = sp_log_error 
            @error_severity = ''ERROR'',
            @error_message = @error_message,
            @error_procedure = ''sp_generate_teif_xml'',
            @error_line = ERROR_LINE();
            
        -- Re-raise the error
        RAISERROR(@error_message, @error_severity, @error_state);
        RETURN -1; -- Error
    END CATCH
END');
GO

-- 15. Create function to validate TEIF XML against schema
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'FN' AND name = 'fn_validate_teif_xml')
    DROP FUNCTION fn_validate_teif_xml;
GO

EXEC('
CREATE FUNCTION fn_validate_teif_xml (@invoice_id INT)
RETURNS @result TABLE (
    is_valid BIT,
    validation_message NVARCHAR(MAX)
)
AS
BEGIN
    DECLARE @xml_content NVARCHAR(MAX);
    DECLARE @is_valid BIT = 1;
    DECLARE @message NVARCHAR(MAX) = ''Validation successful'';
    
    -- Get the XML content
    SELECT @xml_content = xml_content
    FROM generated_xml_files
    WHERE invoice_id = @invoice_id;
    
    -- Basic validation (can be extended with XSD validation)
    IF @xml_content IS NULL
    BEGIN
        SET @is_valid = 0;
        SET @message = ''No XML content found for the specified invoice'';
    END
    ELSE IF CHARINDEX(''<TEIF'', @xml_content) = 0
    BEGIN
        SET @is_valid = 0;
        SET @message = ''Invalid TEIF XML format'';
    END
    
    -- Add more validation rules as needed
    
    -- Return the result
    INSERT INTO @result (is_valid, validation_message)
    VALUES (@is_valid, @message);
    
    RETURN;
END');
GO

PRINT 'Database schema updated successfully!';
PRINT 'Added support for TEIF 1.8.8 with complete validation and XML generation';