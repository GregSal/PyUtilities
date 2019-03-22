from pathlib import Path
from typing import Union, Dict, List, Set, Tuple, Any
from collections import namedtuple
import xml.etree.ElementTree as ET
from file_utilities import set_base_dir, get_file_path, PathInput

ElementKeySet = namedtuple('ElementKeySet', ['element_name',
                                             'key_list', 'key_set'
                                             'prefix_str', 'suffix_str'])
ElementDict = Dict[str, Any]
ElementList = List[ElementDict]
ElementData = Union[ElementDict, ElementList]
KeyList = List[ElementKeySet]
KeySet = Set[str]
SubElementGroup = Tuple[ElementDict, KeySet]
ElementGroup = Tuple[ElementDict, KeySet, KeySet]


def dir_xml_iter(directory_to_scan: PathInput, sub_dir: str = None,
                 base_path: Path = None):
    '''Returns an iterator which scans a dictionary tree and returns xml files'''
    scan_dir_path = get_file_path(directory_to_scan, sub_dir, base_path)
    for file_item in scan_dir_path.iterdir():
        # if the item is a file generate a FileStat object with it
        if file_item.is_file():
            if 'xml' in file_item.suffix:
                yield file_item
        elif file_item.is_dir():
            # recursively scan sub-directories
            for sub_file_item in dir_xml_iter(file_item):
                yield sub_file_item
    pass



def display_element(element_item,indent=''):
    '''Generate a formatted string of the element hierarchy.
    '''
    element_str = '{}Element: {}\n'.format(indent,element_item.tag)
    attr = element_item.attrib
    if len(attr) > 0:
        element_str += '{}\tAttributes:\n'.format(indent)
        for (key,item) in attr.items():
            element_str += '{}\t\t{:>20}:  {:<30}\n'.format(indent,key,item)
    text = element_item.text
    if text is not None:
       element_str += '{}\tValue: {}\n'.format(indent,text)
    tail = element_item.tail
    if tail is not None:
       element_str += '{}\tTail: {}\n'.format(indent,tail)
    if len(list(element_item)) > 0:
        element_str += '{}\tSub Elements:\n'.format(indent)
        for sub_element in element_item:
            element_str += display_element(sub_element,indent+'\t\t')
    return element_str


def element_to_dict(element_item: ET.Element, include_sub_elements=True,
                    element_index: Dict[str, int] = None)->Dict[str, Any]:
    '''Convert the components of an element into a flat dictionary.
    Arguments:
        element_item {ET.Element} -- The XML element to extract the data from.
        include_sub_elements {optional, bool} -- Iterate through sub elements
            and add them to the dictionary. Default is True.
        element_index {optional, Dict[str, int]} -- A dictionary containing all
            element tags already in use along with the usage count.
    Returns:
        A dictionary containing all text and attributes of the element and
        optionally its sub-elements.
    '''

    def add_value(element_item: ET.Element, tag_key: str):
        '''Add the "Text" and "Tail" components of an element.
            The possible keys are:
                    tag_key
                    tag_key + '_Tail'
        Arguments:
            element_item {ET.Element} -- The XML element to extract the data from.
            tag_key {str} -- The key prefix for the values.
        Returns:
            A dictionary containing the "Text" and "Tail" components of an
            element.
        '''
        value_dict = dict()
        text = element_item.text
        tail = element_item.tail
        if text is not None:
            value_dict[tag_key] = text
        if tail is not None:
            tag_tail = tag_key + '_Tail'
            value_dict[tag_tail] = tail
        return value_dict

    def add_attributes(element_item: ET.Element, tag_key: str):
        '''Convert the keys of the attribute dictionary to include the tag text.
            The keys are tag_key + '_' + attribute_name
            Newlines are replaced with spaces
            A Nil attribute name will be replaced with 'nil'
        Arguments:
            element_item {ET.Element} -- The XML element to extract the data from.
            tag_key {str} -- The key prefix for the values.
        Returns:
            A dictionary containing the attributes of an element.
        '''
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

    if element_index is None:
        element_index=dict()
    element_dict = dict()
    tag = element_item.tag
    if tag:
        tag = str(tag)
    else:
        tag = ''
    index = element_index.get(tag, '')
    if index:
        element_index[tag] = index + 1
    else:
        element_index[tag] = 2  #  Blank tag index treated as 1
    tag_key = tag + str(index)
    value_dict = add_value(element_item, tag_key)
    element_dict.update(value_dict)

    attr_dict = add_attributes(element_item, tag_key)
    element_dict.update(attr_dict)

    if include_sub_elements:
        for sub_element in element_item:
            (sub_dict, element_index) = element_to_dict(sub_element,
                                                        element_index)
            element_dict.update(sub_dict)
    return (element_dict, element_index)


