"""
Script de test pour vérifier la correction des espaces de noms dans la signature XML.
"""
import sys
import os
from pathlib import Path
from lxml import etree

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / 'src'))

from teif.sections.signature import sign_xml

def test_signature_namespaces():
    # Données de test
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <TEIF xmlns="http://www.tn.gov/teif"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.tn.gov/teif TEIF_1.8.8.xsd"
          version="1.8.8"
          controlingAgency="TTN">
        <InvoiceHeader>
            <MessageSenderIdentifier type="I-01">0736202XAM000</MessageSenderIdentifier>
            <MessageRecipientIdentifier type="I-01">0914089JAM000</MessageRecipientIdentifier>
            <CreationDateTime>20250901150000</CreationDateTime>
        </InvoiceHeader>
        <InvoiceBody>
            <Bgm>
                <DocumentIdentifier>TEST-2023-001</DocumentIdentifier>
                <DocumentType code="I-11">Facture</DocumentType>
            </Bgm>
        </InvoiceBody>
    </TEIF>"""

    # Chemin vers le certificat et la clé de test
    test_dir = Path(__file__).parent / 'tests' / 'test_data'
    cert_path = test_dir / 'test_cert.pem'
    key_path = test_dir / 'test_key.pem'

    # Lire le certificat et la clé
    with open(cert_path, 'rb') as f:
        cert_data = f.read()
    
    with open(key_path, 'rb') as f:
        key_data = f.read()

    # Signer le document
    signed_xml = sign_xml(test_xml, cert_data, key_data)
    
    # Sauvegarder le résultat pour inspection
    output_path = Path(__file__).parent / 'output' / 'signed_invoice.xml'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(signed_xml)
    
    print(f"Document signé enregistré sous : {output_path}")
    
    # Vérifier les espaces de noms
    root = etree.fromstring(signed_xml)
    nsmap = root.nsmap
    
    print("\nEspaces de noms trouvés :")
    for prefix, uri in nsmap.items():
        print(f"{prefix if prefix else '(default)'}: {uri}")
    
    # Vérifier la présence des préfixes ds et xades
    assert 'ds' in nsmap, "Préfixe 'ds' manquant"
    assert 'xades' in nsmap, "Préfixe 'xades' manquant"
    
    print("\nTest réussi : les espaces de noms sont correctement définis.")

if __name__ == "__main__":
    test_signature_namespaces()
