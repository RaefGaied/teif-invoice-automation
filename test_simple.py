import sys
import os
import xml.etree.ElementTree as ET

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from teif.sections.header import create_header_element
    
    # Test minimal header
    header_data = {'message_id': 'TEST-123'}
    header = create_header_element(header_data)
    
    # Print the generated XML
    print("Test réussi! Voici l'en-tête XML généré :")
    print(ET.tostring(header, encoding='unicode'))
    
except Exception as e:
    print("Erreur lors du test :")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    import traceback
    traceback.print_exc()
