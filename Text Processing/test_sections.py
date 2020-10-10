import unittest
from pathlib import Path
import re
from file_utilities import clean_ascii_text
import Text_Processing as tp
from typing import List
from buffered_iterator import BufferedIterator
import read_dvh_file
from pprint import pprint
import pandas as pd

##%% Test SectionBoundaries
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
             ' The cumulative DVH displays the percentage (relative) '],
            ['                       or volume (absolute) of structures that '
             'receive a dose '],
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
            ['or volume (absolute) of structures that '
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
            ['Description',
            'The cumulative DVH displays the percentage (relative) '
            'or volume (absolute) of structures that '
            'receive a dose equal to or greater than a given dose.'
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
        self.test_source = {
            'DVH Info': [
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
                ],
            'Plan Info 1': [
                'Plan sum: Plan Sum',
                'Course: PLAN SUM',
                'Prescribed dose [cGy]: not defined',
                '% for dose (%): not defined',
                ''
                ],
            'Plan Info 2': [
                'Plan: PARR',
                'Course: C1',
                'Plan Status: Treatment Approved Thursday, January 02, '
                '2020 12:55:56 by gsal',
                'Prescribed dose [cGy]: 5000.0',
                '% for dose (%): 100.0',
                ''
                ],
            'Structure': [
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
                ],
            'DVH': [
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
                ]
            }

        self.test_result = {
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
            'Plan Info 1': {
                    'Plan sum': 'Plan Sum',
                    'Course': 'PLAN SUM',
                    'Prescribed dose': '',
                    'Prescribed dose unit': '',
                    '% for dose (%)': 'not defined'
                    },
            'Plan Info 2': {
                    'Plan': 'PARR',
                    'Course': 'C1',
                    'Plan Status': 'Treatment Approved',
                    'Approved on': 'Thursday, January 02, 2020 12:55:56',
                    'Approved by': 'gsal',
                    'Prescribed dose': 5000.0,
                    'Prescribed dose unit': 'cGy',
                    '% for dose (%)': 100.0
                    },
            'Structure': {
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
                    },
            'DVH': pd.DataFrame({'Dose [cGy]': [0, 1, 2, 3, 4, 5, 3667, 3668,
                                                3669, 3670],
                'Ratio of Total Structure Volume [%]': [100, 100, 100, 100,
                                                        100, 100,
                                                        4.23876e-005,
                                                        2.87336e-005,
                                                        1.50797e-005,
                                                        1.4257e-006]})
            }

        self.context = {
            'File Name': 'trigger_test_text.txt',
            'File Path': Path.cwd() / 'trigger_test_text.txt',
            'Line Count': 0
            }
        self.default_parser = tp.define_csv_parser('dvh_info', delimiter=':',
                                                   skipinitialspace=True)

    def test_dvh_info_section(self):
        dvh_info_section = tp.Section(
            section_name='DVH Info',
            preprocessing_methods=[clean_ascii_text],
            parsing_rules=[read_dvh_file.make_date_parse_rule()],
            default_parser=self.default_parser,
            post_processing_methods=[tp.trim_items, tp.drop_blanks,
                                     tp.merge_continued_rows],
            output_method=tp.to_dict)
        # scan_section
        source = BufferedIterator(self.test_source['DVH Info'])
        self.context['Source'] = source
        test_output = dvh_info_section.scan_section(source, self.context)

        self.assertDictEqual(test_output, self.test_result['DVH Info'])

    def test_plan_info1_section(self):
        dvh_info_section = tp.Section(
            section_name='Plan Info 1',
            preprocessing_methods=[clean_ascii_text],
            parsing_rules=[read_dvh_file.make_prescribed_dose_rule(),
                           read_dvh_file.make_approved_status_rule()],
            default_parser=self.default_parser,
            post_processing_methods=[tp.trim_items, tp.drop_blanks,
                                     tp.convert_numbers],
            output_method=tp.to_dict)
        # scan_section
        source = BufferedIterator(self.test_source['Plan Info 1'])
        self.context['Source'] = source
        test_output = dvh_info_section.scan_section(source, self.context)

        self.assertDictEqual(test_output, self.test_result['Plan Info 1'])


    def test_plan_info2_section(self):
        dvh_info_section = tp.Section(
            section_name='Plan Info 2',
            preprocessing_methods=[clean_ascii_text],
            parsing_rules=[read_dvh_file.make_prescribed_dose_rule(),
                           read_dvh_file.make_approved_status_rule()],
            default_parser=self.default_parser,
            post_processing_methods=[tp.trim_items, tp.drop_blanks,
                                     tp.convert_numbers],
            output_method=tp.to_dict)
        # scan_section
        source = BufferedIterator(self.test_source['Plan Info 2'])
        self.context['Source'] = source
        test_output = dvh_info_section.scan_section(source, self.context)

        self.assertDictEqual(test_output, self.test_result['Plan Info 2'])


    def test_structure_section(self):
        dvh_info_section = tp.Section(
            section_name='Structure',
            preprocessing_methods=[clean_ascii_text],
            parsing_rules=[],
            default_parser=self.default_parser,
            post_processing_methods=[tp.trim_items, tp.drop_blanks,
                                     tp.convert_numbers],
            output_method=tp.to_dict)
        # scan_section
        source = BufferedIterator(self.test_source['Structure'])
        self.context['Source'] = source
        test_output = dvh_info_section.scan_section(source, self.context)

        self.assertDictEqual(test_output, self.test_result['Structure'])


    @unittest.skip('Not Working')
    def test_dvh_section(self):
        dvh_info_section = tp.Section(
            section_name='DVH',
            preprocessing_methods=[clean_ascii_text],
            parsing_rules=[read_dvh_file.make_date_parse_rule()],
            default_parser=self.default_parser,
            post_processing_methods=[tp.trim_items, tp.drop_blanks,
                                     tp.merge_continued_rows],
            output_method=tp.to_dict)
        # scan_section
        source = BufferedIterator(self.test_source['DVH'])
        self.context['Source'] = source
        test_output = dvh_info_section.scan_section(source, self.context)

        self.assertDictEqual(test_output, self.test_result['DVH'])




if __name__ == '__main__':
    unittest.main()
