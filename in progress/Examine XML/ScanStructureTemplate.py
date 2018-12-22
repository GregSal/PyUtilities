from pathlib import Path
import xml.etree.ElementTree as ET

def display_element(element_item,indent):
    print('{}Element: {}'.format(indent,element_item.tag))
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
    #template_path = Path('\\\\dkphysicspv1\\e$\Gregs_Work\\Eclipse\\Version 13 upgrade\\Structure Dictionary\\Templates')
    template_path = Path(r'C:\Users\gsalomon\OneDrive for Business\Structure Dictionary\Templates')
    structure_templates_path = template_path / 'Current Clinical Templates' / 'Structure Templates'
    objective_templates_path = template_path / 'Current Clinical Templates' / 'Objective Templates'
    plan_templates_path = template_path / 'Current Clinical Templates' / 'Plan Templates'
    clinical_protocols_path = template_path / 'Current Clinical Templates' / 'Clinical Protocols'

    head_and_neck_structures = structure_templates_path / 'H+N IMRT 70.xml'
    bladder_structures = template_path / 'V 13 templates' / 'Structure Templates' / 'Bladder.xml'
    #head_and_neack_objectives = objective_templates_path / 'IMRT H&N 70 in 35.xml'
    #head_and_neck_objectives2 = objective_templates_path / 'IMRT H&N 60 in 30.xml'
    #head_and_neack_plan = plan_templates_path / 'VMAT H&N.xml'
    #new_templates = template_path / 'V 13 templates'
    #lung_protocol_path = clinical_protocols_path / 'LUNL SABR 48 in 4.xml'
    #test_template = new_templates / 'Test Protocol ALL.xml'
    #test_prescriptions = new_templates / 'Prescription types.xml'
    #test_evaluation = new_templates / 'Evaluation Items.xml'
    tree = ET.parse(str(bladder_structures))
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

