import unittest
from pathlib import Path
import re
from file_utilities import clean_ascii_text
import Text_Processing as tp
from typing import List

#%% Test Text
from pprint import pprint
test_source_groups = [
    [
        ['Patient Name         ', ' ____, ____'],
        ['Patient ID           ', ' 1234567'],
        ['Comment              ', ' DVHs for multiple plans and plan sums'],
        ['Date                 ', ' Friday, January 17, 2020 09:45:07'],
        ['Exported by          ', ' gsal'],
        ['Type                 ', ' Cumulative Dose Volume Histogram'],
        ['Description          ', ' The cumulative DVH displays the percentage (relative)'],
        ['    '],
        [                          'or volume (absolute) of structures that receive a dose'],
        [                          'equal to or greater than a given dose.']
        ], (
    'Patient Name         : ____, ____\r\n'
    'Patient ID           : 1234567\r\n'
    'Comment              : DVHs for multiple plans and plan sums\r\n'
    'Date                 : Friday, January 17, 2020 09:45:07\r\n'
    'Exported by          : gsal\r\n'
    'Type                 : Cumulative Dose Volume Histogram\r\n'
    'Description          : The cumulative DVH displays the percentage (relative)\r\n'
    '                       or volume (absolute) of structures that receive a dose\r\n'
    '                       equal to or greater than a given dose.\r\n'
    '\r\n'
    'Plan sum: Plan Sum\r\n'
    'Course: PLAN SUM\r\n'
    ), (
    'Plan sum: Plan Sum\r\n'
    'Course: PLAN SUM\r\n'
    'Prescribed dose [cGy]: not defined\r\n'
    '% for dose (%): not defined\r\n'
    '\r\n'
    'Plan: PARR\r\n'
    ), (
    'Plan: PARR\r\n'
    'Course: C1\r\n'
    'Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal\r\n'
    'Prescribed dose [cGy]: 5000.0\r\n'
    '% for dose (%): 100.0\r\n'
    '\r\n'
    'Structure: PRV5 SpinalCanal\r\n'
    )]
#pprint(test_source_groups[0].splitlines())
test_result_dicts = [
    [
        ['Patient Name', '____, ____'],
        ['Patient ID ', '1234567'],
        ['Comment', 'DVHs for multiple plans and plan sums'],
        ['Date', ' Friday, January 17, 2020 09:45:07'],
        ['Exported by', 'gsal'],
        ['Type', 'Cumulative Dose Volume Histogram'],
        ['Description', ('The cumulative DVH displays the percentage (relative)\n'
                         'or volume (absolute) of structures that receive a dose\n'
                         'equal to or greater than a given dose.')]
        ],
    {'Patient Name': '____, ____',
     'Patient ID': '1234567',
     'Comment': 'DVHs for multiple plans and plan sums',
     'Date': 'Friday, January 17, 2020 09:45:07',
     'Exported by': 'gsal',
     'Type': 'Cumulative Dose Volume Histogram',
     'Description': ('The cumulative DVH displays the percentage (relative) '
                     'or volume (absolute) of structures that receive a dose '
                     'equal to or greater than a given dose.')
     },
    {'Plan sum': 'Plan Sum',
     'Course': 'PLAN SUM',
     'Prescribed dose': '',
     'Prescribed dose Unit': '',
     '% for dose (%)': 'not defined'
     },
    {'Plan': 'PARR',
     'Course': 'C1',
     'Plan Status': 'Treatment Approved',
     'Approved on': 'Thursday, January 02, 2020 12:55:56',
     'Approved by': 'gsal',
     'Prescribed dose': 5000.0,
     'Prescribed dose Unit': 'cGy',
     '% for dose (%)': 100.0}
     ]




#%%  dvh_info section tests
class TestSections(unittest.TestCase):
    def setUp(self):
        self.context = {
            'File Name': 'trigger_test_text.txt',
            'File Path': Path.cwd() / 'trigger_test_text.txt',
            'Line Count': 0
            }

        dvh_info_break = [tp.SectionBreak(tp.Trigger(['Plan:', 'Plan sum:']),
                                          name='dvh_info')]
        dvh_info_parsing_rules = [
            make_date_parse_rule(),
            make_default_csv_rule()
            ]

        self.dvh_info_section = tp.Section(
            section_name='dvh_info',
            preprocessing=[clean_ascii_text],
            break_rules=dvh_info_break,
            parsing_rules=dvh_info_parsing_rules,
            processed_lines=[
                tp.trim_items,
                tp.drop_blanks,
                tp.merge_continued_rows
                ],
            output_method=tp.to_dict
            )

    @unittest.skip('Not Working')
    def test_simple_cascading_iterators(self):
        processed_lines = [
            tp.trim_items,
            tp.drop_blanks
            ]
        source = (line for line in test_source_groups[0][:6])
        line_processor = tp.cascading_iterators(source, processed_lines)
        test_output = [row for row in line_processor]
        self.assertListEqual(test_output, test_result_dicts[0][:6])
        cleaned_lines = tp.cascading_iterators(source, processed_lines)

    def test_one_item_cascading_iterators(self):
        preprocessing = [clean_ascii_text],
        source = (line for line in test_source_groups[1][:2])
        line_processor = tp.cascading_iterators(source, preprocessing)
        test_output = [row for row in line_processor]
        self.assertListEqual(test_output, test_source_groups[1][:2])
        cleaned_lines = tp.cascading_iterators(source, preprocessing)

    @unittest.skip('Not Working')
    def test_cascading_iterators(self):
        processed_lines = [
            tp.trim_items,
            tp.drop_blanks,
            tp.merge_continued_rows
            ]
        source = (line for line in test_source_groups[0])
        line_processor = tp.cascading_iterators(source, processed_lines)
        test_output = [row for row in line_processor]
        self.assertListEqual(test_output, test_result_dicts[0])

    @unittest.skip('Not Working')
    def test_dvh_info_section(self):
        source = (line for line in test_source_groups[1].splitlines())
        self.context['Source'] = source
        section_output = self.dvh_info_section.scan_section(self.context)
        self.assertDictEqual(section_output, test_result_dicts[1])


if __name__ == '__main__':
    unittest.main()