def scan_for_elements(element_tree: ET.Element, name=None,
                      include_sub_elements=True)->SubElementGroup:
    '''Scan through the tree for all elements of a given name.
    Arguments:
        element_tree {ET.Element} -- The XML tree to scan.
        name {optional, str} -- The element tags to extract.
        include_sub_elements {optional, bool} -- Iterate through sub elements
            and add them to the dictionary. Default is True.
        Returns:
            A list containing the dictionaries for each instance of the
            specified element.
        and
            A set of all keys in any of the dictionaries in the list.
    '''
    element_list = list()
    key_set = set()
    for element_item in element_tree.iter(name):
        element_dict = element_to_dict(element_item, element_index=dict())[0]
        new_keys = set(element_dict.keys())
        key_set.update(new_keys)
        element_list.append(element_dict)
    return (element_list, key_set)


def get_element_info(element_tree: ET.Element, name: str):
    '''Extract the data from a single element.
        element_tree {ET.Element} -- The XML tree to scan.
        name {optional, str} -- The element tags to extract.
        include_sub_elements {optional, bool} -- Itterate through sub elements
            and add them to the dictionary. Default is True.
        Returns:
            A list containing the dictionaries for each instance of the
            specified element.
        and
            A set of all keys in any of the dictionaries in the list.
    '''
    selected_element = element_tree.find(name)
    element_dict = element_to_dict(selected_element,
                                   include_sub_elements=False)[0]
    return element_dict


def get_element_data_set(element_tree: ET.Element, main_element: str, list_elements: str):
    '''Build a table of elements'''
    element_dict = get_element_info(element_tree, main_element)
    #Extract the desired sub-element data table
    (element_list, key_set) = scan_for_elements(element_tree, list_elements)
    element_dict[list_elements] = element_list
    return (element_dict, key_set)


def scan_files(main_element_name: str, list_element_name: str,
               scan_path: PathInput, sub_dir: str = None,
               base_path: Path = None)->ElementGroup:
    main_element_list = list()
    sub_element_key_set = set()
    main_element_key_set = set()
    for xml_file in dir_xml_iter(scan_path, sub_dir, base_path):
        tree = ET.parse(str(xml_file))
        root = tree.getroot()
        (element_dict, new_keys) = get_element_data_set(
                root, main_element_name, list_element_name)
        element_dict['File Name'] = str(xml_file)
        sub_element_key_set.update(new_keys)
        main_element_key_set.update(set(element_dict.keys()))
        main_element_list.append(element_dict)
    return (main_element_list, sub_element_key_set, main_element_key_set)


def element_str_iter(element_data: ElementData, key_list_sets: KeyList)->str:
    '''Iterate through all elements dictionaries in the list generating a data string.
    '''
    def add_item_str(element_dict: ElementDict, key_list_data: ElementKeySet):
        key_list = key_list_data.key_list
        element_string = str()
        for key in key_list:
            item = element_dict.get(key)
            if item is None:
                element_string += '\t'
            else:
                element_string += '\t' + str(item)
        return key_list_data.prefix_str + element_str

    key_list_data = key_list_sets.pop(0)
    element_name = key_list_data.element_name
    suffix = key_list_data.suffix_str
    if isinstance(element_data, dict):
        element_list = element_data.get(element_name)
    else:
        element_list = element_data

    for element_dict in element_list:
        this_element_str = add_item_str(element_dict, key_list_data)
        if len(key_list_sets) > 0:
            for element_str in element_str_iter(element_dict, key_list_sets):
                yield this_element_str + element_str + suffix
        else:
            yield this_element_str + suffix

