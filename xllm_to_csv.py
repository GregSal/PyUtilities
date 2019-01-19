import xml.etree.ElementTree as ET
import pandas as pd
from file_utilities import set_base_dir
from spreadsheet_tools import append_data_sheet


def display_element(element_item: ET.Element, indent: str, disp_txt: str)->str:
    element_str = str(element_item.tag).rsplit('}',1)[1]
    disp_txt += '{}Element: {}\n'.format(indent,element_str)
    attr = element_item.attrib
    if len(attr) > 0:
        disp_txt += '{}\tAttributes:\n'.format(indent)
        for (key,item) in attr.items():
            # Replace newlines with space
            item = str(item).replace('\n',' ')
            item = str(item).replace('\r',' ')
            disp_txt += '{}\t\t{:>20}:  {:<30}\n'.format(indent,key,item)
    text = element_item.text
    if text is not None:
       disp_txt += '{}\tValue: {}\n'.format(indent,text)
    tail = element_item.tail
    if tail is not None:
       disp_txt += '{}\tTail: {}\n'.format(indent,tail)
    if len(list(element_item)) > 0:
        disp_txt += '{}\tSub Elements:\n'.format(indent)
        for sub_element in element_item:
            disp_txt = display_element(sub_element, indent+'\t\t', disp_txt)
    return disp_txt


def flatten_element(element_item: ET.Element, top_data: dict,
                    add_empty=False)->list:
    data_list = list()
    flattened_data = dict()
    new_data = False
    element_id = str(element_item.tag).rsplit('}',1)[1]
    text = element_item.text
    tail = element_item.tail
    if text is not None:
        flattened_data[element_id] = text
        new_data = True
    elif tail is not None:
        flattened_data[element_id] = tail
        new_data = True
    elif add_empty:
        flattened_data[element_id] = element_id
        new_data = True
    attr = element_item.attrib
    if len(attr) > 0:
        new_data = True
        for (key,item) in attr.items():
            # Replace newlines with space
            item = str(item).replace('\n',' ')
            item = str(item).replace('\r',' ')
            flattened_data[key] = item
    if new_data:
        top_data.update(flattened_data)
        data_list.append(top_data)
    if len(list(element_item)) > 0:
        for sub_element in element_item:
            sub_element_id = str(sub_element.tag).rsplit('}',1)[1]
            element_data_list = flatten_element(sub_element, top_data.copy())
            data_list.extend(element_data_list)
            if len(element_data_list) == 1:
                top_data.update(element_data_list[0])
    return data_list


def main():
    base_path = set_base_dir('Work\\calculation models and configuration')
    eclipse_machine_file_path = base_path / 'Machine Templates'
    eclipse_tr1_file = eclipse_machine_file_path / 'TR1.xml'
    output_file = base_path / 'TR1.txt'
    output_spreadsheet = base_path / 'machine_data.xslx'
    worksheet = dict(file_name=output_spreadsheet, sheet_name='TR1',
                     new_file=True, new_sheet=True, replace=True)
    tree = ET.parse(str(eclipse_tr1_file))
    root = tree.getroot()
    data_list = []
    flattened_data = dict()
    data_list = flatten_element(root, flattened_data, data_list)
    data = pd.DataFrame(data_list)
    append_data_sheet(data, **worksheet)


#    display_str = display_element(root,'','')
#    output_file.write_text(display_str)
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

