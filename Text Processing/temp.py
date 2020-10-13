
from pathlib import Path
from itertools import chain
from typing import List
from file_utilities import clean_ascii_text
import Text_Processing as tp
import read_dvh_file
from pprint import pprint
import pandas as pd
from buffered_iterator import BufferedIterator, BufferedIteratorEOF


#%% Test Text
test_source = [
    'Patient Name         : ____, ____',
    'Patient ID           : 1234567',
    'Comment              : DVHs for multiple plans and plan sums',
    'Date                 : Friday, January 17, 2020 09:45:07',
    'Exported by          : gsal',
    'Type                 : Cumulative Dose Volume Histogram',
    ('Description          : The cumulative DVH displays the '
    'percentage (relative)'),
    ('                       or volume (absolute) of structures '
    'that receive a dose'),
    '                      equal to or greater than a given dose.',
    ''
    'Plan sum: Plan Sum',
    'Course: PLAN SUM',
    'Prescribed dose [cGy]: not defined',
    '% for dose (%): not defined',
    ''
    'Plan: PARR',
    'Course: C1',
    'Plan Status: Treatment Approved Thursday, January 02, '
    '2020 12:55:56 by gsal',
    'Prescribed dose [cGy]: 5000.0',
    '% for dose (%): 100.0',
    ''
    'Structure: PRV5 SpinalCanal',
    'Approval Status: Approved',
    'Plan: Plan Sum',
    'Course: PLAN SUM',
    'Volume [cm³]: 121.5',
    'Dose Cover.[%]: 100.0',
    'Sampling Cover.[%]: 100.1',
    'Min Dose [cGy]: 36.7',
    'Max Dose [cGy]: 3670.1',
    'Mean Dose [cGy]: 891.9',
    'Modal Dose [cGy]: 44.5',
    'Median Dose [cGy]: 863.2',
    'STD [cGy]: 621.9',
    'NDR: ',
    'Equiv. Sphere Diam. [cm]: 6.1',
    'Conformity Index: N/A',
    'Gradient Measure [cm]: N/A',
    ''
    'Dose [cGy] Ratio of Total Structure Volume [%]',
    '         0                       100',
    '         1                       100',
    '         2                       100',
    '         3                       100',
    '         4                       100',
    '         5                       100',
    '      3667              4.23876e-005',
    '      3668              2.87336e-005',
    '      3669              1.50797e-005',
    '      3670               1.4257e-006',
    '',
    'Structure: PTV 50',
    'Approval Status: Approved',
    'Plan: Plan Sum',
    'Course: PLAN SUM',
    'Volume [cm³]: 363.6',
    'Dose Cover.[%]: 100.0',
    'Sampling Cover.[%]: 100.0',
    'Min Dose [cGy]: 3985.9',
    'Max Dose [cGy]: 5442.0',
    'Mean Dose [cGy]: 5144.5',
    'Modal Dose [cGy]: 5177.3',
    'Median Dose [cGy]: 5166.9',
    'STD [cGy]: 131.9',
    'NDR: ',
    'Equiv. Sphere Diam. [cm]: 8.9',
    'Conformity Index: N/A',
    'Gradient Measure [cm]: N/A',
    '',
    'Dose [cGy] Ratio of Total Structure Volume [%]',
    '         0                       100',
    '         1                       100',
    '         2                       100',
    '         3                       100',
    '         4                       100',
    '         5                       100',
    '      5437               9.4777e-005',
    '      5438              6.35607e-005',
    '      5439              3.62425e-005',
    '      5440              1.82336e-005',
    '      5441              9.15003e-006',
    '      5442               6.6481e-008'
    ]


