-- First, check if the index exists and drop it
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_status')
BEGIN
    DROP INDEX IX_invoices_status ON invoices;
END
GO

-- Drop the default constraint if it exists
DECLARE @constraint_name NVARCHAR(256);
SELECT @constraint_name = name 
FROM sys.default_constraints 
WHERE parent_object_id = OBJECT_ID('invoices') 
AND parent_column_id = (
    SELECT column_id 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('invoices') 
    AND name = 'status'
);

IF @constraint_name IS NOT NULL
BEGIN
    EXEC('ALTER TABLE invoices DROP CONSTRAINT ' + @constraint_name);
END
GO

-- Drop the check constraint if it exists
IF EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_invoices_status')
BEGIN
    ALTER TABLE invoices DROP CONSTRAINT CK_invoices_status;
END
GO

-- Update existing statuses to match the new enum values
-- First check current status distribution
SELECT status, COUNT(*) as count 
FROM invoices 
GROUP BY status 
ORDER BY count DESC;

-- Map old statuses to new values
UPDATE invoices 
SET status = CASE 
    WHEN LOWER(TRIM(status)) IN ('draft', 'new') THEN 'draft'
    WHEN LOWER(TRIM(status)) IN ('processing', 'in_progress', 'in-progress') THEN 'processing'
    WHEN LOWER(TRIM(status)) IN ('generated', 'processed') THEN 'generated'
    WHEN LOWER(TRIM(status)) = 'error' THEN 'error'
    WHEN LOWER(TRIM(status)) = 'uploading' THEN 'uploading'
    WHEN LOWER(TRIM(status)) = 'uploaded' THEN 'uploaded'
    WHEN LOWER(TRIM(status)) = 'archived' THEN 'archived'
    ELSE 'draft'  -- default for any unexpected values
END;

-- Update the status column to be NOT NULL with new default
ALTER TABLE invoices
ALTER COLUMN status NVARCHAR(50) NOT NULL;

-- Add the default constraint
ALTER TABLE invoices 
ADD CONSTRAINT DF_invoices_status DEFAULT 'draft' FOR status;

-- Add the check constraint with new enum values
ALTER TABLE invoices WITH NOCHECK
ADD CONSTRAINT CK_invoices_status 
CHECK (status IN ('draft', 'uploading', 'uploaded', 'processing', 'generated', 'error', 'archived'));

-- Recreate the index
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_status')
BEGIN
    CREATE INDEX IX_invoices_status ON invoices(status);
END
GO

-- Verify the update
SELECT 
    status,
    COUNT(*) as count
FROM 
    invoices
GROUP BY 
    status
ORDER BY 
    count DESC;