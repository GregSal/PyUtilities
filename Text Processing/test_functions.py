import unittest
from itertools import chain
from typing import List
from file_utilities import clean_ascii_text
import Text_Processing as tp
import read_dvh_file


class Test_cascading_iterators(unittest.TestCase):
    def test_simple_cascading_iterators(self):
        def ml(x): return x*10
        def dv(x): return x/5

        def skip_odd(num_list):
            for i in num_list:
                if i % 2 == 0:
                    yield i

        source = range(5)
        test_iter = tp.cascading_iterators(source, [skip_odd, ml, dv])
        test_output = [i for i in test_iter]
        self.assertListEqual(test_output, [0.0, 4.0, 8.0])


class TestParsers(unittest.TestCase):
    def test_csv_parser(self):
        test_text = 'Part 1,"Part 2a, Part 2b"'
        expected_output = [['Part 1', 'Part 2a, Part 2b']]
        test_parser = tp.define_csv_parser(name='Default csv')
        test_output = test_parser(test_text)
        self.assertListEqual(test_output, expected_output)

    def test_default_csv_parser(self):
        test_text = [
            'Export Version:,1',
            '================',
            '',
            'IMSure Version:,3.7.2',
            'Exported Date:,03.09.2020  14:20',
            'User:,Superuser',
            'Patient:,"____, ----"',
            'Patient ID:,0123456',
            ]
        expected_output = [
            ['Export Version:', '1'],
            ['================'],
            [],
            ['IMSure Version:', '3.7.2'],
            ['Exported Date:', '03.09.2020  14:20'],
            ['User:', 'Superuser'],
            ['Patient:', '____, ----'],
            ['Patient ID:', '0123456']
            ]
        test_parser = tp.define_csv_parser(name='Default')
        test_iter = (test_parser(line) for line in test_text)
        test_output = [row for row in chain.from_iterable(test_iter)]
        self.assertListEqual(test_output, expected_output)

    def test_list_csv_parser(self):
        test_text = [
            'Patient Name:     ____, ____',
            'Patient ID:   1234567',
            'Comment: DVHs for multiple plans and plan sums',
            'Date: Friday, January 17, 2020 09:45:07',
            'Exported by:    gsal',
            'Type: Cumulative Dose Volume Histogram',
            'Description:The cumulative DVH displays the percentage',
            'or volume (absolute) of structures that receive a dose',
            'equal to or greater than a given dose.',
            'Plan sum: Plan Sum',
            'Course: PLAN SUM',
            'Prescribed dose [cGy]: not defined',
            '% for dose (%): not defined'
            ]
        expected_output = [
            ['Patient Name', '____, ____'],
            ['Patient ID', '1234567'],
            ['Comment', 'DVHs for multiple plans and plan sums'],
            ['Date', 'Friday, January 17, 2020 09', '45', '07'],
            ['Exported by', 'gsal'],
            ['Type', 'Cumulative Dose Volume Histogram'],
            ['Description', 'The cumulative DVH displays the percentage'],
            ['or volume (absolute) of structures that receive a dose'],
            ['equal to or greater than a given dose.'],
            ['Plan sum', 'Plan Sum'],
            ['Course', 'PLAN SUM'],
            ['Prescribed dose [cGy]', 'not defined'],
            ['% for dose (%)', 'not defined'],
            ]
        stl = ''
        ctx = {}
        test_parser = tp.define_csv_parser('dvh_info', delimiter=':',
                                           skipinitialspace=True)
        test_iter = (test_parser(line, stl, ctx) for line in test_text)
        test_output = [row for row in chain.from_iterable(test_iter)]
        self.assertListEqual(test_output, expected_output)


