# TEIF XML Structure - Comprehensive Analysis (v1.8.8)

## Overview
This document provides a complete analysis of the Tunisian Electronic Invoice Format (TEIF) XML structure based on the official TTN standard version 1.8.8.

## 1. Document Structure

### 1.1 Root Element
```xml
<TEIF 
    xmlns="http://www.tradenet.com.tn/teif/invoice/1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd"
    version="1.8.8"
    controlingAgency="TTN">
```

**Attributes:**
- `version`: "1.8.8" (MANDATORY)
- `controlingAgency`: "TTN" (MANDATORY)
- `xmlns`: TEIF namespace (MANDATORY)
- `xmlns:xsi`: XML Schema Instance (MANDATORY)
- `xsi:schemaLocation`: XSD schema location (MANDATORY)

### 1.2 Document Header
```xml
<DocumentHeader>
    <DocumentIdentifier>FACT-2025-001</DocumentIdentifier>
    <DocumentType code="I-11">Facture</DocumentType>
    <CreationDateTime>2025-08-05T12:00:00</CreationDateTime>
</DocumentHeader>
```

**Elements:**
- `DocumentIdentifier`: Unique invoice number (MANDATORY)
- `DocumentType`: 
  - `code`: "I-11" for invoice (MANDATORY)
  - Text: "Facture" (MANDATORY)
- `CreationDateTime`: ISO 8601 format (MANDATORY)

## 2. Partner Information (MANDATORY)

### 2.1 PartnerSection
```xml
<PartnerSection>
    <!-- Supplier (Fournisseur) -->
    <Partner functionCode="I-62">
        <Name nameType="Qualification">NOM DU FOURNISSEUR</Name>
        <TaxId>12345678A</TaxId>
        <Address>
            <Street>RUE PRINCIPALE</Street>
            <City>TUNIS</City>
            <PostalCode>1000</PostalCode>
            <Country>TN</Country>
        </Address>
        <Contact>
            <Name>CONTACT COMMERCIAL</Name>
            <Phone>+216 XX XXX XXX</Phone>
            <Email>contact@fournisseur.tn</Email>
        </Contact>
    </Partner>
    
    <!-- Buyer (Client) -->
    <Partner functionCode="I-64">
        <Name nameType="Qualification">NOM DU CLIENT</Name>
        <TaxId>98765432B</TaxId>
        <Address>
            <Street>AVENUE HABIB BOURGUIBA</Street>
            <City>SOUSSE</City>
            <PostalCode>4000</PostalCode>
            <Country>TN</Country>
        </Address>
    </Partner>
</PartnerSection>
```

**Function Codes:**
- `I-62`: Supplier (Fournisseur)
- `I-64`: Buyer (Client)

## 3. Invoice Body (MANDATORY)

### 3.1 Invoice Header
```xml
<InvoiceBody>
    <Bgm>
        <DocumentNameCode>380</DocumentNameCode>
        <DocumentNumber>FACT-2025-001</DocumentNumber>
    </Bgm>
    <Dtm>
        <DateTimeQualifier>137</DateTimeQualifier>
        <DateTime>2025-08-05</DateTime>
    </Dtm>
    <PaymentTerms>
        <TermsType>1</TermsType>
        <TermsDescription>Paiement à 30 jours</TermsDescription>
    </PaymentTerms>
```

### 3.2 Line Items
```xml
    <Line lineNumber="1">
        <Item>
            <Description>Produit ou service</Description>
            <BuyerItemIdentification>
                <ID>REF-001</ID>
            </BuyerItemIdentification>
        </Item>
        <Quantity unit="PCE">1.000</Quantity>
        <Price>
            <Amount amountTypeCode="I-183" currencyIdentifier="TND">1000.000</Amount>
        </Price>
        <LineTotal>
            <Amount amountTypeCode="I-171" currencyIdentifier="TND">1000.000</Amount>
        </LineTotal>
    </Line>
```

**Amount Type Codes:**
- `I-183`: Unit price
- `I-171`: Line total amount

### 3.3 Invoice Summary
```xml
    <InvoiceMoa>
        <Amount amountTypeCode="I-176" currencyIdentifier="TND">1000.000</Amount>
        <Amount amountTypeCode="I-180" currencyIdentifier="TND">1190.000</Amount>
        <Amount amountTypeCode="I-181" currencyIdentifier="TND">190.000</Amount>
    </InvoiceMoa>
    
    <InvoiceTax>
        <TaxTypeName code="I-1602">TVA</TaxTypeName>
        <TaxRate>19.0</TaxRate>
        <TaxableAmount>1000.000</TaxableAmount>
        <TaxAmount>190.000</TaxAmount>
    </InvoiceTax>
</InvoiceBody>
```

