"""
Test module for the LinSection and LinItem classes.
"""
import unittest
import xml.etree.ElementTree as ET

from teif.sections.lines import LinSection, LinItem


class TestLinSection(unittest.TestCase):
    """Test cases for the LinSection and LinItem classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')
        self.lin_section = LinSection()
    
    def test_add_line_item(self):
        """Test adding a line item to the section."""
        line_item = LinItem(line_number=1)
        self.lin_section.add_line(line_item)
        self.assertEqual(len(self.lin_section.lines), 1)
    
    def test_to_xml_empty_section(self):
        """Test converting an empty section to XML."""
        self.lin_section.to_xml(self.parent)
        self.assertIsNone(self.parent.find('LinSection'))
    
    def test_to_xml_with_lines(self):
        """Test converting a section with lines to XML."""
        # Add a line item
        line_item = LinItem(line_number=1)
        line_item.set_item_info(
            item_identifier='1',
            item_code='DDM',
            description='Dossier DDM',
            lang='fr'
        )
        line_item.set_quantity(1.0, 'UNIT')
        line_item.add_tax(
            type_name='TVA',
            code='I-1602',
            category='S',
            details=[{'rate': 12, 'amount': 2.0}]
        )
        line_item.add_amount(2.0, 'I-183', 'TND')
        line_item.add_amount(2.0, 'I-171', 'TND')
        
        self.lin_section.add_line(line_item)
        self.lin_section.to_xml(self.parent)
        
        # Check the XML structure
        lin_section = self.parent.find('LinSection')
        self.assertIsNotNone(lin_section)
        
        lin = lin_section.find('Lin')
        self.assertIsNotNone(lin)
        self.assertEqual(lin.get('lineNumber'), '1')
        
        item_id = lin.find('ItemIdentifier')
        self.assertEqual(item_id.text, '1')
        
        imd = lin.find('LinImd')
        self.assertIsNotNone(imd)
        self.assertEqual(imd.get('lang'), 'fr')
        self.assertEqual(imd.find('ItemCode').text, 'DDM')
        self.assertEqual(imd.find('ItemDescription').text, 'Dossier DDM')
        
        qty = lin.find('LinQty/Quantity')
        self.assertEqual(qty.text, '1.0')
        self.assertEqual(qty.get('measurementUnit'), 'UNIT')
        
        tax = lin.find('LinTax')
        self.assertIsNotNone(tax)
        self.assertEqual(tax.find('TaxTypeName').text, 'TVA')
        self.assertEqual(tax.find('TaxCategory').text, 'S')
        
        tax_details = tax.findall('TaxDetails/TaxDetail')
        self.assertEqual(len(tax_details), 1)
        self.assertEqual(tax_details[0].find('TaxRate').text, '12')
        
        moa = lin.findall('LinMoa/MoaDetails/Moa')
        self.assertEqual(len(moa), 2)
        self.assertEqual(moa[0].get('amountTypeCode'), 'I-183')
        self.assertEqual(moa[0].find('Amount').text, '2.000')
        self.assertEqual(moa[1].get('amountTypeCode'), 'I-171')
        self.assertEqual(moa[1].find('Amount').text, '2.000')

    def test_generate_xml_example(self):
        """Generate and display XML for a sample LinSection."""
        # Create a sample LinSection with multiple line items
        section = LinSection()
        
        # Add first line item
        line1 = LinItem(line_number=1)
        line1.set_item_info(
            item_identifier='1',
            item_code='DDM',
            description='Dossier DDM',
            lang='fr'
        )
        line1.set_quantity(1.0, 'UNIT')
        line1.add_tax(
            type_name='TVA',
            code='I-1602',
            category='S',
            details=[{'rate': 12, 'amount': 2.0}]
        )
        line1.add_amount(2.0, 'I-183', 'TND')
        line1.add_amount(2.0, 'I-171', 'TND')
        
        # Add a sub-line item
        sub_line = LinItem(line_number=1.1)
        sub_line.set_item_info(
            item_identifier='1.1',
            item_code='SUB',
            description='Sous-ligne',
            lang='fr'
        )
        sub_line.set_quantity(1.0, 'UNIT')
        sub_line.add_amount(2.0, 'I-100', 'TND')
        line1.add_sub_line(sub_line)
        
        # Add second line item
        line2 = LinItem(line_number=2)
        line2.set_item_info(
            item_identifier='2',
            item_code='SVC',
            description='Service',
            lang='fr'
        )
        line2.set_quantity(1.0, 'SERVICE')
        line2.add_tax(
            type_name='TVA',
            code='I-1602',
            category='S',
            details=[{'rate': 19, 'amount': 3.8}]
        )
        line2.add_amount(20.0, 'I-100', 'TND')
        
        # Add lines to section
        section.add_line(line1)
        section.add_line(line2)
        
        # Generate XML
        root = ET.Element('TestRoot')
        section.to_xml(root)
        
        # Convert to a pretty-printed XML string
        from xml.dom import minidom
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        print("\nGenerated XML for LinSection:")
        print(xml_str)
        
        # Verify the XML structure
        self.assertIsNotNone(root.find('LinSection'))
        self.assertEqual(len(root.findall('.//Lin')), 3)  # 2 main lines + 1 sub-line


class TestLinItem(unittest.TestCase):
    """Test cases for the LinItem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')
        self.line_item = LinItem(line_number=1)
    
    def test_set_item_info(self):
        """Test setting item information."""
        self.line_item.set_item_info(
            item_identifier='1',
            item_code='DDM',
            description='Dossier DDM',
            lang='fr'
        )
        
        self.assertEqual(self.line_item.item_identifier, '1')
        self.assertEqual(self.line_item.item_code, 'DDM')
        self.assertEqual(self.line_item.description, 'Dossier DDM')
        self.assertEqual(self.line_item.language, 'fr')
    
    def test_set_quantity(self):
        """Test setting quantity information."""
        self.line_item.set_quantity(2.5, 'KGM')
        self.assertEqual(self.line_item.quantity['value'], 2.5)
        self.assertEqual(self.line_item.quantity['unit'], 'KGM')
    
    def test_add_amount(self):
        """Test adding a monetary amount."""
        self.line_item.add_amount(100.0, 'EUR', 'I-110')
        self.assertEqual(len(self.line_item.amounts), 1)
        self.assertEqual(self.line_item.amounts[0]['amount'], 100.0)
        self.assertEqual(self.line_item.amounts[0]['currency'], 'EUR')
        self.assertEqual(self.line_item.amounts[0]['type_code'], 'I-110')
    
    def test_add_tax(self):
        """Test adding tax information."""
        tax_details = [
            {'amount': 19.0, 'rate': 19.0, 'currency': 'TND'}
        ]
        self.line_item.add_tax(
            type_name='TVA',
            code='I-1602',
            category='S',
            details=tax_details
        )
        
        self.assertEqual(len(self.line_item.taxes), 1)
        self.assertEqual(self.line_item.taxes[0]['type_name'], 'TVA')
        self.assertEqual(self.line_item.taxes[0]['code'], 'I-1602')
        self.assertEqual(self.line_item.taxes[0]['category'], 'S')
        self.assertEqual(self.line_item.taxes[0]['details'], tax_details)
    
    def test_add_additional_info(self):
        """Test adding additional product information."""
        self.line_item.add_additional_info(
            code='COLOR',
            description='Red',
            lang='en'
        )
        
        self.assertEqual(len(self.line_item.additional_info), 1)
        self.assertEqual(self.line_item.additional_info[0]['code'], 'COLOR')
        self.assertEqual(self.line_item.additional_info[0]['description'], 'Red')
        self.assertEqual(self.line_item.additional_info[0]['lang'], 'en')
    
    def test_add_sub_line(self):
        """Test adding a sub-line to a line item."""
        sub_line = LinItem(line_number=1.1)
        self.line_item.add_sub_line(sub_line)
        
        self.assertEqual(len(self.line_item.sub_lines), 1)
        self.assertEqual(self.line_item.sub_lines[0].line_number, 1.1)
    
    def test_to_xml_complete(self):
        """Test complete XML generation with all fields."""
        line = LinItem(line_number=1)
        line.set_item_info(
            item_identifier='1',
            item_code='DDM',
            description='Dossier DDM',
            lang='fr'
        )
        line.set_quantity(1.0, 'UNIT')
        line.add_tax(
            type_name='TVA',
            code='I-1602',
            category='S',
            details=[{'rate': 12, 'amount': 2.0}]
        )
        line.add_amount(2.0, 'I-183', 'TND')
        line.add_amount(2.0, 'I-171', 'TND')

        # Create root element and add line
        root = ET.Element('TestRoot')
        section = ET.SubElement(root, 'LinSection')
        line.to_xml(section)

        # Convert to string for assertion
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Check basic structure
        self.assertIn('<LinSection>', xml_str)
        self.assertIn('<Lin lineNumber="1">', xml_str)
        
        # Check item identifier
        self.assertIn('<ItemIdentifier>1</ItemIdentifier>', xml_str)
        
        # Check item info
        self.assertIn('<LinImd lang="fr">', xml_str)
        self.assertIn('<ItemCode>DDM</ItemCode>', xml_str)
        self.assertIn('<ItemDescription>Dossier DDM</ItemDescription>', xml_str)
        
        # Check quantity
        self.assertIn('<LinQty>', xml_str)
        self.assertIn('<Quantity measurementUnit="UNIT">1.0</Quantity>', xml_str)
        
        # Check tax
        self.assertIn('<LinTax>', xml_str)
        self.assertIn('<TaxTypeName code="I-1602">TVA</TaxTypeName>', xml_str)
        self.assertIn('<TaxCategory>S</TaxCategory>', xml_str)
        self.assertIn('<TaxDetails>', xml_str)
        self.assertIn('<TaxRate>12</TaxRate>', xml_str)
        
        # Check amounts
        self.assertIn('<LinMoa>', xml_str)
        self.assertIn('<MoaDetails>', xml_str)
        self.assertIn('<Moa amountTypeCode="I-183" currencyCodeList="ISO_4217">', xml_str)
        self.assertIn('<Amount currencyIdentifier="TND">2.000</Amount>', xml_str)
        self.assertIn('<Moa amountTypeCode="I-171" currencyCodeList="ISO_4217">', xml_str)


if __name__ == '__main__':
    unittest.main()
