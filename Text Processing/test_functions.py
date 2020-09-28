import unittest
from itertools import chain
from file_utilities import clean_ascii_text
import Text_Processing as tp
from typing import List


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

    def test_list_csv_parser(self):
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
        stl = ''
        ctx = {}
        test_parser = tp.define_csv_parser('dvh_info', delimiter=':',
                                           skipinitialspace=True)
        test_iter = (test_parser(line, stl, ctx) for line in test_text)
        test_output = [row for row in chain.from_iterable(test_iter)]
        self.assertListEqual(test_output, expected_output)

    def test_date_parse_function(self):

        def date_parse(line, *args, **kwargs) -> tp.ParseResults:
            '''If Date,don't split beyond first :'''
            parsed_line = line.split(':', maxsplit=1)
            return [parsed_line]

        test_text = [
            'Date: Friday, January 17, 2020 09:45:07',
            'Exported by: gsal'
            ]
        expected_output = [
            ['Date', ' Friday, January 17, 2020 09:45:07'],
            ['Exported by', 'gsal']
            ]

        test_iter = (date_parse(line) for line in test_text)
        test_output = [row for row in chain.from_iterable(test_iter)]
        self.assertListEqual(test_output, expected_output)

    def test_approved_status_parse_function(self):

        def approved_status_parse(line, sentinel, context=None) -> List[List[str]]:
            '''If Treatment Approved, Split "Plan Status" into 3 lines:
                Plan Status
                Approved on
                Approved by
                '''
            idx1 = line.find(sentinel)
            idx2 = idx1 + len(sentinel)
            idx3 = line.find(' by')
            idx4 = idx3 + 4
            parsed_lines = [
                ['Plan Status', line[idx1:idx2]],
                ['Approved on', line[idx2+1:idx3]],
                ['Approved by', line[idx4:]]
                ]
            return parsed_lines

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

        trigger = tp.Trigger('Treatment Approved')
        test_output = list()
        for line in test_text:
            is_pass, sentinel = trigger.apply(line)
            if is_pass:
                test_output.extend(approved_status_parse(line, sentinel))
        self.assertListEqual(test_output, expected_output)

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
