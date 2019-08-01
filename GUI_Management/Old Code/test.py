from typing import Union, Callable, List, Dict, NamedTuple, Tuple, Any
from pathlib import Path
from file_utilities import set_base_dir
from pickle import dump, load
from typing import NamedTuple

class TreeLevel(NamedTuple):
    group_name: str
    group_values: List[str]

TreeLevelList = List[TreeLevel]

groups = [TreeLevel('workbook_name', ['TemplateCategory', 'TreatmentSite', 'modification_date']),
          TreeLevel('sheet_name', ['TemplateID', 'TemplateCategory', 'TreatmentSite', 'Diagnosis', 'Author'])]


template_directory = set_base_dir(r'Work\Structure Dictionary\Template Spreadsheets')
template_file = template_directory / 'TemplateData.pkl'
file = open(str(template_file), 'rb')
template_data = load(file)
template_data.columns
item_set= template_data.groupby(['workbook_name', 'sheet_name'])
select = ['TemplateID', 'TemplateCategory', 'TreatmentSite']
for name, group in item_set:
    values = group[select]
    print(values)
group_1= template_data.groupby('workbook_name')
a = group_1.first().iloc[0]
for Index_1, groups in group_1:
    print(Index_1)
    print(groups[select])
    group_2 = groups.groupby('sheet_name')
    for Index_2, groups_2 in group_2:
        print(Index_2)
        print(groups_2)

