from pathlib import Path
import xml.etree.ElementTree as ET

def display_element(element_item,indent):
    element_str = str(element_item.tag).rsplit('}',1)[1]
    print('{}Element: {}'.format(indent,element_str))
    attr = element_item.attrib
    if len(attr) > 0:
        print('{}\tAttributes:'.format(indent))
        for (key,item) in attr.items():
            # Replace newlines with space
            item = str(item).replace('\n',' ')
            item = str(item).replace('\r',' ')
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
    # template_path = Path(r'C:\Users\gsalomon\OneDrive for Business\Structure Dictionary\Templates')
    # structure_templates_path = template_path / 'Current Clinical Templates' / 'Structure Templates'
    # objective_templates_path = template_path / 'Current Clinical Templates' / 'Objective Templates'
    # plan_templates_path = template_path / 'Current Clinical Templates' / 'Plan Templates'
    # clinical_protocols_path = template_path / 'Current Clinical Templates' / 'Clinical Protocols'

    # head_and_neck_structures = structure_templates_path / 'H+N IMRT 70.xml'
    # bladder_structures = template_path / 'V 13 templates' / 'Structure Templates' / 'Bladder.xml
    base_path = Path.cwd()
    eclipse_machine_file_path = base_path / 'Machine Templates'
    eclipse_tr1_file = eclipse_machine_file_path / 'TR1.xml'
    tree = ET.parse(str(eclipse_tr1_file))
    root = tree.getroot()
    display_element(root,'')

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

