# TEIF XML Structure - Comprehensive Analysis

## Overview
This document provides a complete analysis of the Tunisian Electronic Invoice Format (TEIF) XML structure based on the official TTN standard and sample files.

## 1. Root Element Structure

```xml
<TEIFInvoice xmlns="http://www.tradenet.com.tn/teif/invoice/1.0" 
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
             xsi:schemaLocation="http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd">
```

**Requirements:**
- Namespace: `http://www.tradenet.com.tn/teif/invoice/1.0`
- Schema validation required
- Version attribute on InvoiceHeader

## 2. Element Sequence (MANDATORY ORDER)

### 2.1 InvoiceHeader (Rank 1 - MANDATORY)
```xml
<InvoiceHeader version="1.0">
    <MessageId>TTN-{INVOICE_NUMBER}-{TIMESTAMP}</MessageId>
</InvoiceHeader>
```

**Fields:**
- `version`: Always "1.0"
- `MessageId`: Format: TTN-{InvoiceNumber}-{YYYYMMDDHHmmss}

**Edge Cases:**
- MessageId must be unique
- Timestamp must be invoice generation time
- Maximum length: 50 characters

### 2.2 Bgm (Document Message - Rank 2 - MANDATORY)
```xml
<Bgm>
    <DocumentTypeCode>380</DocumentTypeCode>
    <DocumentNumber>INVOICE-001</DocumentNumber>
</Bgm>
```

**Fields:**
- `DocumentTypeCode`: Always "380" (Commercial Invoice)
- `DocumentNumber`: Invoice number from PDF

**Edge Cases:**
- DocumentNumber must match PDF invoice number exactly
- No special characters except hyphens and underscores
- Maximum length: 35 characters

### 2.3 Dtm (Date/Time - Rank 3 - MANDATORY)
```xml
<Dtm>
    <DateTimeQualifier>137</DateTimeQualifier>
    <DateTime>2025-07-30</DateTime>
</Dtm>
```

**Fields:**
- `DateTimeQualifier`: "137" (Document date)
- `DateTime`: Format YYYY-MM-DD

**Edge Cases:**
- Date must be valid
- Cannot be future date
- Must match PDF invoice date

### 2.4 PartnerSection - Supplier (Rank 4 - MANDATORY)
```xml
<PartnerSection role="supplier">
    <Nad>
        <PartyQualifier>SU</PartyQualifier>
        <PartyId>1234567ABC</PartyId>
        <PartyName>Entreprise Exemple</PartyName>
        <PartyAddress>Tunis</PartyAddress>
    </Nad>
</PartnerSection>
```

**Fields:**
- `role`: "supplier"
- `PartyQualifier`: "SU" (Supplier)
- `PartyId`: Company tax ID/identifier
- `PartyName`: Company name
- `PartyAddress`: Full address

**Edge Cases:**
- PartyId must be valid Tunisian tax ID format
- PartyName cannot be empty
- Address should include city and postal code if available

### 2.5 PartnerSection - Buyer (Rank 5 - MANDATORY)
```xml
<PartnerSection role="buyer">
    <Nad>
        <PartyQualifier>BY</PartyQualifier>
        <PartyId>9876543XYZ</PartyId>
        <PartyName>Client Exemple</PartyName>
        <PartyAddress>Sfax</PartyAddress>
    </Nad>
</PartnerSection>
```

**Fields:**
- `role`: "buyer"
- `PartyQualifier`: "BY" (Buyer)
- Similar structure to supplier

### 2.6 PytSection (Payment Terms - CONDITIONAL)
```xml
<PytSection>
    <Pyt>
        <PaymentTermsTypeCode>1</PaymentTermsTypeCode>
        <PaymentTermsDescription>Net 30 jours</PaymentTermsDescription>
    </Pyt>
</PytSection>
```

**Fields:**
- `PaymentTermsTypeCode`: Payment terms code
- `PaymentTermsDescription`: Human-readable description

**Edge Cases:**
- Optional section
- Common codes: 1 (Net), 2 (Cash), 3 (End of month)

### 2.7 LinSection (Line Items - MANDATORY)
```xml
<LinSection lineNumber="1">
    <LinImd>
        <ItemDescriptionType>F</ItemDescriptionType>
        <ItemDescription>Service exemple</ItemDescription>
    </LinImd>
    <LinQty>
        <QuantityQualifier>47</QuantityQualifier>
        <Quantity>1</Quantity>
        <MeasureUnitQualifier>PCE</MeasureUnitQualifier>
    </LinQty>
    <LinDtm>
        <DateTimeQualifier>137</DateTimeQualifier>
        <DateTime>2025-07-30</DateTime>
    </LinDtm>
    <LinTax>
        <DutyTaxFeeTypeCode>VAT</DutyTaxFeeTypeCode>
        <DutyTaxFeeRate>18.00</DutyTaxFeeRate>
        <TaxPaymentDate>
            <DateTimeQualifier>140</DateTimeQualifier>
            <DateTime>2025-07-30</DateTime>
        </TaxPaymentDate>
    </LinTax>
    <LinMoa>
        <MonetaryAmountTypeQualifier>203</MonetaryAmountTypeQualifier>
        <MonetaryAmount>84.75</MonetaryAmount>
        <CurrencyCode>TND</CurrencyCode>
        <Rff>
            <ReferenceQualifier>LI</ReferenceQualifier>
            <ReferenceNumber>LINE-1</ReferenceNumber>
        </Rff>
    </LinMoa>
</LinSection>
```