test_result = {
    'DVH Info': {
            'Patient Name': '____, ____',
            'Patient ID': '1234567',
            'Comment': 'DVHs for multiple plans and plan sums',
            'Date': 'Friday, January 17, 2020 09:45:07',
            'Exported by': 'gsal',
            'Type': 'Cumulative Dose Volume Histogram',
            'Description': ('The cumulative DVH displays the '
                            'percentage (relative) or volume '
                            '(absolute) of structures that receive a '
                            'dose equal to or greater than a '
                            'given dose.')
            },
    'Plan Info': [{
            'Plan sum': 'Plan Sum',
            'Course': 'PLAN SUM',
            'Prescribed dose': '',
            'Prescribed dose unit': '',
            '% for dose (%)': 'not defined'
            }, {
            'Plan': 'PARR',
            'Course': 'C1',
            'Plan Status': 'Treatment Approved',
            'Approved on': 'Thursday, January 02, 2020 12:55:56',
            'Approved by': 'gsal',
            'Prescribed dose': 5000.0,
            'Prescribed dose unit': 'cGy',
            '% for dose (%)': 100.0
            }],
    'Structures': pd.DataFrame([{
            'Structure': 'PRV5 SpinalCanal',
            'Approval Status': 'Approved',
            'Plan': 'Plan Sum',
            'Course': 'PLAN SUM',
            'Volume [cc]': 121.5,
            'Dose Cover.[%]': 100.0,
            'Sampling Cover.[%]': 100.1,
            'Min Dose [cGy]': 36.7,
            'Max Dose [cGy]': 3670.1,
            'Mean Dose [cGy]': 891.9,
            'Modal Dose [cGy]': 44.5,
            'Median Dose [cGy]': 863.2,
            'STD [cGy]': 621.9,
            'NDR': '',
            'Equiv. Sphere Diam. [cm]': 6.1,
            'Conformity Index': 'N/A',
            'Gradient Measure [cm]': 'N/A'
            },{
            'Structure': 'PTV 50',
            'Approval Status': 'Approved',
            'Plan': 'Plan Sum',
            'Course': 'PLAN SUM',
            'Volume [cc]': 363.6,
            'Dose Cover.[%]': 100.0,
            'Sampling Cover.[%]': 100.0,
            'Min Dose [cGy]': 3985.9,
            'Max Dose [cGy]': 5442.0,
            'Mean Dose [cGy]': 5144.5,
            'Modal Dose [cGy]': 5177.3,
            'Median Dose [cGy]': 5166.9,
            'STD [cGy]': 131.9,
            'NDR': '',
            'Equiv. Sphere Diam. [cm]': 8.9,
            'Conformity Index': 'N/A',
            'Gradient Measure [cm]': 'N/A'
            }]),
    'DVH': pd.DataFrame([
        {
            'Structure': 'PRV5 SpinalCanal',
            'Plan': 'Plan Sum',
            'Dose [cGy]': [0, 1, 2, 3, 4, 5, 3667, 3668, 3669, 3670],
            'Ratio of Total Structure Volume [%]': [100, 100, 100, 100,
                                                    100, 100,
                                                    4.23876e-005,
                                                    2.87336e-005,
                                                    1.50797e-005,
                                                    1.4257e-006]
            },
        {
            'Structure': 'PTV 50',
            'Plan': 'Plan Sum',
            'Dose [cGy]': [0,1,2,3,4,5,5437,5438,5439,5440,5441,5442],
            'Ratio of Total Structure Volume [%]': [100, 100, 100, 100,
                                                    100, 100,
                                                    9.4777e-005,
                                                    6.35607e-005,
                                                    3.62425e-005,
                                                    1.82336e-005,
                                                    9.15003e-006,
                                                    6.6481e-008]
            }])
    }

context = {
    'File Name': 'Test_DVH_Sections.txt',
    'File Path': Path.cwd() / 'Text Files' / 'Test_DVH_Sections.txt',
    'Line Count': 0
    }


#%% scan_section

dvh_info_break = read_dvh_file.dvh_info_break
dvh_info_section = read_dvh_file.dvh_dvh_info_section
repeating = False

source = iter(BufferedIterator(test_source))
context = {}
context['Source'] = source
break_check = dvh_info_break.check_start(context)
while True:
    try:
        row = source.__next__()
        test_output = break_check(row)
    except tp.StartSection as start_marker:
        break
# Done To Here
sentinel = end_marker.get_context()['sentinel']
context['Current Section'] = 'DVH Info'
break_check = dvh_info_break.check_end(context)
while True:
    try:
        row = source.__next__()
        test_output = break_check(row)
    except tp.StartSection as start_marker:
        break


section_iter = tp.cascading_iterators(source, [
    clean_ascii_text,
    dvh_info_parser.parse,
    tp.trim_items,
    tp.drop_blanks,
    tp.merge_continued_rows
    ])

test_output = output_method(section_iter)
pprint(test_output)

#%% Plan Info 1 Section
preprocessing_methods = [clean_ascii_text]
parsing_rules = [read_dvh_file.make_prescribed_dose_rule(),
                 read_dvh_file.make_approved_status_rule()]
default_parser = tp.define_csv_parser('plan_info', delimiter=':',
                                        skipinitialspace=True)
plan_info_parser = tp.LineParser(parsing_rules, default_parser)
post_processing_methods=[tp.trim_items, tp.drop_blanks, tp.convert_numbers]
output_method=tp.to_dict

# scan_section
source = BufferedIterator(test_source['Plan Info 1'])
context = {}
context['Source'] = source
context['Current Section'] = 'Plan Info 1'

