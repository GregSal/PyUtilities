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



if __name__ == '__main__':
    unittest.main()
