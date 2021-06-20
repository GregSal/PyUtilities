import unittest
from pathlib import Path
from functools import partial
import re
from file_utilities import clean_ascii_text
import Text_Processing as tp
from typing import List
from buffered_iterator import BufferedIterator
import read_dvh_file
from pprint import pprint
import pandas as pd


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

    def test_dvh_info_section(self):
        self.context = {}
        dvh_info_break = tp.SectionBoundaries(
            start_section=None,
            end_section=self.dvh_info_end)
        source = BufferedIterator(self.test_text)
        start_check = dvh_info_break.check_start(**self.context)
        try:
            lines = [start_check(row, source) for row in source]
        except tp.StartSection as start_marker:
            sentinel = start_marker.get_context()['Sentinel']
            self.assertTrue(sentinel)
        else:
            self.fail()
        end_check = dvh_info_break.check_end(**self.context)
        try:
            lines = [end_check(row, source) for row in source]
        except tp.StopSection as end_marker:
            sentinel = end_marker.get_context()['Sentinel']
            self.assertEqual(sentinel, 'Plan sum:')
        else:
            self.fail()

    def test_plan_info_break(self):
        plan_info_break = tp.SectionBoundaries(
            start_section=self.dvh_info_end,
            end_section=self.plan_info_end)
        source = BufferedIterator(self.test_text)
        start_check = plan_info_break.check_start(**self.context)
        try:
            lines = [start_check(row, source) for row in source]
        except tp.StartSection as start_marker:
            sentinel = start_marker.get_context()['Sentinel']
            self.assertEqual(sentinel, 'Plan sum:')
        else:
            self.fail()
        end_check = plan_info_break.check_end(**self.context)
        try:
            lines = [end_check(row, source) for row in source]
        except tp.StopSection as end_marker:
            sentinel = end_marker.get_context()['Sentinel']
            self.assertEqual(sentinel, '% for dose (%):')
        else:
            self.fail()

    def test_structure_info_break_sentinal(self):
        structure_info_break = tp.SectionBoundaries(
             start_section=self.structure_info_start,
             end_section=self.structure_info_end)
        source = BufferedIterator(self.test_text)
        start_check = structure_info_break.check_start(**self.context)
        try:
            lines = [start_check(row, source) for row in source]
        except tp.StartSection as start_marker:
            sentinel = start_marker.get_context()['Sentinel']
            self.assertEqual(sentinel, 'Structure:')
        else:
            self.fail()
        end_check = structure_info_break.check_end(**self.context)
        try:
            lines = [end_check(row, source) for row in source]
        except tp.StopSection as end_marker:
            sentinel = end_marker.get_context()['Sentinel']
            self.assertEqual(sentinel, 'Gradient Measure')
        else:
            self.fail()


    def test_dvh_data_break_sentinal(self):
        dvh_data_break = tp.SectionBoundaries(
            start_section=self.structure_info_end,
            end_section=self.structure_info_start)
        source = BufferedIterator(self.test_text)
        start_check = dvh_data_break.check_start(**self.context)
        try:
            lines = [start_check(row, source) for row in source]
        except tp.StartSection as start_marker:
            sentinel = start_marker.get_context()['Sentinel']
            self.assertEqual(sentinel, 'Gradient Measure')
        else:
            self.fail()
        end_check = dvh_data_break.check_end(**self.context)
        try:
            lines = [end_check(row, source) for row in source]
        except tp.StopSection as end_marker:
            sentinel = end_marker.get_context()['Sentinel']
            self.assertEqual(sentinel, 'Structure:')
        else:
            self.fail()


