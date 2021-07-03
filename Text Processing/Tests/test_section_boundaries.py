import unittest
import Text_Processing as tp
from buffered_iterator import BufferedIterator


#%% Test Data
DVH_TEST_TEXT = [
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
        '',
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

# Test data
GENERIC_TEST_TEXT = [
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



#%% Test SectionBoundaries
class Test_DVH_Info_SectionBoundaries(unittest.TestCase):
    def setUp(self):
        self.context = {}
        dvh_info_end = tp.SectionBreak(
            name='End of DVH Info',
            trigger=tp.Trigger(['Plan:', 'Plan sum:'])
            )
        dvh_info_section = tp.Section(
            start_section=None,
            end_section=dvh_info_end)
        dvh_info_section.source = BufferedIterator(DVH_TEST_TEXT)
        self.test_section = dvh_info_section

    def test_dvh_info_section_start_sentinel(self):
        start_check = self.test_section.section_scan('Start')
        output = [row for row in start_check]  # pylint: disable=unused-variable
        sentinel = self.test_section.context['Sentinel']
        self.assertTrue(sentinel)

    def test_dvh_info_section_start_empty_list(self):
        start_check = self.test_section.section_scan('Start')
        skipped_lines = [row for row in start_check]
        self.assertListEqual(skipped_lines, [])

    def test_dvh_info_section_end_sentinel(self):
        end_check = self.test_section.section_scan('End')
        output = [row for row in end_check]  # pylint: disable=unused-variable
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, 'Plan sum:')

    def test_dvh_info_section_end_lines(self):
        end_check = self.test_section.section_scan('End')
        scanned_lines = [row for row in end_check]
        self.assertListEqual(DVH_TEST_TEXT[:10], scanned_lines)

class Test_Plan_Info_SectionBoundaries(unittest.TestCase):
    def setUp(self):
        self.context = {}
        dvh_info_end = tp.SectionBreak(
            name='End of DVH Info',
            trigger=tp.Trigger(['Plan:', 'Plan sum:'])
            )
        plan_info_end = tp.SectionBreak(
            name='End of Plan Info',
            trigger=tp.Trigger(['% for dose (%):']),
            offset='After'
            )
        plan_info_section = tp.Section(
            start_section=dvh_info_end,
            end_section=plan_info_end)
        plan_info_section.source = BufferedIterator(DVH_TEST_TEXT)
        self.test_section = plan_info_section

    def test_plan_info_section_start_sentinel(self):
        start_check = self.test_section.section_scan('Start')
        output = [row for row in start_check]  # pylint: disable=unused-variable
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, 'Plan sum:')

    def test_plan_info_section_start_skipped_lines(self):
        start_check = self.test_section.section_scan('Start')
        skipped_lines = [row for row in start_check]  # pylint: disable=unused-variable
        self.assertListEqual(DVH_TEST_TEXT[:10], skipped_lines)

    def test_plan_info_section_end_sentinel(self):
        end_check = self.test_section.section_scan('End')
        output = [row for row in end_check]  # pylint: disable=unused-variable
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, '% for dose (%):')

    def test_dvh_info_section_end_lines(self):
        start_check = self.test_section.section_scan('Start')
        skipped_lines = [row for row in start_check]  # pylint: disable=unused-variable
        end_check = self.test_section.section_scan('End')
        scanned_lines = [row for row in end_check]
        self.assertListEqual(DVH_TEST_TEXT[10:14], scanned_lines)


class Test_Plan_Info_SectionBoundaries(unittest.TestCase):
    def setUp(self):
        self.context = {}
        dvh_info_end = tp.SectionBreak(
            name='End of DVH Info',
            trigger=tp.Trigger(['Plan:', 'Plan sum:'])
            )
        plan_info_end = tp.SectionBreak(
            name='End of Plan Info',
            trigger=tp.Trigger(['% for dose (%):']),
            offset='After'
            )
        plan_info_section = tp.Section(
            start_section=dvh_info_end,
            end_section=plan_info_end)
        plan_info_section.source = BufferedIterator(DVH_TEST_TEXT)
        self.test_section = plan_info_section


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


if __name__ == '__main__':
    unittest.main()