from pathlib import Path
import xml.etree.ElementTree as ET

def element_to_dict(element_item: ET.Element, include_sub_elements=True, \
                    super_dict=dict(), element_index=dict(), index=''):
    '''convert the components of an element into a flat dictionary'''

    def add_value(element_item: ET.Element, tag: str, tag_key: str):
        '''Create a dictionary of the "Text" and "Tail" components of an element'''
        value_dict = dict()
        if tag is not None:
            text = element_item.text
            tail = element_item.tail
            if text is not None:
                value_dict[tag_key] = text
            if tail is not None:
                tag_tail = tag_key + '_Tail'
                value_dict[tag_tail] = tail
        return value_dict
            
    def add_attributes(element_item: ET.Element, tag: str, tag_key: str):
        '''Convert the keys of the attribute dictionary to include the tag text'''
        attr_dict = dict()
        attributes = element_item.attrib
        for (key, value) in attributes.items():
            # Replace newlines with space
            value = str(value).replace('\n',' ')
            value = str(value).replace('\r',' ')
            key_str = str(key)
            if '}nil' in key_str:
                key_str = 'nil'
            atr_key = tag_key + '_' + key_str
            attr_dict[atr_key] = value
        return attr_dict

    element_dict = dict()
    tag = str(element_item.tag)
    tag_key = tag + index
    value_dict = add_value(element_item, tag, tag_key)
    element_dict.update(value_dict)

    attr_dict = add_attributes(element_item, tag, tag_key)
    element_dict.update(attr_dict)

    if include_sub_elements:
        sub_dict = dict()
        for sub_element in element_item: 
            tag = str(sub_element.tag)
            if tag in super_dict:
                index = element_index.get(tag)
                if index is None:
                    index = 2
                else:
                    index += 1
                element_index[tag] = index
            else:
                index = ''                    
            (sub_dict, element_index) = element_to_dict(sub_element, super_dict=element_dict.keys(), element_index=element_index, index=str(index))
            element_dict.update(sub_dict)
            sub_dict.clear()
    return (element_dict, element_index)


def scan_structure_set(element_tree: ET.Element, search_string='Structures'):
    structure_list = list()
    key_set = set()
    for element_item in element_tree.iter(search_string):
        element_dict = element_to_dict(element_item, element_index=dict())[0]
        new_keys = set(element_dict.keys())
        key_set.update(new_keys)
        structure_list.append(element_dict)
    return (structure_list, key_set)

def dir_xml_iter(directory_to_scan: Path):
    '''Returns an iterator which scans a dictionary tree and returns xml files'''
    for file_item in directory_to_scan.iterdir():
        # if the item is a file generate a FileStat object with it
        if file_item.is_file():
            if 'xml' in file_item.suffix:
                yield file_item
        elif file_item.is_dir():
            # recursively scan sub-directories
            for sub_file_item in dir_xml_iter(file_item):
                yield sub_file_item

def get_template_info(template_root: ET.Element, search_string='Structures'):
    '''Extract the structure data from a template'''
    #Extract the Preview data from a template        
    template = template_root.find('Preview')
    template_dict = element_to_dict(template, include_sub_elements=False, element_index=dict())[0]
    #Extract the structure data
    (structure_list, key_set) = scan_structure_set(template_root, search_string)
    template_dict[search_string] = structure_list
    return (template_dict, key_set)

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

def scan_files(scan_path, search_string='Structures'):
    template_list = list()
    key_set = set()
    preview_key_set = set()
    for template_file in dir_xml_iter(scan_path):
        tree = ET.parse(str(template_file))
        root = tree.getroot()
        #display_element(root,'')
        template_dict = dict()
        (template_dict, new_keys) = get_template_info(root, search_string)
        key_set.update(new_keys)
        #for element in root.iter():
        #    (element_dict, new_keys) = get_template_info(element, search_string)
        #    template_dict.update(element_dict)
        #    key_set.update(new_keys)
        template_dict['File Name'] = str(template_file)
        preview_key_set.update(set(template_dict.keys()))
        template_list.append(template_dict)
        #display_element(root,'')
    return (template_list, key_set, preview_key_set)

