# Diagramme de Génération XML TEIF

## Processus de Génération XML Seulement

\`\`\`mermaid
flowchart TD
    A[Données Invoice Extraites] --> B{Validation des Données}
    B -->|Valides| C[Initialisation XML TEIF]
    B -->|Invalides| Z[Erreur: Données Manquantes]
    
    C --> D[Génération Header Section]
    D --> E[Génération Seller Section]
    E --> F[Génération Buyer Section]
    F --> G[Génération Invoice Lines]
    G --> H[Génération Tax Summary]
    H --> I[Génération Payment Section]
    I --> J[Génération Totals Section]
    
    J --> K{Validation XML Structure}
    K -->|Valide| L[XML TEIF Complet]
    K -->|Invalide| M[Correction Structure XML]
    M --> K
    
    L --> N[Formatage et Indentation]
    N --> O[XML TEIF Final]
    
    subgraph "Sections XML Générées"
        D1[Header: ID, Date, Type]
        E1[Seller: Nom, Adresse, TVA]
        F1[Buyer: Nom, Adresse, TVA]
        G1[Lines: Produits, Quantités, Prix]
        H1[Tax: TVA, Taxes diverses]
        I1[Payment: Conditions, Échéances]
        J1[Totals: HT, TVA, TTC]
    end
    
    D --> D1
    E --> E1
    F --> F1
    G --> G1
    H --> H1
    I --> I1
    J --> J1
    
    style A fill:#e1f5fe
    style O fill:#c8e6c9
    style Z fill:#ffcdd2
    style M fill:#fff3e0
\`\`\`

## Détail des Étapes de Génération

\`\`\`mermaid
sequenceDiagram
    participant Data as Données Invoice
    participant Gen as XML Generator
    participant Val as Validator
    participant XML as Document XML
    
    Data->>Gen: Données extraites
    Gen->>Val: Validation données
    Val-->>Gen: Données validées
    
    Gen->>XML: Créer racine TEIF
    Gen->>XML: Ajouter Header
    Gen->>XML: Ajouter Seller
    Gen->>XML: Ajouter Buyer
    
    loop Pour chaque ligne
        Gen->>XML: Ajouter InvoiceLine
    end
    
    Gen->>XML: Ajouter TaxSummary
    Gen->>XML: Ajouter PaymentSection
    Gen->>XML: Ajouter Totals
    
    Gen->>Val: Valider structure XML
    Val-->>Gen: Structure validée
    
    Gen->>XML: Formater document
    XML-->>Gen: XML TEIF final
\`\`\`

## Structure des Données XML

\`\`\`mermaid
graph LR
    A[XML TEIF Root] --> B[Header]
    A --> C[Seller]
    A --> D[Buyer]
    A --> E[InvoiceLines]
    A --> F[TaxSummary]
    A --> G[PaymentSection]
    A --> H[Totals]
    
    B --> B1[InvoiceID]
    B --> B2[InvoiceDate]
    B --> B3[InvoiceType]
    
    C --> C1[SellerName]
    C --> C2[SellerAddress]
    C --> C3[SellerTVA]
    
    D --> D1[BuyerName]
    D --> D2[BuyerAddress]
    D --> D3[BuyerTVA]
    
    E --> E1[Line1: Product, Qty, Price]
    E --> E2[Line2: Product, Qty, Price]
    E --> E3[LineN: Product, Qty, Price]
    
    F --> F1[TVA Rate]
    F --> F2[TVA Amount]
    F --> F3[Other Taxes]
    
    G --> G1[Payment Terms]
    G --> G2[Due Date]
    
    H --> H1[Total HT]
    H --> H2[Total TVA]
    H --> H3[Total TTC]
    
    style A fill:#1976d2,color:#fff
    style B fill:#42a5f5
    style C fill:#42a5f5
    style D fill:#42a5f5
    style E fill:#66bb6a
    style F fill:#ffa726
    style G fill:#ab47bc
    style H fill:#ef5350,color:#fff