def build_variable_set():
    def make_key_list(primary_keys, key_set):
        '''make an ordered list of keys starting with the primary keys'''
        remaining_keys = key_set.difference(set(primary_keys))
        all_keys = primary_keys
        all_keys.extend(remaining_keys)
        return all_keys

    def make_indexed_key_list(indexed_keys: list, key_set: set):
        '''Make an ordered list of indexed keys by looking for indexed_keys + index'''
        def add_index(key: str, index: int):
            '''Make an indexed set of keys by adding the index to the key string'''
            return key + str(index)

        indexed_key_list = indexed_keys.copy()
        key_set = key_set.difference(indexed_keys)
        index = 2
        while len(key_set) > 0:
            indexed_keys = list(map(add_index, indexed_keys, index))
            found = [key in key_set for key in indexed_keys]
            if any(found):
                indexed_key_list.extend(indexed_keys)
                key_set = key_set.difference(indexed_keys)
                index += 1
            else:
                key_set = set()
        return indexed_key_list
    #generate variable lists
    if len(sub_element_key_list) > 0:
           objective_key_list = make_objective_key_list(objective_keys, structure_key_set)
           primary_structure_keys.extend(objective_key_list)
    structure_key_list = make_key_list(primary_structure_keys, structure_key_set)

    preview_key_set.discard(search_string)
    preview_key_list = make_key_list(primary_preview_keys, preview_key_set)

    key_list_sets = [
        ElementKeySet('Preview', objective_Structure_keys,
                      preview_key_set, ' ', ' '),
        ElementKeySet('ObjectivesOneStructure', individual_objective_keys,
                      objective_key_set, ' ', ' ')
        ]

def make_xml_table(output_file, main_element_list, key_list_sets):
    '''Write the list of structures to a tab delimited file'''

    def make_header_line(sub_element_key_list, main_element_key_list):
        '''Make the header label consisting of variable names'''
        header = str()
        for item in main_element_key_list:
            header += '\t' + item
        for item in sub_element_key_list:
            header += '\t' + item
        header += '\n'
        return header




    file_str = make_header_line(structure_key_list, preview_key_list)
    for template_str in template_iter(template_list, structure_key_list, preview_key_list, search_string):
        file_str += template_str
    output_file.write_text(file_str)

    for template_str in element_str_iter(main_element_list, key_list_sets)

def main():
    template_path = set_base_dir(r'Structure Dictionary\Template Archive')
    clinical_protocols_path = template_path / 'protocol Templates'
    structure_templates_path =  template_path / 'Structure Templates'
    objective_templates_path = template_path / 'Objective Templates'

    output_table = get_file_path('all_objective_data.txt',
                                 base_path=template_path)
    primary_preview_keys = ['Preview_ID', 'Preview_Type']
    structure_keys = ['Structure_ID', 'Structure_Name', 'VolumeType',
                      'VolumeCode', 'VolumeCodeTable', 'ColorAndStyle']
    objective_Structure_keys = ['ObjectivesOneStructure_ID', 'VolumeType',
                                'Distance', 'Color', 'VolumeCode',
                                'VolumeCodeTable']
    individual_objective_keys = ['Group', 'Type', 'Operator', 'Dose',
                                 'Volume', 'Priority']
    template_data = scan_files('Preview', 'ObjectivesOneStructure',
                               objective_templates_path)
    (template_list, objective_key_set, preview_key_set) = template_data


    make_xml_table(output_table, template_list, key_list_sets)

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


