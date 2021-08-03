import unittest
from functools import partial
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
        '',
        'Plan: PARR',
        'Course: C1',
        'Plan Status: Treatment Approved Thursday, January 02, '
        '2020 12:55:56 by gsal',
        'Prescribed dose [cGy]: 5000.0',
        '% for dose (%): 100.0',
        '',
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
        '',
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

GENERIC_TEST_RESULTS = {
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


#%% Test Section Boundaries
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
        self.test_section = dvh_info_section

    def test_dvh_info_section_start_sentinel(self):
        self.test_section.initialize(DVH_TEST_TEXT)
        sentinel = self.test_section.context['Sentinel']
        self.assertTrue(sentinel)

    def test_dvh_info_section_start_empty_list(self):
        self.test_section.initialize(DVH_TEST_TEXT)
        skipped_lines = self.test_section.context['Skipped Lines']
        self.assertListEqual(skipped_lines, [])

    def test_dvh_info_section_end_sentinel(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        output = [row for row in end_check]  # pylint: disable=unused-variable
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, 'Plan sum:')

    def test_dvh_info_section_end_lines(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
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
        self.test_section = plan_info_section

    def test_plan_info_section_start_sentinel(self):
        self.test_section.initialize(DVH_TEST_TEXT)
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, 'Plan sum:')

    def test_plan_info_section_start_skipped_lines(self):
        self.test_section.initialize(DVH_TEST_TEXT)
        skipped_lines = self.test_section.context['Skipped Lines']
        self.assertListEqual(DVH_TEST_TEXT[:10], skipped_lines)

    def test_plan_info_section_end_sentinel(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        output = [row for row in end_check]  # pylint: disable=unused-variable
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, '% for dose (%):')

    def test_dvh_info_section_end_scan(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        scanned_lines = [row for row in end_check]
        self.assertListEqual(DVH_TEST_TEXT[10:14], scanned_lines)

    def test_dvh_info_section_end_lines(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        scanned_lines = [row for row in end_check]
        self.assertListEqual(DVH_TEST_TEXT[10:14], scanned_lines)


class Test_structure_Info_SectionBoundaries(unittest.TestCase):
    def setUp(self):
        structure_info_start = tp.SectionBreak(
            name='Start of Structure Info',
            trigger=tp.Trigger(['Structure:']),
            offset='Before'
            )
        structure_info_end = tp.SectionBreak(
            name='End of Structure Info',
            trigger=tp.Trigger(['Gradient Measure']),
            offset='After'
            )
        structure_info_section = tp.Section(start_section=structure_info_start,
                                            end_section=structure_info_end)
        self.test_section = structure_info_section

    def test_structure_info_break_start_sentinal(self):
        self.test_section.initialize(DVH_TEST_TEXT)
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, 'Structure:')

    def test_structure_info_break_start_skipped_lines(self):
        self.test_section.initialize(DVH_TEST_TEXT)
        skipped_lines = self.test_section.context['Skipped Lines']
        self.assertListEqual(DVH_TEST_TEXT[:21], skipped_lines)

    def test_structure_info_break_end_sentinal(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        scanned_lines = [row for row in end_check]
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, 'Gradient Measure')

    def test_structure_info_break_end_skipped_scan(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        scanned_lines = [row for row in end_check]
        self.assertListEqual(DVH_TEST_TEXT[21:38], scanned_lines)

    def test_structure_info_break_end_skipped_lines(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        scanned_lines = [row for row in end_check]
        self.assertListEqual(DVH_TEST_TEXT[21:38], scanned_lines)


class Test_dvh_data_SectionBoundaries(unittest.TestCase):
    def setUp(self):
        structure_info_start = tp.SectionBreak(
            name='Start of Structure Info',
            trigger=tp.Trigger(['Structure:']),
            offset='Before'
            )
        structure_info_end = tp.SectionBreak(
            name='End of Structure Info',
            trigger=tp.Trigger(['Gradient Measure']),
            offset='After'
            )
        dvh_data_section = tp.Section(start_section=structure_info_end,
                                      end_section=structure_info_start)
        self.test_section = dvh_data_section

    def test_dvh_data_break_start_sentinal(self):
        self.test_section.initialize(DVH_TEST_TEXT)
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, 'Gradient Measure')

    def test_dvh_data_break_start_skipped_lines(self):
        self.test_section.initialize(DVH_TEST_TEXT)
        skipped_lines = self.test_section.context['Skipped Lines']
        self.assertListEqual(DVH_TEST_TEXT[:38], skipped_lines)

    def test_dvh_data_break_end_sentinal(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        scanned_lines = [row for row in end_check]
        sentinel = self.test_section.context['Sentinel']
        self.assertEqual(sentinel, 'Structure:')

    def test_dvh_data_break_end_skipped_lines(self):
        end_check = self.test_section.scan(DVH_TEST_TEXT)
        scanned_lines = [row for row in end_check]
        self.assertListEqual(DVH_TEST_TEXT[38:51], scanned_lines)


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

        self.test_section_multi_line_reader = tp.SectionProcessor(
            default_parser=default_parser,
            post_processing_methods=[tp.trim_items,
                                     tp.drop_blanks,
                                     tp.merge_continued_rows
                                     ]
            )
        self.test_section_line_reader = tp.SectionProcessor(
            default_parser=default_parser,
            post_processing_methods=[tp.trim_items,
                                     tp.drop_blanks
                                     ]
            )
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
        test_section = tp.Section(
            section_name='Test Section',
            start_section=section_start_after,
            end_section=section_end_before,
            processor=self.test_section_multi_line_reader,
            aggregate=tp.to_dict
            )
        source = BufferedIterator(GENERIC_TEST_TEXT)
        test_output = test_section.read(source, start_search=True)
        self.assertDictEqual(test_output, GENERIC_TEST_RESULTS['Section A'])
        next_item = test_section.source.look_ahead()
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
        test_section = tp.Section(
            section_name='Test Section',
            start_section=section_start_gap,
            end_section=section_end_skip_line,
            processor=self.test_section_line_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )
        source = BufferedIterator(GENERIC_TEST_TEXT)
        test_output = test_section.read(source, start_search=True)
        self.assertDictEqual(test_output, GENERIC_TEST_RESULTS['Section B'])
        next_item = test_section.source.look_ahead()
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
        test_section = tp.Section(
            section_name='Test Section',
            start_section=section_start_reuse,
            end_section=section_end_skip_line,
            processor=self.test_section_line_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )
        source = BufferedIterator(GENERIC_TEST_TEXT)

        test_output = test_section.read(source, start_search=True)
        self.assertDictEqual(test_output, GENERIC_TEST_RESULTS['Section C'])
        next_item = test_section.source.look_ahead()
        self.assertEqual(next_item, 'C&D Content1:gg')
if __name__ == '__main__':
    unittest.main()