section_iter = tp.cascading_iterators(source, [
    clean_ascii_text,
    plan_info_parser.parse,
    tp.trim_items,
    tp.drop_blanks,
    tp.convert_numbers
    ])

test_output = output_method(section_iter)
pprint(test_output)

#%% Plan Info 2 Section
preprocessing_methods = [clean_ascii_text]
parsing_rules = [read_dvh_file.make_prescribed_dose_rule(),
                 read_dvh_file.make_approved_status_rule()]
default_parser = tp.define_csv_parser('plan_info', delimiter=':',
                                        skipinitialspace=True)
plan_info_parser = tp.LineParser(parsing_rules, default_parser)
post_processing_methods=[tp.trim_items, tp.drop_blanks, tp.convert_numbers]
output_method=tp.to_dict

plan_info_section = tp.SectionReader(section_name='Plan Info',
                               preprocessing_methods=preprocessing_methods,
                               parsing_rules=parsing_rules,
                               default_parser=default_parser,
                               post_processing_methods=post_processing_methods,
                               output_method=output_method)
# scan_section
source = BufferedIterator(test_source['Plan Info 2'])
context = {}
context['Source'] = source

test_output = plan_info_section.scan_section(source, context)
pprint(test_output)

source = BufferedIterator(test_source['Plan Info 1'])
context = {}
context['Source'] = source

test_output2 = [row for
                row in plan_info_section.iter_section(source, context)]
pprint(test_output2)

#test_output = [processed_line for processed_line in section_iter]

#pprint(test_output)
#test_output = [parsed_line
#                for parsed_line in test_parser.parse(test_text)]


#processed_lines = tp.cascading_iterators(iter(self.test_text),
#                                            post_processing_methods)
#test_output = [processed_line for processed_line in processed_lines]

#parsing_rules = [
#    read_dvh_file.make_prescribed_dose_rule(),
#    read_dvh_file.make_date_parse_rule(),
#    read_dvh_file.make_approved_status_rule()
#    ]
#default_parser = tp.define_csv_parser('dvh_info', delimiter=':',
#                                        skipinitialspace=True)

#test_parser = tp.LineParser(parsing_rules, default_parser)
#test_output = [parsed_line
#                for parsed_line in test_parser.parse(test_text)]



#post_processing_methods=[
#    tp.trim_items,
#    tp.drop_blanks,
#    tp.merge_continued_rows
#    ]
#processed_lines = tp.cascading_iterators(iter(self.test_text),
#                                            post_processing_methods)
#test_output = [processed_line for processed_line in processed_lines]


#dvh_info_end = tp.SectionBreak(
#    name='End of DVH Info',
#    trigger=tp.Trigger(['Plan:', 'Plan sum:'])
#    )
#plan_info_end = tp.SectionBreak(
#    name='End of Plan Info',
#    trigger=tp.Trigger(['% for dose (%):']),
#    offset='After'
#    )
#structure_info_start = tp.SectionBreak(
#    name='Start of Structure Info',
#    trigger=tp.Trigger(['Structure:']),
#    offset='Before'
#    )
#structure_info_end = tp.SectionBreak(
#    name='End of Structure Info',
#    trigger=tp.Trigger(['Gradient Measure']),
#    offset='After'
#    )

#class TestSections(unittest.TestCase):
#    def setUp(self):
#        self.context = {
#            'File Name': 'trigger_test_text.txt',
#            'File Path': Path.cwd() / 'trigger_test_text.txt',
#            'Line Count': 0
#            }
#        preprocessing_methods = [clean_ascii_text]
#        parsing_rules = [read_dvh_file.make_date_parse_rule()]
#        default_parser = read_dvh_file.make_default_csv_parser()
#        line_parser = tp.LineParser(parsing_rules, default_parser)
#        post_processing_methods=[
#            tp.trim_items,
#            tp.drop_blanks,
#            tp.merge_continued_rows
#            ],


#        self.dvh_info_section = tp.Section(
#            section_name='dvh_info',
#            preprocessing=[clean_ascii_text],
#            parsing_rules=parsing_rules,
#            processed_lines=[
#                tp.trim_items,
#                tp.drop_blanks,
#                tp.merge_continued_rows
#                ],
#            output_method=tp.to_dict
#            )


#    @unittest.skip('Not Working')
#    def test_dvh_info_section(self):
#        source = (line for line in test_source_groups[1].splitlines())
#        self.context['Source'] = source
#        section_output = self.dvh_info_section.scan_section(self.context)
#        self.assertDictEqual(section_output, test_result_dicts[1])

