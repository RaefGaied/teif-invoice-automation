-- Check the current status values and their counts in the invoices table
SELECT 
    status,
    COUNT(*) as count,
    CONVERT(VARCHAR(10), MIN(created_at), 120) as first_created,
    CONVERT(VARCHAR(10), MAX(created_at), 120) as last_created
FROM 
    invoices
GROUP BY 
    status
ORDER BY 
    count DESC;

-- Show the structure of the invoices table
SELECT 
    c.name as column_name,
    TYPE_NAME(c.user_type_id) as data_type,
    c.max_length,
    c.is_nullable,
    ISNULL(OBJECT_DEFINITION(c.default_object_id), '') as default_value
FROM 
    sys.columns c
WHERE 
    OBJECT_ID = OBJECT_ID('invoices')
ORDER BY 
    c.column_id;
-- First, update the status column to use the new enum values
ALTER TABLE invoices
ALTER COLUMN status NVARCHAR(50) 
    CONSTRAINT DF_invoices_status DEFAULT 'processing' 
    CONSTRAINT CK_invoices_status CHECK (status IN ('processing', 'processed', 'error'));
    
-- Update any existing 'draft' status to 'processing'
UPDATE invoices 
SET status = 'processing' 
WHERE status = 'draft';