**Fields:**
- `lineNumber`: Sequential line number
- `ItemDescriptionType`: "F" (Free text)
- `ItemDescription`: Product/service description
- `QuantityQualifier`: "47" (Invoiced quantity)
- `Quantity`: Numeric quantity
- `MeasureUnitQualifier`: Unit code (PCE, KGM, etc.)
- `DutyTaxFeeTypeCode`: "VAT" or "TVA"
- `DutyTaxFeeRate`: Tax percentage
- `MonetaryAmountTypeQualifier`: "203" (Line amount)
- `MonetaryAmount`: Line total amount
- `CurrencyCode`: "TND"

**Edge Cases:**
- Multiple LinSection elements for multiple lines
- Quantity must be positive
- Tax rate must match Tunisian VAT rates (0%, 7%, 13%, 19%)
- Amount calculations must be precise

### 2.8 InvoiceMoa (Invoice Monetary Amounts - MANDATORY)
```xml
<InvoiceMoa>
    <Moa>
        <MonetaryAmountTypeQualifier>86</MonetaryAmountTypeQualifier>
        <MonetaryAmount>100.00</MonetaryAmount>
        <CurrencyCode>TND</CurrencyCode>
    </Moa>
</InvoiceMoa>
```

**Fields:**
- `MonetaryAmountTypeQualifier`: Amount type code
  - "86": Total invoice amount excluding VAT
  - "125": Total invoice amount including VAT
  - "176": Total amount due
- `MonetaryAmount`: Numeric amount (3 decimal places)
- `CurrencyCode`: "TND"

**Edge Cases:**
- Multiple Moa elements for different amount types
- Amounts must be consistent with line totals
- Precision: 3 decimal places

### 2.9 InvoiceTax (Tax Information - MANDATORY)
```xml
<InvoiceTax>
    <Tax>
        <DutyTaxFeeTypeCode>TVA</DutyTaxFeeTypeCode>
        <DutyTaxFeeRate>18.00</DutyTaxFeeRate>
        <Moa>
            <MonetaryAmountTypeQualifier>124</MonetaryAmountTypeQualifier>
            <MonetaryAmount>15.25</MonetaryAmount>
            <CurrencyCode>TND</CurrencyCode>
        </Moa>
    </Tax>
</InvoiceTax>
```

**Fields:**
- `DutyTaxFeeTypeCode`: "TVA" or "VAT"
- `DutyTaxFeeRate`: Tax percentage
- `MonetaryAmountTypeQualifier`: "124" (Tax amount)
- `MonetaryAmount`: Tax amount
- `CurrencyCode`: "TND"

**Edge Cases:**
- Multiple Tax elements for different tax rates
- Tax amounts must match calculations
- Common Tunisian VAT rates: 0%, 7%, 13%, 19%

### 2.10 RefTtnVal (TTN Reference - MANDATORY)
```xml
<RefTtnVal>
    <Reference>
        <ReferenceQualifier>AAK</ReferenceQualifier>
        <ReferenceNumber>SAMPLE-REF-001</ReferenceNumber>
        <ReferenceDate>
            <DateTimeQualifier>171</DateTimeQualifier>
            <DateTime>2025-07-30</DateTime>
        </ReferenceDate>
    </Reference>
</RefTtnVal>
```

**Fields:**
- `ReferenceQualifier`: "AAK" (Reference number)
- `ReferenceNumber`: Unique reference
- `DateTimeQualifier`: "171" (Reference date)
- `DateTime`: Reference date

### 2.11 Signature (Digital Signature - MANDATORY)
```xml
<Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    <ds:SignedInfo>
        <ds:CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
        <ds:SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
    </ds:SignedInfo>
    <!-- Additional signature elements -->
</Signature>
```

## 3. Data Validation Rules

### 3.1 Mandatory Fields
- All elements marked as MANDATORY must be present
- Cannot be empty or null

### 3.2 Format Validation
- Dates: YYYY-MM-DD format
- Amounts: Numeric with up to 3 decimal places
- Currency: Always "TND"
- Tax rates: Valid Tunisian VAT rates

### 3.3 Business Rules
- Total amounts must equal sum of line amounts
- Tax amounts must be calculated correctly
- Invoice date cannot be in the future
- Party IDs must be valid Tunisian format

### 3.4 Edge Cases to Handle
- Missing PDF data → Use default values
- Invalid amounts → Validation and correction
- Multiple tax rates → Separate Tax elements
- Long descriptions → Truncate to field limits
- Special characters → Escape or remove
- Empty line items → Skip or use defaults

## 4. Common Error Scenarios

### 4.1 Data Extraction Issues
- Company names extracted as addresses
- Amounts showing as 0.000
- Invoice numbers as fragments ("tre")
- Missing tax information

### 4.2 XML Validation Issues
- Incorrect element order
- Missing mandatory fields
- Invalid data formats
- Namespace errors

### 4.3 Business Logic Issues
- Amount calculations don't match
- Tax rates not recognized
- Invalid party identifiers
- Date inconsistencies

## 5. Implementation Checklist

- [ ] Root element with correct namespace
- [ ] InvoiceHeader with unique MessageId
- [ ] Bgm with correct document type
- [ ] Dtm with valid date
- [ ] Both PartnerSection elements
- [ ] LinSection for each invoice line
- [ ] InvoiceMoa with all amount types
- [ ] InvoiceTax with correct calculations
- [ ] RefTtnVal with unique reference
- [ ] Signature section (can be placeholder)
- [ ] Data validation for all fields
- [ ] Error handling for missing data
- [ ] Business rule validation
- [ ] XML schema validation
