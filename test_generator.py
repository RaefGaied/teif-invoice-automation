from src.teif.generator import TEIFGenerator
from datetime import datetime, timedelta

def test_generator():
    # Create a minimal test invoice
    invoice_data = {
        "version": "1.8.8",
        "controlling_agency": "TTN",
        "header": {
            "sender_identifier": "0736202XAM000",
            "receiver_identifier": "0914089JAM000"
        },
        "bgm": {
            "document_number": "TEST-001",
            "document_type": "I-11",
            "document_type_label": "Facture"
        },
        "dates": [
            {
                "date_text": datetime.now().strftime("%d%m%y"),
                "function_code": "I-31",
                "format": "ddMMyy"
            }
        ]
    }
    
    # Generate XML
    generator = TEIFGenerator()
    xml_content = generator.generate_teif_xml(invoice_data)
    
    # Print XML to console
    print("Generated XML:")
    print(xml_content)
    
    # Save to file
    with open("output/test_invoice.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    print("\nXML saved to output/test_invoice.xml")

if __name__ == "__main__":
    test_generator()