#%% Test Boundary offsets
class TestBoundaryOffsets(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        # Reader definitions
        default_parser = tp.define_csv_parser(
            'test_parser',
            delimiter=':',
            skipinitialspace=True
            )

        self.test_section_multi_line_reader = tp.SectionReader(
            default_parser=default_parser,
            post_processing_methods=[tp.trim_items,
                                     tp.drop_blanks,
                                     tp.merge_continued_rows
                                     ]
            )
        self.test_section_line_reader = tp.SectionReader(
            default_parser=default_parser,
            post_processing_methods=[tp.trim_items,
                                     tp.drop_blanks
                                     ]
            )

        # Test data
        self.test_source = [
            'Single Section',
            'Section Name:         A',
            'A Content1:  a  ',
            'A Content Long: The cumulative DVH displays the ',
            'percentage (relative) or volume (absolute) of structures ',
            'that receive a dose equal to or greater than a given dose.',
            'A Content2:b',
            '',
            'A Content3:c',
            'defghijk'
            '',
            'End Section',

            'Section With Gap',
            'Single Section',
            'Section Name:B',
            'B Content1:a',
            'B Content2:b',
            'B Content3:c',
            'End Section',
            'Skip this line',
            'B Content4:d',

            'Section Reuse',
            'Section Name:C',
            'C Content1:d',
            'C Content2:e',
            'C Content3:f',
            'C&D Content1:gg',
            'End Section',

            'Section D',
            'Section Name:D',
            'D Content1:g',
            'D Content2:h',
            'D Content3:i',
            'End Section',

            'Done Multi Section',

            'Single Section',
            'Section Name:E',
            'E Content1:1',
            'E Content2:2',
            'E Content3:3',
            'End Section',
            ]


        self.test_result = {
            'Section A': {
                'Section Name':'A',
                'A Content1':'a',
                'A Content2':'b',
                'A Content Long': 'The cumulative DVH displays the '
                    'percentage (relative) or volume (absolute) of structures '
                    'that receive a dose equal to or greater than a given dose.',
                'A Content3': 'c defghijk'
                },
            'Section B': {
                    'Section Name':'B',
                    'B Content1':'a',
                    'B Content2':'b',
                    'B Content3':'c',
                    'B Content4': 'd'
                    },
            'Section C': {
                    'Section Name':'C',
                    'C Content1':'d',
                    'C Content2':'e',
                    'C Content3':'f',
                    'C&D Content1': 'gg'
                    },
            'Section D': {
                    'Section Name':'D',
                    'D Content1':'g',
                    'D Content2':'h',
                    'D Content3':'i',
                    'C&D Content1': 'gg'
                    },
            'Section E': {
                'Section Name':'E',
                'E Content1':'1',
                'E Content2':'2',
                'E Content3':'3'
                }
            }

        self.context = {}

    def test_section_break_after_before(self):
        section_start_after = tp.SectionBreak(
            name='Single Section After',
            trigger=tp.Trigger('Single Section'),
            offset='After'
            )
        section_end_before = tp.SectionBreak(
            name='Single Section Before',
            trigger=tp.Trigger('End'),
            offset='Before'
            )
        section_break_after_before = tp.SectionBoundaries(
            start_section=section_start_after,
            end_section=section_end_before
            )
        test_section = tp.Section(
            section_name='Test Section',
            boundaries=section_break_after_before,
            reader=self.test_section_multi_line_reader,
            aggregate=tp.to_dict
            )
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        **self.context)
        self.assertDictEqual(test_output, self.test_result['Section A'])
        get_next = iter(source)
        next_item = get_next.__next__()
        self.assertEqual(next_item, 'End Section')

    def test_section_break_gap(self):
        section_start_gap = tp.SectionBreak(
            name='Section With Gap',
            trigger=tp.Trigger('Section With Gap'),
            offset=1
            )
        section_end_skip_line = tp.SectionBreak(
            name='Section End Skip Line',
            trigger=tp.Trigger('End'),
            offset=2
            )
        section_break_gap = tp.SectionBoundaries(
            start_section=section_start_gap,
            end_section=section_end_skip_line
            )
        test_section = tp.Section(
            section_name='Test Section',
            boundaries=section_break_gap,
            reader=self.test_section_line_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        **self.context)
        self.assertDictEqual(test_output, self.test_result['Section B'])
        get_next = iter(source)
        next_item = get_next.__next__()
        self.assertEqual(next_item, 'Section Reuse')

    def test_section_break_reuse(self):
        section_start_reuse = tp.SectionBreak(
            name='Section Start Before',
            trigger=tp.Trigger('C Content1:d'),
            offset=-2
            )
        section_end_skip_line = tp.SectionBreak(
            name='Section End Reuse',
            trigger=tp.Trigger('Section D'),
            offset=-3
            )
        section_break_reuse = tp.SectionBoundaries(
            start_section=section_start_reuse,
            end_section=section_end_skip_line
            )

        test_section = tp.Section(
            section_name='Test Section',
            boundaries=section_break_reuse,
            reader=self.test_section_line_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )
        source = BufferedIterator(self.test_source)

        test_output = test_section.read(source, start_search=True,
                                        **self.context)
        self.assertDictEqual(test_output, self.test_result['Section C'])
        get_next = iter(source)
        next_item = get_next.__next__()
        self.assertEqual(next_item, 'C&D Content1:gg')
if __name__ == '__main__':
    unittest.main()
