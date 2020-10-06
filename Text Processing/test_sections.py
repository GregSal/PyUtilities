import unittest
from pathlib import Path
import re
from file_utilities import clean_ascii_text
import Text_Processing as tp
from typing import List
from buffered_iterator import BufferedIterator
import read_dvh_file
from pprint import pprint

#%% Test Text
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

#%% Test SectionBoundaries
class TestSectionBoundaries(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.dvh_info_end = tp.SectionBreak(
            name='End of DVH Info',
            trigger=tp.Trigger(['Plan:', 'Plan sum:'])
            )
        self.plan_info_end = tp.SectionBreak(
            name='End of Plan Info',
            trigger=tp.Trigger(['% for dose (%):']),
            offset='After'
            )
        self.structure_info_start = tp.SectionBreak(
            name='Start of Structure Info',
            trigger=tp.Trigger(['Structure:']),
            offset='Before'
            )
        self.structure_info_end = tp.SectionBreak(
            name='End of Structure Info',
            trigger=tp.Trigger(['Gradient Measure']),
            offset='After'
            )
        self.test_text = [
            'Patient Name: ____, ____',
            'Patient ID: 1234567',
            'Comment: DVHs for multiple plans and plan sums',
            'Exported by: gsal',
            'Type: Cumulative Dose Volume Histogram',
            '',
            'Plan sum: Plan Sum',
            'Course: PLAN SUM',
            'Prescribed dose [cGy]: not defined',
            '% for dose (%): not defined',
            '',
            'Plan: PARR',
            'Course: C1',
            'Prescribed dose [cGy]: 5000.0',
            '% for dose (%): 100.0',
            '',
            'Structure: PRV5 SpinalCanal',
            'Approval Status: Approved',
            'Plan: Plan Sum',
            'Course: PLAN SUM',
            'Volume [cm³]: 121.5',
            'Conformity Index: N/A',
            'Gradient Measure [cm]: N/A'
            ]

    @unittest.skip('Not Working')
    def test_dvh_info_section(self):
        self.context = {}
        dvh_info_break = tp.SectionBoundaries(start_section=None,
                                              end_section=self.dvh_info_end)
        #self.assertDictEqual(section_output, test_result_dicts[1])

    def test_start_plan_info_break(self):
        plan_info_break = tp.SectionBoundaries(
            start_section=self.dvh_info_end,
            end_section=self.plan_info_end)
        source = BufferedIterator(self.test_text)
        context = self.context.copy()
        context['Source'] = source
        break_check = plan_info_break.check_start(context)
        with self.assertRaises(tp.StartSection):
            lines = [break_check(row) for row in source]

    def test_start_plan_info_break_sentinal(self):
        plan_info_break = tp.SectionBoundaries(
             start_section=self.dvh_info_end,
             end_section=self.plan_info_end)
        source = BufferedIterator(self.test_text)
        context = self.context.copy()
        context['Source'] = source
        break_check = plan_info_break.check_start(context)
        sentinel = None
        try:
            for row in source:
                test_output = break_check(row)
        except tp.StartSection as end_marker:
            sentinel = end_marker.get_context()['sentinel']
        self.assertEqual(sentinel, 'Plan sum:')

    def test_all_breaks(self):
        plan_info_break = tp.SectionBoundaries(
             start_section=self.dvh_info_end,
             end_section=self.plan_info_end)
        source = BufferedIterator(self.test_text)
        context = self.context.copy()
        context['Source'] = source
        break_check = plan_info_break.check_start(context)
        sentinel = None
        try:
            for row in source:
                test_output = break_check(row)
        except tp.StartSection as end_marker:
            sentinel = end_marker.get_context()['sentinel']
        self.assertEqual(sentinel, 'Plan sum:')


class TestProcessing(unittest.TestCase):
    def setUp(self):
        self.test_text = [
            ['Patient Name         ', ' ____, ____'],
            ['Patient ID           ', ' 1234567'],
            ['Comment              ',
             ' DVHs for multiple plans and plan sums'],
            ['Date                 ',
            'Friday, January 17, 2020 09:45:07'],
            ['Exported by          ', ' gsal'],
            ['Type                 ', ' Cumulative Dose Volume Histogram'],
            ['Description          ',
             ' The cumulative DVH displays the percentage (relative)'],
            ['                       or volume (absolute) of structures that '
             'receive a dose'],
            ['                       equal to or greater than a given dose.'],
            [''],
            ['Plan sum', ' Plan Sum'],
            ['Course', ' PLAN SUM'],
            ['Prescribed dose [cGy]', ' not defined'],
            ['% for dose (%)', ' not defined'],
            [''],
            ['Plan', ' PARR'],
            ['Course', ' C1'],
            ['Plan Status', 'Treatment Approved'],
            ['Approved on', 'Thursday, January 02, 2020 12:55:56'],
            ['Approved by', 'gsal'],
            ['Prescribed dose', '5000.0'],
            ['Prescribed dose unit', 'cGy'],
            ['% for dose (%)', ' 100.0'],
            [''],
            ['Structure', ' PRV5 SpinalCanal'],
            ['Approval Status', ' Approved'],
            ['Plan', ' Plan Sum'],
            ['Course', ' PLAN SUM'],
            ['Volume [cm³]', ' 121.5'],
            ['Dose Cover.[%]', ' 100.0'],
            ['Sampling Cover.[%]', ' 100.1'],
            ['Min Dose [cGy]', ' 36.7'],
            ['Max Dose [cGy]', ' 3670.1'],
            ['Mean Dose [cGy]', ' 891.9'],
            ['Modal Dose [cGy]', ' 44.5'],
            ['Median Dose [cGy]', ' 863.2'],
            ['STD [cGy]', ' 621.9'],
            ['NDR', ' '],
            ['Equiv. Sphere Diam. [cm]', ' 6.1'],
            ['Conformity Index', ' N/A'],
            ['Gradient Measure [cm]', ' N/A']
            ]
        self.trimmeded_output = [
            ['Patient Name','____, ____'],
            ['Patient ID','1234567'],
            ['Comment',
            'DVHs for multiple plans and plan sums'],
            ['Date',
            'Friday, January 17, 2020 09:45:07'],
            ['Exported by','gsal'],
            ['Type','Cumulative Dose Volume Histogram'],
            ['Description',
            'The cumulative DVH displays the percentage (relative)'],
            ['or volume (absolute) of structures that '
            'receive a dose'],
            ['equal to or greater than a given dose.'],
            [''],
            ['Plan sum','Plan Sum'],
            ['Course','PLAN SUM'],
            ['Prescribed dose [cGy]','not defined'],
            ['% for dose (%)','not defined'],
            [''],
            ['Plan','PARR'],
            ['Course','C1'],
            ['Plan Status','Treatment Approved'],
            ['Approved on','Thursday, January 02, 2020 12:55:56'],
            ['Approved by','gsal'],
            ['Prescribed dose','5000.0'],
            ['Prescribed dose unit','cGy'],
            ['% for dose (%)','100.0'],
            [''],
            ['Structure','PRV5 SpinalCanal'],
            ['Approval Status','Approved'],
            ['Plan','Plan Sum'],
            ['Course','PLAN SUM'],
            ['Volume [cm³]','121.5'],
            ['Dose Cover.[%]','100.0'],
            ['Sampling Cover.[%]','100.1'],
            ['Min Dose [cGy]','36.7'],
            ['Max Dose [cGy]','3670.1'],
            ['Mean Dose [cGy]','891.9'],
            ['Modal Dose [cGy]','44.5'],
            ['Median Dose [cGy]','863.2'],
            ['STD [cGy]','621.9'],
            ['NDR',''],
            ['Equiv. Sphere Diam. [cm]','6.1'],
            ['Conformity Index','N/A'],
            ['Gradient Measure [cm]','N/A']
            ]
        self.dropped_blank_output = [
            ['Patient Name','____, ____'],
            ['Patient ID','1234567'],
            ['Comment',
            'DVHs for multiple plans and plan sums'],
            ['Date',
            'Friday, January 17, 2020 09:45:07'],
            ['Exported by','gsal'],
            ['Type','Cumulative Dose Volume Histogram'],
            ['Description',
            'The cumulative DVH displays the percentage (relative)'],
            ['or volume (absolute) of structures that'
            'receive a dose'],
            ['equal to or greater than a given dose.'],
            ['Plan sum','Plan Sum'],
            ['Course','PLAN SUM'],
            ['Prescribed dose [cGy]','not defined'],
            ['% for dose (%)','not defined'],
            ['Plan','PARR'],
            ['Course','C1'],
            ['Plan Status','Treatment Approved'],
            ['Approved on','Thursday, January 02, 2020 12:55:56'],
            ['Approved by','gsal'],
            ['Prescribed dose','5000.0'],
            ['Prescribed dose unit','cGy'],
            ['% for dose (%)','100.0'],
            ['Structure','PRV5 SpinalCanal'],
            ['Approval Status','Approved'],
            ['Plan','Plan Sum'],
            ['Course','PLAN SUM'],
            ['Volume [cm³]','121.5'],
            ['Dose Cover.[%]','100.0'],
            ['Sampling Cover.[%]','100.1'],
            ['Min Dose [cGy]','36.7'],
            ['Max Dose [cGy]','3670.1'],
            ['Mean Dose [cGy]','891.9'],
            ['Modal Dose [cGy]','44.5'],
            ['Median Dose [cGy]','863.2'],
            ['STD [cGy]','621.9'],
            ['NDR',''],
            ['Equiv. Sphere Diam. [cm]','6.1'],
            ['Conformity Index','N/A'],
            ['Gradient Measure [cm]','N/A']
            ]
        self.merged_line_output = [
            ['Patient Name','____, ____'],
            ['Patient ID','1234567'],
            ['Comment',
            'DVHs for multiple plans and plan sums'],
            ['Date',
            'Friday, January 17, 2020 09:45:07'],
            ['Exported by','gsal'],
            ['Type','Cumulative Dose Volume Histogram'],
            [
            'Description',
            'The cumulative DVH displays the percentage (relative)'
            'or volume (absolute) of structures that '
            'receive a dose '
            'equal to or greater than a given dose.'
            ],
            ['Plan sum','Plan Sum'],
            ['Course','PLAN SUM'],
            ['Prescribed dose [cGy]','not defined'],
            ['% for dose (%)','not defined'],
            ['Plan','PARR'],
            ['Course','C1'],
            ['Plan Status','Treatment Approved'],
            ['Approved on','Thursday, January 02, 2020 12:55:56'],
            ['Approved by','gsal'],
            ['Prescribed dose','5000.0'],
            ['Prescribed dose unit','cGy'],
            ['% for dose (%)','100.0'],
            ['Structure','PRV5 SpinalCanal'],
            ['Approval Status','Approved'],
            ['Plan','Plan Sum'],
            ['Course','PLAN SUM'],
            ['Volume [cm³]','121.5'],
            ['Dose Cover.[%]','100.0'],
            ['Sampling Cover.[%]','100.1'],
            ['Min Dose [cGy]','36.7'],
            ['Max Dose [cGy]','3670.1'],
            ['Mean Dose [cGy]','891.9'],
            ['Modal Dose [cGy]','44.5'],
            ['Median Dose [cGy]','863.2'],
            ['STD [cGy]','621.9'],
            ['NDR',''],
            ['Equiv. Sphere Diam. [cm]','6.1'],
            ['Conformity Index','N/A'],
            ['Gradient Measure [cm]','N/A']
            ]

    def test_trim_line_processor(self):
        processed_lines = tp.cascading_iterators(
            iter(self.test_text),
            [tp.trim_items])
        test_trimmed_output = [processed_line
                               for processed_line in processed_lines]
        self.assertListEqual(test_trimmed_output, self.trimmeded_output)

    def test_dropped_blank_processor(self):
        processed_lines = tp.cascading_iterators(
            iter(self.trimmeded_output),
            [tp.drop_blanks])
        test_dropped_blank_output = [processed_line
                                     for processed_line in processed_lines]
        self.assertListEqual(test_dropped_blank_output,
                             self.dropped_blank_output)

    def test_merged_line_processor(self):
        processed_lines = tp.cascading_iterators(
            iter(self.dropped_blank_output),
            [tp.merge_continued_rows])
        test_merged_line_output = [processed_line
                                   for processed_line in processed_lines]
        test_merged_line_output = [tp.merge_continued_rows(parsed_line)
               for parsed_line in self.dropped_blank_output]
        self.assertListEqual(test_merged_line_output,
                             self.merged_line_output)

    def test_line_processor(self):
        post_processing_methods=[
            tp.trim_items,
            tp.drop_blanks,
            tp.merge_continued_rows
            ]
        processed_lines = tp.cascading_iterators(iter(self.test_text),
                                                 post_processing_methods)
        test_output = [processed_line for processed_line in processed_lines]
        self.assertListEqual(test_output, self.merged_line_output)


class TestSections(unittest.TestCase):
    def setUp(self):
        self.context = {
            'File Name': 'trigger_test_text.txt',
            'File Path': Path.cwd() / 'trigger_test_text.txt',
            'Line Count': 0
            }
        preprocessing_methods = [clean_ascii_text]
        parsing_rules = [read_dvh_file.make_date_parse_rule()]
        default_parser = read_dvh_file.make_default_csv_parser()
        line_parser = tp.LineParser(parsing_rules, default_parser)
        post_processing_methods=[
            tp.trim_items,
            tp.drop_blanks,
            tp.merge_continued_rows
            ],


        self.dvh_info_section = tp.Section(
            section_name='dvh_info',
            preprocessing=[clean_ascii_text],
            parsing_rules=parsing_rules,
            processed_lines=[
                tp.trim_items,
                tp.drop_blanks,
                tp.merge_continued_rows
                ],
            output_method=tp.to_dict
            )


    @unittest.skip('Not Working')
    def test_dvh_info_section(self):
        source = (line for line in test_source_groups[1].splitlines())
        self.context['Source'] = source
        section_output = self.dvh_info_section.scan_section(self.context)
        self.assertDictEqual(section_output, test_result_dicts[1])


if __name__ == '__main__':
    unittest.main()
