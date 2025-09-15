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

-- Update the status column with new default and constraint
ALTER TABLE invoices
ALTER COLUMN status NVARCHAR(50) NOT NULL;

-- Add the default constraint
ALTER TABLE invoices ADD CONSTRAINT DF_invoices_status DEFAULT 'processing' FOR status;

-- Add the check constraint with new enum values (lowercase)
ALTER TABLE invoices WITH NOCHECK
ADD CONSTRAINT CK_invoices_status 
CHECK (status IN ('processing', 'processed', 'error'));

-- Update any existing status to match the new values
-- First, check what statuses exist
SELECT DISTINCT status, COUNT(*) as count 
FROM invoices 
GROUP BY status 
ORDER BY count DESC;

-- Update all existing statuses to lowercase
UPDATE invoices 
SET status = LOWER(TRIM(status));

-- Convert any non-matching statuses to 'processing'
UPDATE invoices 
SET status = 'processing' 
WHERE status NOT IN ('processing', 'processed', 'error');

-- Recreate the index
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_invoices_status')
BEGIN
    CREATE INDEX IX_invoices_status ON invoices(status);
END

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
