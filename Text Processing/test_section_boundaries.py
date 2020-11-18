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

    def test_dvh_info_section(self):
        self.context = {}
        dvh_info_break = tp.SectionBoundaries(
            start_section=None,
            end_section=self.dvh_info_end)
        source = BufferedIterator(self.test_text)
        context = self.context.copy()
        context['Source'] = source
        break_check = dvh_info_break.check_start(context)
        try:
            lines = [break_check(row) for row in source]
        except tp.StartSection as end_marker:
            pass
        else:
            self.fail()

    def test_start_plan_info_break(self):
        plan_info_break = tp.SectionBoundaries(
            start_section=self.dvh_info_end,
            end_section=self.plan_info_end)
        source = BufferedIterator(self.test_text)
        context = self.context.copy()
        context['Source'] = source
        break_check = plan_info_break.check_start(context)
        try:
            lines = [break_check(row) for row in source]
        except tp.StartSection as end_marker:
            pass
        else:
            self.fail()

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


if __name__ == '__main__':
    unittest.main()
