#%% Imports
import unittest
from pathlib import Path
from functools import partial
from itertools import chain
from typing import List
from file_utilities import clean_ascii_text
import Text_Processing as tp
import read_dvh_file
from pprint import pprint
import pandas as pd
from buffered_iterator import BufferedIterator, BufferedIteratorEOF

# Aggregate definitions
def print_list(parsed_lines):
    '''print items and add then to a list.
    '''
    output = list()
    for line_item in parsed_lines:
        pprint(line_item)
        output.append(line_item)
    return output


#%% tests
class TestSectionGroupRead(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        # Test Source
        self.test_source = [
            'Single Delimiter Section',
            'Section Name:D1',
            'D1 Content1:a',
            'D1 Content2:b',
            'D1 Content3:c',
            'End Section',
            '',
            'Single Fixed Width Section',
            'Section Name    F1',
            'F1 Content1     d',
            'F1 Content2     e',
            'F1 Content3     f',
            'End Section',
            '',
            'Text to be ignored',
            '',
            'Combined Group Section',
            '',
            'More Text to be ignored',
            '',
            'Single Delimiter Section',
            'Section Name:D2',
            'D2 Content1:m',
            'D2 Content2:n',
            'D2 Content3:o',
            'End Section',
            '',
            'Even More Text to be ignored',
            '',
            'Single Fixed Width Section',
            'Section Name    F2',
            'F2 Content1     p',
            'F2 Content2     q',
            'F2 Content3     r',
            'End Section',
            '',
            'Final Text to be ignored',
            '',
            'Done Combined Group Section',
            '',
            'Multi Combined Group Section',
            'Single Delimiter Section',
            'Section Name:D3',
            'D3 Content1:a',
            'D3 Content2:b',
            'D3 Content3:c',
            'End Section',
            'Single Fixed Width Section',
            'Section Name    F3',
            'F3 Content1     1',
            'F3 Content2     2',
            'F3 Content3     3',
            'End Section',
            'Single Delimiter Section',
            'Section Name:D4',
            'D4 Content1:d',
            'D4 Content2:e',
            'D4 Content3:f',
            'End Section',
            'Single Fixed Width Section',
            'Section Name    F4',
            'F4 Content1     4',
            'F4 Content2     5',
            'F4 Content3     6',
            'End Section',
            'Single Delimiter Section',
            'Section Name:D5',
            'D5 Content1:g',
            'D5 Content2:h',
            'D5 Content3:i',
            'End Section',
            'Single Fixed Width Section',
            'Section Name    F5',
            'F5 Content1     7',
            'F5 Content2     8',
            'F5 Content3     9',
            'End Section',
            'Single Delimiter Section',
            'Section Name:D6',
            'D6 Content1:j',
            'D6 Content2:k',
            'D6 Content3:l',
            'End Section',
            'Single Fixed Width Section',
            'Section Name    F6',
            'F6 Content1     10',
            'F6 Content2     11',
            'F6 Content3     12',
            'End Section',
            'Done Combined Group Section',
            ]

        # Test Results
        self.test_result = {
            'Section D1': {
                'Section Name':'D1',
                'D1 Content1': 'a',
                'D1 Content2': 'b',
                'D1 Content3': 'c'
                },
            'Section F1': {
                'Section Name':'F1',
                'F1 Content1': 'd',
                'F1 Content2': 'e',
                'F1 Content3': 'f'
                },
            'Test Group Section': [
                {'Section Name':'D2',
                 'D2 Content1': 'm',
                 'D2 Content2': 'n',
                 'D2 Content3': 'o'
                },
                {
                 'Section Name':'F2',
                 'F2 Content1': 'p',
                 'F2 Content2': 'q',
                 'F2 Content3': 'r'
                }],
            'Test Multi Group Section': [
                [{'Section Name':'D3',
                  'D3 Content1': 'a',
                  'D3 Content2': 'b',
                  'D3 Content3': 'c'
                 },
                 {
                  'Section Name':'F3',
                  'F3 Content1': 1,
                  'F3 Content2': 2,
                  'F3 Content3': 3
                 }],
                [{'Section Name':'D4',
                  'D4 Content1': 'd',
                  'D4 Content2': 'e',
                  'D4 Content3': 'f'
                 },
                 {
                  'Section Name':'F4',
                  'F4 Content1': 4,
                  'F4 Content2': 5,
                  'F4 Content3': 6
                 }],
                [{'Section Name':'D5',
                  'D5 Content1': 'g',
                  'D5 Content2': 'h',
                  'D5 Content3': 'i'
                 },
                 {
                  'Section Name':'F5',
                  'F5 Content1': 7,
                  'F5 Content2': 8,
                  'F5 Content3': 9
                 }],
                [{'Section Name':'D6',
                  'D6 Content1': 'j',
                  'D6 Content2': 'k',
                  'D6 Content3': 'l'
                 },
                 {
                  'Section Name':'F6',
                  'F6 Content1': 10,
                  'F6 Content2': 11,
                  'F6 Content3': 12
                 }]
                 ]
            }

        self.context = {}

        # Reader definitions
        fixed_width_parser=tp.define_fixed_width_parser(widths=16)
        delimiter_parser = tp.define_csv_parser(
            'delimiter_parser',
            delimiter=':',
            skipinitialspace=True
            )
        delimiter_section_reader = tp.SectionReader(
            default_parser=delimiter_parser,
            post_processing_methods=[tp.trim_items,
                                     tp.drop_blanks
                                     ]
            )
        fixed_width_reader = tp.SectionReader(
            default_parser=fixed_width_parser,
            post_processing_methods=[tp.trim_items,
                                        tp.drop_blanks,
                                        tp.convert_numbers]
            )
        # SectionBreak definitions
        delimiter_section_start = tp.SectionBreak(
            name='Delimiter Section',
            trigger=tp.Trigger('Single Delimiter Section'),
            offset='After'
            )
        fixed_width_section_start = tp.SectionBreak(
            name='Fixed Width Section',
            trigger=tp.Trigger('Single Fixed Width Section'),
            offset='After'
            )
        section_end = tp.SectionBreak(
            name='Single Section',
            trigger=tp.Trigger('End Section')
            )
        group_section_start = tp.SectionBreak(
            name='Combined Group Section',
            trigger=tp.Trigger('Combined Group Section'),
            offset='After'
            )
        multi_group_section_start = tp.SectionBreak(
            name='Multi Combined Group Section',
            trigger=tp.Trigger('Combined Group Section'),
            offset='After'
            )
        group_section_end = tp.SectionBreak(
            name='End Group Section',
            trigger=tp.Trigger('Done Combined Group Section'),
            offset='Before'
            )
        delimiter_section_break = tp.SectionBoundaries(
            start_section=delimiter_section_start,
            end_section=section_end
            )
        fixed_width_section_break = tp.SectionBoundaries(
            start_section=fixed_width_section_start,
            end_section=section_end
            )
        group_section_break = tp.SectionBoundaries(
            start_section=group_section_start,
            end_section=group_section_end
            )
        multi_group_section_break = tp.SectionBoundaries(
            start_section=group_section_start,
            end_section=group_section_end
            )

        # Section definitions
        self.delimiter_section = tp.Section(
            section_name='Delimiter Section',
            boundaries=delimiter_section_break,
            reader=delimiter_section_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )
        self.fixed_width_section = tp.Section(
            section_name='Fixed Width Section',
            boundaries=fixed_width_section_break,
            reader=fixed_width_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )
        self.group_section = tp.Section(
            section_name='Group Section',
            boundaries=group_section_break,
            reader=[self.delimiter_section, self.fixed_width_section],
            aggregate=print_list
            )
        self.multi_group_section = tp.Section(
            section_name='Group Section',
            boundaries=multi_group_section_break,
            reader=[self.delimiter_section, self.fixed_width_section],
            aggregate=print_list
            )

    def test_delimiter_sub_section_read(self):
        test_section = self.delimiter_section
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        **self.context)
        self.assertDictEqual(test_output, self.test_result['Section D1'])

    def test_fixed_width_sub_section_read(self):
        test_section = self.fixed_width_section
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        **self.context)
        self.assertDictEqual(test_output, self.test_result['Section F1'])

    def test_group_section_read(self):
        test_section = self.group_section
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        **self.context)
        expected_output = self.test_result['Test Group Section']
        for count, output in enumerate(zip(test_output, expected_output)):
            with self.subTest(section=count):
                section_output = output[0]
                expected_section_output = output[1]
                self.assertDictEqual(section_output,
                                     expected_section_output)

    def test_multi_group_section_read(self):
        test_section = self.multi_group_section
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        **self.context)
        expected_output = self.test_result['Test Multi Group Section']
        for section_count, section_output in enumerate(zip(test_output,
                                                           expected_output)):
            for count, output in enumerate(zip(section_output[0],
                                               expected_output[1])):
                subsection = f'{section_count}.{count}'
                with self.subTest(subsection=subsection):
                    section_output = output[0]
                    expected_section_output = output[1]
                    self.assertDictEqual(section_output,
                                         expected_section_output)
if __name__ == '__main__':
    unittest.main()