class TestParseRules(unittest.TestCase):
    def test_parse_prescribed_dose_rule(self):
        test_text = [
            'Prescribed dose [cGy]: not defined',
            '% for dose (%): not defined',
            'Prescribed dose [cGy]: 5000.0',
            '% for dose (%): 100.0'
            ]
        expected_output = [
            ['Prescribed dose', ''],
            ['Prescribed dose unit', ''],
            ['Prescribed dose', '5000.0'],
            ['Prescribed dose unit', 'cGy'],
            ]

        dose_rule = read_dvh_file.make_prescribed_dose_rule()
        test_output = list()
        for line in test_text:
            result = dose_rule.apply(line)
            if result:
                test_output.extend(result)
        self.assertListEqual(test_output, expected_output)

    def test_date_parse_rule(self):
        test_text = [
            'Date: Friday, January 17, 2020 09:45:07',
            'Exported by: gsal'
            ]
        expected_output = [
            ['Date', ' Friday, January 17, 2020 09:45:07']
            ]

        date_rule = read_dvh_file.make_date_parse_rule()
        test_output = list()
        for line in test_text:
            result = date_rule.apply(line)
            if result:
                test_output.extend(result)
        self.assertListEqual(test_output, expected_output)

    def test_approved_status_rule(self):
        test_text = [
            'Plan: PARR',
            ('Plan Status: Treatment Approved Thursday, '
             'January 02, 2020 12:55:56 by gsal'),
            'Plan: PARR2-50Gy',
            'Plan Status: Unapproved'
            ]
        expected_output = [
            ['Plan Status', 'Treatment Approved'],
            ['Approved on', 'Thursday, January 02, 2020 12:55:56'],
            ['Approved by', 'gsal']
            ]

        approved_status_rule = read_dvh_file.make_approved_status_rule()
        test_output = list()
        for line in test_text:
            result = approved_status_rule.apply(line)
            if result:
                test_output.extend(result)
        self.assertListEqual(test_output, expected_output)


class TestLineParser(unittest.TestCase):
    def test_dvh_line_parser(self):
        test_text = [
            'Patient Name: ____, ____',
            'Patient ID:   1234567',
            'Comment:      DVHs for multiple plans and plan sums',
            'Date:Friday, January 17, 2020 09:45:07',
            'Exported by:  gsal',
            'Type:         Cumulative Dose Volume Histogram',
            'Description:  The cumulative DVH displays the percentage',
            'or volume (absolute) of structures that receive a dose',
            '        equal to or greater than a given dose.',
            '',
            'Plan sum: Plan Sum',
            'Course: PLAN SUM',
            'Prescribed dose [cGy]: not defined',
            '% for dose (%): not defined',
            '',
            'Plan: PARR',
            'Course: C1',
            ('Plan Status: Treatment Approved Thursday, '
            'January 02, 2020 12:55:56 by gsal'),
            'Prescribed dose [cGy]: 5000.0',
            '% for dose (%): 100.0'
            ]
        expected_output = [
            ['Patient Name', '____, ____'],
            ['Patient ID', '1234567'],
            ['Comment', 'DVHs for multiple plans and plan sums'],
            ['Date', 'Friday, January 17, 2020 09:45:07'],
            ['Exported by', 'gsal'],
            ['Type', 'Cumulative Dose Volume Histogram'],
            ['Description', 'The cumulative DVH displays the percentage'],
            ['or volume (absolute) of structures that receive a dose'],
            ['equal to or greater than a given dose.'],
            [],
            ['Plan sum', 'Plan Sum'],
            ['Course', 'PLAN SUM'],
            ['Prescribed dose', ''],
            ['Prescribed dose unit', ''],
            ['% for dose (%)', 'not defined'],
            [],
            ['Plan', 'PARR'],
            ['Course', 'C1'],
            ['Plan Status', 'Treatment Approved'],
            ['Approved on', 'Thursday, January 02, 2020 12:55:56'],
            ['Approved by', 'gsal'],
            ['Prescribed dose', '5000.0'],
            ['Prescribed dose unit', 'cGy'],
            ['% for dose (%)', '100.0']
            ]

        parsing_rules = [
            read_dvh_file.make_prescribed_dose_rule(),
            read_dvh_file.make_date_parse_rule(),
            read_dvh_file.make_approved_status_rule()
            ]
        default_parser = tp.define_csv_parser('dvh_info', delimiter=':',
                                              skipinitialspace=True)

        test_parser = tp.LineParser(parsing_rules, default_parser)
        test_output = [parsed_line
                       for parsed_line in test_parser.parse(test_text)]
        self.assertListEqual(test_output, expected_output)




if __name__ == '__main__':
    unittest.main()
