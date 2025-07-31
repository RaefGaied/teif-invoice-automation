import fs from "fs"
import path from "path"

// --- Données d'exemple de la facture (format JSON) ---
// Dans un cas réel, ces données proviendraient de votre base de données ou de votre ERP.
const invoiceData = {
  invoiceNumber: "INV-2024-001",
  invoiceDate: "2024-07-30",
  sender: {
    name: "Ma Société SARL",
    taxId: "MF1234567A",
    address: "123 Rue de l'Innovation, 1000 Tunis",
  },
  receiver: {
    name: "Client Alpha SA",
    taxId: "MF9876543B",
    address: "456 Avenue du Progrès, 3000 Sfax",
  },
  items: [
    { description: "Service de développement logiciel", quantity: 1, unitPrice: 1500.0, total: 1500.0 },
    { description: "Licence annuelle Logiciel X", quantity: 2, unitPrice: 250.0, total: 500.0 },
  ],
  totalAmount: 2000.0,
  currency: "TND",
}

/**
 * Transforme les données de facture JSON en un format XML simplifié (simulant TEIF).
 * @param {object} data - Les données de la facture au format JSON.
 * @returns {string} La facture au format XML simplifié.
 */
function transformToTeif(data) {
  const invoiceNum = data.invoiceNumber || ""
  const invoiceDate = data.invoiceDate || ""
  const sender = data.sender || {}
  const receiver = data.receiver || {}
  const items = data.items || []
  const totalAmount = data.totalAmount || 0.0
  const currency = data.currency || "TND"

  let xmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<TEIFInvoice xmlns="http://www.tradenet.com.tn/teif/invoice/1.0"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd">
    <InvoiceHeader>
        <InvoiceNumber>${invoiceNum}</InvoiceNumber>
        <InvoiceDate>${invoiceDate}</InvoiceDate>
        <Currency>${currency}</Currency>
        <TotalAmount>${totalAmount.toFixed(2)}</TotalAmount>
    </InvoiceHeader>
    <SenderDetails>
        <Name>${sender.name || ""}</Name>
        <TaxID>${sender.taxId || ""}</TaxID>
        <Address>${sender.address || ""}</Address>
    </SenderDetails>
    <ReceiverDetails>
        <Name>${receiver.name || ""}</Name>
        <TaxID>${receiver.taxId || ""}</TaxID>
        <Address>${receiver.address || ""}</Address>
    </ReceiverDetails>
    <InvoiceItems>
`

  for (const item of items) {
    xmlContent += `        <Item>
            <Description>${item.description || ""}</Description>
            <Quantity>${item.quantity || 0}</Quantity>
            <UnitPrice>${(item.unitPrice || 0.0).toFixed(2)}</UnitPrice>
            <LineTotal>${(item.total || 0.0).toFixed(2)}</LineTotal>
        </Item>
`
  }

  xmlContent += `    </InvoiceItems>
    <!-- Espace réservé pour la Signature Électronique -->
    <!-- Cette partie nécessite un certificat électronique qualifié et des bibliothèques cryptographiques spécifiques. -->
    <ElectronicSignature>
        <SignatureValue>PLACEHOLDER_POUR_DONNEES_DE_SIGNATURE_ELECTRONIQUE</SignatureValue>
    </ElectronicSignature>
</TEIFInvoice>
`
  return xmlContent
}

// --- Exécution du script ---
const outputDir = "public/teif-invoices" // Dossier de sortie pour les factures TEIF générées
const fileName = `facture_${invoiceData.invoiceNumber}.xml`
const outputPath = path.join(outputDir, fileName)

// Créer le dossier de sortie s'il n'existe pas
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true })
}

// Effectuer la transformation et sauvegarder le fichier
const teifXml = transformToTeif(invoiceData)

try {
  fs.writeFileSync(outputPath, teifXml, "utf-8")
  console.log(`Facture transformée en TEIF et sauvegardée sous : ${outputPath}`)
  console.log("\n--- IMPORTANT ---")
  console.log(
    "Ceci est un exemple SIMPLIFIÉ du format TEIF. Le format réel est plus complexe et doit être strictement conforme au schéma officiel de TTN.",
  )
  console.log(
    "La signature électronique est un processus cryptographique distinct qui nécessite un certificat qualifié et des outils spécifiques, non inclus dans ce script de transformation de base.",
  )
} catch (error) {
  console.error("Erreur lors de la sauvegarde du fichier TEIF :", error)
}
