"""Debug script to examine PDF extraction issues"""
import sys
sys.path.append('src')

from extractors.pdf_extractor import PDFExtractor
import json

def debug_pdf_extraction():
    """Debug the PDF extraction process step by step."""
    

    extractor = PDFExtractor()
    

    print("=== EXTRACTING RAW TEXT FROM PDF ===")
    try:
        raw_text = extractor._extract_text_from_pdf("facture.pdf")  
        print("Raw text extracted successfully!")
        print(f"Text length: {len(raw_text)} characters")
        print("\n=== FIRST 500 CHARACTERS OF RAW TEXT ===")
        print(repr(raw_text[:500]))
        print("\n=== READABLE FIRST 500 CHARACTERS ===")
        print(raw_text[:500])
        
        # Save raw text for inspection
        with open("debug_raw_text.txt", "w", encoding="utf-8") as f:
            f.write(raw_text)
        print("\n✓ Raw text saved to debug_raw_text.txt")
        
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        return
    
    # Test specific extraction methods
    print("\n=== TESTING INVOICE NUMBER EXTRACTION ===")
    invoice_num = extractor._extract_invoice_number(raw_text)
    print(f"Extracted invoice number: '{invoice_num}'")
    
    print("\n=== TESTING COMPANY EXTRACTION ===")
    sender, receiver = extractor._extract_companies(raw_text)
    print(f"Sender: {json.dumps(sender, indent=2)}")
    print(f"Receiver: {json.dumps(receiver, indent=2)}")
    
    print("\n=== TESTING AMOUNT EXTRACTION ===")
    amounts = extractor._extract_amounts(raw_text)
    print(f"Amounts: {json.dumps(amounts, indent=2)}")
    
    print("\n=== TESTING TTN SPECIFIC EXTRACTION ===")
    # Check if methods exist before calling them
    if hasattr(extractor, '_extract_ttn_amounts'):
        ttn_amounts = extractor._extract_ttn_amounts(raw_text)
        print(f"TTN Amounts: {json.dumps(ttn_amounts, indent=2)}")
    else:
        print("⚠️ _extract_ttn_amounts method not found")
    
    if hasattr(extractor, '_extract_ttn_items'):
        ttn_items = extractor._extract_ttn_items(raw_text)
        print(f"TTN Items: {json.dumps(ttn_items, indent=2)}")
    else:
        print("⚠️ _extract_ttn_items method not found")
    
    print("\n=== FULL EXTRACTION TEST ===")
    full_data = extractor.extract_from_pdf("facture.pdf")  # Fixed filename
    
    # Save debug data
    with open("debug_full_extraction.json", "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2, ensure_ascii=False)
    print("✓ Full extraction saved to debug_full_extraction.json")
    
    # Show key issues
    print("\n=== IDENTIFIED ISSUES ===")
    issues = []
    
    if full_data["invoice_number"] in ["tre", "UNKNOWN"] or len(full_data["invoice_number"]) < 3:
        issues.append(f"❌ Invoice number issue: '{full_data['invoice_number']}'")
    
    if full_data["sender"]["name"] in ["Rue du Lac Malaren", "ENTREPRISE EMETTRICE", ""]:
        issues.append(f"❌ Sender name issue: '{full_data['sender']['name']}'")
    
    if full_data["total_amount"] == 0.0:
        issues.append("❌ No amounts extracted from PDF")
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✓ No major issues detected")

if __name__ == "__main__":
    debug_pdf_extraction()
