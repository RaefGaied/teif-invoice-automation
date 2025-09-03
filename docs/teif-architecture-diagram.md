# TEIF Converter - Architecture & Workflow Diagram

## Main Workflow
\`\`\`mermaid
graph TB
    subgraph "Input Layer"
        PDF[📄 PDF Invoice]
        CONFIG[⚙️ Configuration Files]
        CERTS[🔐 Certificates]
    end
    
    subgraph "CLI Interface"
        CLI[🖥️ Command Line Interface]
        ARGS[📝 Arguments Parser]
    end
    
    subgraph "Core Processing"
        EXTRACTOR[🔍 PDF Extractor]
        GENERATOR[⚡ TEIF Generator]
        VALIDATOR[✅ XML Validator]
    end
    
    subgraph "TEIF Sections Generation"
        HEADER[📋 Header Section]
        PARTNER[👥 Partner Section]
        LINES[📊 Invoice Lines]
        TAXES[💰 Tax Calculation]
        AMOUNTS[💵 Amount Management]
        PAYMENT[💳 Payment Terms]
        SIGNATURE[🔏 XAdES Signature]
    end
    
    subgraph "Output Layer"
        XML[📄 TEIF XML]
        SIGNED[🔒 Signed XML]
    end
    
    PDF --> CLI
    CONFIG --> CLI
    CERTS --> CLI
    
    CLI --> ARGS
    ARGS --> EXTRACTOR
    EXTRACTOR --> GENERATOR
    
    GENERATOR --> HEADER
    GENERATOR --> PARTNER
    GENERATOR --> LINES
    GENERATOR --> TAXES
    GENERATOR --> AMOUNTS
    GENERATOR --> PAYMENT
    
    HEADER --> VALIDATOR
    PARTNER --> VALIDATOR
    LINES --> VALIDATOR
    TAXES --> VALIDATOR
    AMOUNTS --> VALIDATOR
    PAYMENT --> VALIDATOR
    
    VALIDATOR --> XML
    XML --> SIGNATURE
    SIGNATURE --> SIGNED
    
    style PDF fill:#e1f5fe
    style XML fill:#e8f5e8
    style SIGNED fill:#fff3e0
    style CLI fill:#f3e5f5
    style GENERATOR fill:#fff8e1
    style SIGNATURE fill:#ffebee
\`\`\`

## Detailed Component Architecture
\`\`\`mermaid
graph LR
    subgraph "src/extractors/"
        EXT1[PDF Extractor]
        EXT2[Text Parser]
        EXT3[Data Normalizer]
    end
    
    subgraph "src/teif/sections/"
        SEC1[header.py]
        SEC2[partner.py]
        SEC3[lines.py]
        SEC4[taxes.py]
        SEC5[amounts.py]
        SEC6[payment.py]
        SEC7[signature.py]
        SEC8[common.py]
    end
    
    subgraph "src/teif/"
        GEN[generator.py]
        UTILS[utils/]
    end
    
    subgraph "src/cli/"
        MAIN[main.py]
    end
    
    EXT1 --> EXT2
    EXT2 --> EXT3
    EXT3 --> GEN
    
    GEN --> SEC1
    GEN --> SEC2
    GEN --> SEC3
    GEN --> SEC4
    GEN --> SEC5
    GEN --> SEC6
    GEN --> SEC7
    
    SEC8 --> SEC1
    SEC8 --> SEC2
    SEC8 --> SEC3
    SEC8 --> SEC4
    SEC8 --> SEC5
    SEC8 --> SEC6
    SEC8 --> SEC7
    
    UTILS --> GEN
    MAIN --> GEN
    
    style GEN fill:#ffeb3b
    style MAIN fill:#4caf50
\`\`\`

## TEIF XML Structure Flow
\`\`\`mermaid
graph TD
    subgraph "TEIF Document Structure"
        ROOT[🏗️ TEIF Root Element]
        
        subgraph "Document Metadata"
            HEADER_XML[📋 Header<br/>- DocumentType: INVOICE<br/>- DocumentNumber<br/>- DocumentDate<br/>- Currency: TND]
        end
        
        subgraph "Business Parties"
            SELLER[🏢 Seller<br/>- Name<br/>- TaxIdentifier<br/>- Address]
            BUYER[🏪 Buyer<br/>- Name<br/>- TaxIdentifier<br/>- Address]
        end
        
        subgraph "Invoice Content"
            INV_HEADER[📄 InvoiceHeader<br/>- Invoice Details<br/>- References]
            INV_LINES[📊 InvoiceLines<br/>- Line Items<br/>- Quantities<br/>- Unit Prices]
            INV_TOTALS[💰 InvoiceTotals<br/>- MOA I-181: HT Amount<br/>- MOA I-182: VAT Amount<br/>- MOA I-183: TTC Amount]
        end
        
        subgraph "Security Layer"
            SIG_SECTION[🔐 Signature<br/>- XAdES-B Format<br/>- SignedInfo<br/>- SignatureValue<br/>- KeyInfo<br/>- QualifyingProperties]
        end
    end
    
    ROOT --> HEADER_XML
    ROOT --> SELLER
    ROOT --> BUYER
    ROOT --> INV_HEADER
    ROOT --> INV_LINES
    ROOT --> INV_TOTALS
    ROOT --> SIG_SECTION
    
    style ROOT fill:#2196f3,color:#fff
    style HEADER_XML fill:#4caf50,color:#fff
    style SELLER fill:#ff9800,color:#fff
    style BUYER fill:#ff9800,color:#fff
    style INV_HEADER fill:#9c27b0,color:#fff
    style INV_LINES fill:#9c27b0,color:#fff
    style INV_TOTALS fill:#9c27b0,color:#fff
    style SIG_SECTION fill:#f44336,color:#fff
\`\`\`

## Signature Generation Process
\`\`\`mermaid
sequenceDiagram
    participant PDF as PDF Invoice
    participant EXT as Extractor
    participant GEN as TEIF Generator
    participant SIG as Signature Section
    participant CERT as Certificate Store
    participant XML as Final XML
    
    PDF->>EXT: Extract invoice data
    EXT->>GEN: Parsed invoice data
    GEN->>GEN: Generate TEIF sections
    GEN->>SIG: Request signature
    SIG->>CERT: Load certificate & key
    CERT-->>SIG: Certificate data
    SIG->>SIG: Create SignedInfo
    SIG->>SIG: Calculate digest (SHA-256)
    SIG->>SIG: Generate signature value
    SIG->>SIG: Add XAdES properties
    SIG-->>GEN: Complete signature element
    GEN->>XML: Final signed TEIF XML
    
    Note over SIG: XAdES-B Signature Elements:<br/>- ds:SignedInfo<br/>- ds:SignatureValue<br/>- ds:KeyInfo<br/>- ds:Object (XAdES properties)
\`\`\`

## Data Flow & Validation
\`\`\`mermaid
flowchart TD
    START([🚀 Start Process])
    
    subgraph "Input Validation"
        CHECK_PDF{📄 Valid PDF?}
        CHECK_CERT{🔐 Certificate Available?}
    end
    
    subgraph "Data Processing"
        EXTRACT[🔍 Extract PDF Data]
        NORMALIZE[📝 Normalize Data]
        VALIDATE_DATA{✅ Data Valid?}
    end
    
    subgraph "XML Generation"
        GEN_HEADER[📋 Generate Header]
        GEN_PARTIES[👥 Generate Parties]
        GEN_LINES[📊 Generate Lines]
        GEN_TOTALS[💰 Calculate Totals]
        VALIDATE_XML{✅ XML Valid?}
    end
    
    subgraph "Signature Process"
        CREATE_SIG[🔏 Create Signature]
        SIGN_DOC[✍️ Sign Document]
        VALIDATE_SIG{✅ Signature Valid?}
    end
    
    SUCCESS([✅ Success: TEIF XML Generated])
    ERROR([❌ Error: Process Failed])
    
    START --> CHECK_PDF
    CHECK_PDF -->|Yes| CHECK_CERT
    CHECK_PDF -->|No| ERROR
    CHECK_CERT -->|Yes| EXTRACT
    CHECK_CERT -->|No| ERROR
    
    EXTRACT --> NORMALIZE
    NORMALIZE --> VALIDATE_DATA
    VALIDATE_DATA -->|Yes| GEN_HEADER
    VALIDATE_DATA -->|No| ERROR
    
    GEN_HEADER --> GEN_PARTIES
    GEN_PARTIES --> GEN_LINES
    GEN_LINES --> GEN_TOTALS
    GEN_TOTALS --> VALIDATE_XML
    VALIDATE_XML -->|Yes| CREATE_SIG
    VALIDATE_XML -->|No| ERROR
    
    CREATE_SIG --> SIGN_DOC
    SIGN_DOC --> VALIDATE_SIG
    VALIDATE_SIG -->|Yes| SUCCESS
    VALIDATE_SIG -->|No| ERROR
    
    style START fill:#4caf50,color:#fff
    style SUCCESS fill:#4caf50,color:#fff
    style ERROR fill:#f44336,color:#fff
    style CHECK_PDF fill:#2196f3,color:#fff
    style CHECK_CERT fill:#2196f3,color:#fff
    style VALIDATE_DATA fill:#ff9800,color:#fff
    style VALIDATE_XML fill:#ff9800,color:#fff
    style VALIDATE_SIG fill:#ff9800,color:#fff
