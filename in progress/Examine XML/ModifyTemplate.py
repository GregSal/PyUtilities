from pathlib import Path
import xml.etree.ElementTree as ET

def display_element(element_item,indent):
    print('{}Element: {}'.format(indent,element_item.tag))
    attr = element_item.attrib
    if len(attr) > 0:
        print('{}\tAttributes:'.format(indent))
        for (key,item) in attr.items():
            print('{}\t\t{:>20}:  {:<30}'.format(indent,key,item))
    text = element_item.text
    if text is not None:
       print('{}\tValue: {}'.format(indent,text))
    tail = element_item.tail
    if tail is not None:
       print('{}\tTail: {}'.format(indent,tail))
    if len(list(element_item)) > 0:
        print('{}\tSub Elements:'.format(indent))
        for sub_element in element_item: 
            display_element(sub_element,indent+'\t\t')

def main():
    template_path = Path('\\\\dkphysicspv1\\e$\Gregs_Work\\Eclipse\\Version 13 upgrade\\Templates')
    clinical_protocols_path = template_path / 'Current Clinical Templates' / 'Clinical Protocols'
    new_templates = template_path / 'V 13 templates'
    lung_protocol_path = clinical_protocols_path / 'LUNL SABR 48 in 4.xml'
    test_template = new_templates / 'Test Protocol ALL.xml'
    test_prescriptions = new_templates / 'Prescription types.xml'
    tree = ET.parse(str(test_prescriptions))
    root = tree.getroot()
    general = root.find('Preview')
    general.set('ID','New Prescription')
    new_file = new_templates / 'New Prescription.xml'
    tree.write(str(new_file))
    #display_element(root,'')

main()
    #for child in root:
    #    print(child.tag, child.attrib)
    #list(root)
    #template = root.find('StructureTemplate')
    #list(template)
    #structures = template.find('Structures')
    #list(structures)
    #structures_list = structures.findall('Structure')
    #for structure in structures_list:
    #    print(structure.attrib['ID'])
    #    for attr in structure.iter():
    #        print('\t' + attr.tag)
    #        for elm in attr.itertext(): 
    #            print('\t\t' + elm)