def make_structures_table(output_file, template_list, structure_key_set, preview_key_set, primary_structure_keys=[], objective_keys=[], search_string='Structures'):
    '''Write the list of structures to a tab delimited file'''

    def make_key_list(primary_keys, key_set):
        '''make an ordered list of keys starting with the primary keys'''        
        remaining_keys = key_set.difference(set(primary_keys))
        all_keys = primary_keys
        all_keys.extend(remaining_keys)
        return all_keys

    def make_objective_key_list(objective_keys: list, key_set: set):
        '''Make an ordered list of objective keys by looking for objective key + index'''
        def add_index(key: str):
            '''Make an indexed set of keys by adding the index to the key string'''
            return key + str(index)

        objective_key_list = objective_keys.copy()
        key_set = key_set.difference(objective_keys)
        index = 2
        while len(key_set) > 0:
            indexed_keys = list(map(add_index, objective_keys))
            found = [key in key_set for key in indexed_keys]
            if any(found):
                objective_key_list.extend(indexed_keys)
                key_set = key_set.difference(indexed_keys)
                index += 1
            else:
                key_set = set()
        return objective_key_list

    def make_header_line(structure_key_list, preview_key_list):
        '''Make the header label consisting of variable names'''
        header = str()
        for item in preview_key_list:
            header += '\t' + item
        for item in structure_key_list:
            header += '\t' + item
        header += '\n'
        return header

    def structure_iter(structure_list, structure_key_list):
        '''Iterate through all structures generating a structure data string'''
        for structure in structure_list:
            structure_str = str()
            for key in structure_key_list:
                item = structure.get(key)
                if item is None:
                    structure_str += '\t'
                else:
                    structure_str += '\t' + str(item)
            yield structure_str

    def template_iter(template_list, structure_key_list, preview_key_list, search_string='Structures'):
        '''Iterate through all structures generating a structure data string'''
        for template in template_list:
            template_str = str()
            #template items string
            starter_string = str()
            for key in preview_key_list:
                item = template.get(key)
                if item is None:
                    starter_string += '\t'
                else: 
                    starter_string += '\t' + str(item)
            structure_list = template.get(search_string)
            if structure_list is None:
                template_str = ''
            else:
                for structure_str in structure_iter(structure_list, structure_key_list):
                    template_str += starter_string + structure_str +'\n'
            yield template_str

    
    #generate variable lists
    if len(objective_keys) > 0:
           objective_key_list = make_objective_key_list(objective_keys, structure_key_set)
           primary_structure_keys.extend(objective_key_list)
    structure_key_list = make_key_list(primary_structure_keys, structure_key_set)

    primary_preview_keys = ['Preview_ID', 'Preview_Type']
    preview_key_set.discard(search_string)
    preview_key_list = make_key_list(primary_preview_keys, preview_key_set)

    file_str = make_header_line(structure_key_list, preview_key_list)
    for template_str in template_iter(template_list, structure_key_list, preview_key_list, search_string):
        file_str += template_str
    output_file.write_text(file_str)
    
def main():
    #template_path = Path('\\\\dkphysicspv1\\e$\Gregs_Work\\Eclipse\\Version 13 upgrade\\Structure Dictionary\\Templates')
    template_path = Path(r'C:\Users\gsalomon\OneDrive for Business 1\Structure Dictionary\Templates')
    #clinical_protocols_path = template_path / 'Current Clinical Templates' / 'Clinical Protocols'
    #clinical_templates_path = template_path / 'Current Clinical Templates'
    #new_templates = template_path / 'V 13 templates'
    #new_structure_templates =  template_path / 'V 13 templates\\Structure Templates'
    #objective_templates_path = template_path / 'Current Clinical Templates' / 'Objective Templates'
    #Barrie_protocols = template_path / 'From Barrie'
    clinical_trials_path = template_path / r'Current Clinical Templates\Clinical Trial Templates'
    #lung_protocol_path = clinical_protocols_path / 'LUNL SABR 48 in 4.xml'
    #test_template = new_templates / 'Test Protocol ALL.xml'
    #test_prescriptions = new_templates / 'Prescription types.xml'
    #test_evaluation = new_templates / 'Evaluation Items.xml'

    output_table = template_path / 'all_structure_data.txt'
    (template_list, structure_key_set, preview_key_set) = scan_files(clinical_trials_path, search_string='Structure')
    structure_keys = ['Structure_ID', 'Structure_Name', 'VolumeType', 'VolumeCode', 'VolumeCodeTable', 'ColorAndStyle']
    make_structures_table(output_table, template_list, structure_key_set, preview_key_set, primary_structure_keys=structure_keys, search_string='Structure')

    #objectives_table = template_path / 'all_objective_data.txt'
    #objectives_table = Barrie_protocols / 'Barrie_protocol_data.txt'
    #objective_Structure_keys = ['ObjectivesOneStructure_ID', 'VolumeType', 'Distance', 'Color', \
    #                            'VolumeCode', 'VolumeCodeTable']
                                #'ObjectivesOneStructure_SurfaceOnly', 'Distance_nil', 'SamplePoints_nil']
    #individual_objective_keys = ['Group', 'Type', 'Operator', 'Dose', 'Volume', 'Priority']
    #(template_list, objective_key_set, preview_key_set) = scan_files(Barrie_protocols, search_string='ObjectivesOneStructure')
    #make_structures_table(objectives_table, template_list, \
    #                      objective_key_set, preview_key_set, search_string='ObjectivesOneStructure', \
    #                      primary_structure_keys=objective_Structure_keys, \
    #                      objective_keys=individual_objective_keys)
    
    #tree = ET.parse(str(test_template))
    #root = tree.getroot()

    #(structure_list, key_set) = scan_structure_set(root)
    #keys = str()
    #for key in key_set:
    #    keys += '\t' + key
    #print(keys)
    #print('done')

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


