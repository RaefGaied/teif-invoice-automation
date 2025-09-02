"""
Utils for XML handling and serialization.
"""
from lxml import etree as ET

def serialize_xml(element, encoding='UTF-8', xml_declaration=True, pretty_print=True):
    """
    Serialize XML element to string with proper formatting.
    
    Args:
        element: The root XML element to serialize
        encoding: Output encoding (default: UTF-8)
        xml_declaration: Whether to include XML declaration (default: True)
        pretty_print: Whether to format the output with indentation (default: True)
        
    Returns:
        str: Formatted XML string
    """
    # Ensure we have a proper XML tree
    if not hasattr(element, 'getroottree'):
        element = ET.ElementTree(element)
    
    # Serialize to string with pretty printing
    return ET.tostring(
        element,
        xml_declaration=xml_declaration,
        encoding=encoding,
        pretty_print=pretty_print,
        standalone=True
    ).decode(encoding)

def save_xml(element, file_path, encoding='UTF-8'):
    """
    Save XML element to a file with proper formatting.
    
    Args:
        element: The root XML element to save
        file_path: Path to the output file
        encoding: Output encoding (default: UTF-8)
    """
    xml_string = serialize_xml(element, encoding=encoding)
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(xml_string)
