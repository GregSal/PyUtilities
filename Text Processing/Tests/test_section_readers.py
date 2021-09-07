import unittest
from pathlib import Path
import csv
import Text_Processing as tp
from buffered_iterator import BufferedIterator
import read_dvh_file
import pandas as pd

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
        self.trimmed_output = [
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
        processor = tp.ProcessingMethods([tp.trim_items])
        test_trimmed_output = list()
        for line in self.test_text:
            processed_lines = processor.process(line, {})
            if processed_lines:
                if tp.true_iterable(processed_lines):
                    test_trimmed_output.extend(processed_lines)
        self.assertListEqual(test_trimmed_output, self.trimmed_output)

    def test_trim_line_reader(self):
        processor = tp.ProcessingMethods([tp.trim_items])
        test_trimmed_output = processor.reader(self.test_text)
        self.assertListEqual(test_trimmed_output, self.trimmed_output)

    def test_dropped_blank_processor(self):
        processor = tp.ProcessingMethods([tp.drop_blanks])
        test_dropped_blank_output = processor.read(iter(self.trimmed_output))
        self.assertListEqual(test_dropped_blank_output,
                             self.dropped_blank_output)

    def test_merged_line_processor(self):
        processor = tp.ProcessingMethods([tp.merge_continued_rows])
        source = iter(self.dropped_blank_output)
        test_merged_line_output = processor.read(source)
        self.assertListEqual(test_merged_line_output,
                             self.merged_line_output)

    def test_line_processor(self):
        processor = tp.ProcessingMethods([
            tp.trim_items,
            tp.drop_blanks,
            tp.merge_continued_rows
            ])
        test_output = processor.read(iter(self.test_text))
        self.assertListEqual(test_output, self.merged_line_output)


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.source = [
            'Patient Name         : ____, ____',
            'Patient ID           : 1234567',
            'Comment              : DVHs for multiple plans and plan sums',
            'Date                 : Friday, January 17, 2020 09:45:07',
            'Exported by          : gsal',
            'Type                 : Cumulative Dose Volume Histogram'
            ]
        self.line = 'Patient Name         : ____, ____'
        self.test_result = {
            'First Line': ['Patient Name         ', '____, ____'],
            'Default Parse': [
                ['Patient Name         ', '____, ____'],
                ['Patient ID           ', '1234567'],
                ['Comment              ',
                 'DVHs for multiple plans and plan sums'],
                ['Date                 ',
                 'Friday, January 17, 2020 09',
                 '45', '07'],
                ['Exported by          ', 'gsal'],
                ['Type                 ', 'Cumulative Dose Volume Histogram']
                ],
            'dvh_info Parse': [
                ['Patient Name         ', '____, ____'],
                ['Patient ID           ', '1234567'],
                ['Comment              ',
                 'DVHs for multiple plans and plan sums'],
                ['Date                 ',
                 ' Friday, January 17, 2020 09:45:07'],
                ['Exported by          ', 'gsal'],
                ['Type                 ', 'Cumulative Dose Volume Histogram']
                ]
            }
        parameters = dict(
            delimiter=':',
            doublequote=True,
            quoting=csv.QUOTE_MINIMAL,
            quotechar='"',
            escapechar=None,
            lineterminator='\r\n',
            skipinitialspace=True,
            strict=False
            )
        csv.register_dialect('dvh_info', parameters)
        self.default_parser = tp.sig_match(tp.define_csv_parser(
            'dvh_info',
            delimiter=':',
            skipinitialspace=True))
        self.dvh_info_reader = tp.ProcessingMethods([tp.RuleSet(
            [read_dvh_file.make_date_parse_rule()],
            default=tp.define_csv_parser('dvh_info', delimiter=':',
                                         skipinitialspace=True))])

    def test_csv_line_parse(self):
        test_output = [txt for txt in self.default_parser(self.line, {})][0]
        self.assertListEqual(test_output, self.test_result['First Line'])

    def test_dvh_info_line_parse(self):
        test_output = self.dvh_info_reader.process(self.line)
        self.assertListEqual(test_output, self.test_result['First Line'])

    def test_csv_parse(self):
        reader = self.default_parser(self.source, {})
        test_output = [text_line for text_line in reader]
        self.assertListEqual(test_output, self.test_result['Default Parse'])

    def test_dvh_info_parse(self):
        test_output = self.dvh_info_reader.read(self.source)
        self.assertListEqual(test_output, self.test_result['dvh_info Parse'])


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

    def test_dvh_info_reader(self):
        dvh_info_reader = tp.ProcessingMethods([
            tp.clean_ascii_text,
            tp.RuleSet([read_dvh_file.make_date_parse_rule()],
                       default=self.default_parser),
            tp.trim_items,
            tp.drop_blanks,
            tp.merge_continued_rows
            ])
        # scan_section
        source = BufferedIterator(self.test_source['DVH Info'])
        reader = dvh_info_reader.reader(source, self.context)
        test_output = tp.to_dict(reader)
        self.assertDictEqual(test_output, self.test_result['DVH Info'])

    def test_plan_info1_read(self):
        plan_info_reader = tp.ProcessingMethods([
            tp.clean_ascii_text,
            tp.RuleSet([read_dvh_file.make_prescribed_dose_rule(),
                     read_dvh_file.make_approved_status_rule()],
                       default=self.default_parser),
            tp.trim_items,
            tp.drop_blanks,
            tp.convert_numbers
            ])
        # scan_section
        source = BufferedIterator(self.test_source['Plan Info 1'])
        reader = plan_info_reader.reader(source, self.context)
        test_output = tp.to_dict(reader)
        self.assertDictEqual(test_output, self.test_result['Plan Info 1'])


    def test_plan_info2_read(self):
        plan_info_reader = tp.ProcessingMethods([
            tp.clean_ascii_text,
            tp.RuleSet([read_dvh_file.make_prescribed_dose_rule(),
                     read_dvh_file.make_approved_status_rule()],
                       default=self.default_parser),
            tp.trim_items,
            tp.drop_blanks,
            tp.convert_numbers
            ])
        # scan_section
        source = BufferedIterator(self.test_source['Plan Info 2'])
        reader = plan_info_reader.reader(source, self.context)
        test_output = tp.to_dict(reader)
        self.assertDictEqual(test_output, self.test_result['Plan Info 2'])


    def test_structure_reader(self):
        structure_reader = tp.ProcessingMethods([
            tp.clean_ascii_text,
            self.default_parser,
            tp.trim_items,
            tp.drop_blanks,
            tp.convert_numbers
            ])
        # scan_section
        source = BufferedIterator(self.test_source['Structure'])
        reader = structure_reader.reader(source, self.context)
        test_output = tp.to_dict(reader)
        self.assertDictEqual(test_output, self.test_result['Structure'])


    def test_dvh_reader(self):
        dvh_data_reader = tp.ProcessingMethods([
            tp.clean_ascii_text,
            tp.define_fixed_width_parser(widths=10),
            tp.trim_items,
            tp.drop_blanks,
            tp.convert_numbers
            ])
        # scan_section
        source = BufferedIterator(self.test_source['DVH'])
        reader = dvh_data_reader.reader(source, self.context)
        test_output = tp.to_dataframe(reader)
        self.assertDictEqual(test_output.to_dict(),
                             self.test_result['DVH'].to_dict())


if __name__ == '__main__':
    unittest.main()