**Amount Type Codes:**
- `I-176`: Total amount without tax
- `I-180`: Total amount with tax
- `I-181`: Total tax amount

## 4. Additional Information (CONDITIONAL)

```xml
<AdditionalInformation>
    <Note>Conditions de paiement: Paiement à 30 jours fin de mois</Note>
    <Reference>
        <ReferenceType>ON</ReferenceType>
        <ReferenceNumber>CMD-2025-001</ReferenceNumber>
    </Reference>
</AdditionalInformation>
```

## 5. Signature (CONDITIONAL)

```xml
<Signature>
    <SignatoryParty>
        <Name>NOM DU SIGNATAIRE</Name>
        <Title>Directeur Commercial</Title>
    </SignatoryParty>
    <DigitalSignature>
        <!-- Signature électronique XAdES -->
    </DigitalSignature>
</Signature>
```

## Validation Rules

### Mandatory Fields
1. Root element with all required attributes
2. Document header with unique identifier
3. Supplier and buyer information
4. At least one line item
5. Invoice totals (with and without tax)
6. Tax information

### Data Types
- **Amounts**: Decimal with 3 decimal places (e.g., 1000.000)
- **Dates**: ISO 8601 format (YYYY-MM-DD)
- **Tax Rates**: Decimal with 1 decimal place (e.g., 19.0)
- **Currencies**: TND (Tunisian Dinar)

### Business Rules
1. Line totals must equal quantity × unit price
2. Tax amounts must equal taxable amount × (tax rate / 100)
3. Document numbers must be unique
4. All monetary amounts must be in TND

## Example Complete Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEIF 
    xmlns="http://www.tradenet.com.tn/teif/invoice/1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd"
    version="1.8.8"
    controlingAgency="TTN">
    
    <DocumentHeader>
        <DocumentIdentifier>FACT-2025-001</DocumentIdentifier>
        <DocumentType code="I-11">Facture</DocumentType>
        <CreationDateTime>2025-08-05T12:00:00</CreationDateTime>
    </DocumentHeader>
    
    <!-- Partner and Invoice Body sections as shown above -->
    
</TEIF>
```

## Version History

### v1.8.8 (Current)
- Added support for digital signatures
- Updated tax calculation rules
- Enhanced validation rules

### v1.7.0
- Initial public release
- Basic invoice structure
- Support for standard tax calculations

## References

1. [TTN TEIF 1.8.8 Specification](https://www.tradenet.tn/teif/specs)
2. [Tunisian Tax Authority Requirements](https://www.impots.finances.gov.tn)
3. [UN/CEFACT XML Naming and Design Rules](https://www.unece.org/cefact/)





""" 
   def _add_partner_details(self, parent: ET.Element, partner_data: Dict[str, Any], function_code: str):
     Ajoute les détails d'un partenaire (vendeur ou acheteur).
     partner = ET.SubElement(
        parent,
        "PartnerDetails",
        functionCode=function_code
     )
    
     nad = ET.SubElement(partner, "Nad")
    
     # Identifiant du partenaire
     ET.SubElement(
        nad,
        "PartnerIdentifier",
        type=partner_data.get('id_type', 'I-01')
    ).text = partner_data.get('id', '')
    
     # Nom du partenaire
     ET.SubElement(
        nad,
        "PartnerName",
        nameType="Qualification"
     ).text = partner_data.get('name', '')
    
     # Adresse
     address = ET.SubElement(
        nad,
        "PartnerAdresses",
        lang=partner_data.get('language', 'fr')
     )
    
     # Détails de l'adresse
     ET.SubElement(
        address,
        "Street"
    ).text = partner_data.get('address', {}).get('street', '')
    
     ET.SubElement(
        address,
        "CityName"
    ).text = partner_data.get('address', {}).get('city', '')
    
     ET.SubElement(
        address,
        "PostalCode"
    ).text = partner_data.get('address', {}).get('postal_code', '')
    
     ET.SubElement(
        address,
        "Country",
        codeList="ISO_3166-1"
    ).text = partner_data.get('address', {}).get('country', 'TN')
     """

     
""" def _add_partner_section(self, parent: ET.Element, data: Dict[str, Any]):
    Ajoute la section des partenaires (vendeur et acheteur).
      partner_section = ET.SubElement(parent, "PartnerSection")
    
      # Détails du vendeur
      self._add_partner_details(
        partner_section,
        data.get('seller', {}),
        function_code="I-62"  # Code pour le vendeur
    )
    
      # Détails de l'acheteur
      self._add_partner_details(
        partner_section,
        data.get('buyer', {}),
        function_code="I-64"  # Code pour l'acheteur
    )"""
