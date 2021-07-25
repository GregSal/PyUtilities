#%% Imports
import unittest
from functools import partial
import Text_Processing as tp

from buffered_iterator import BufferedIterator


#%% Reader definitions
default_parser = tp.define_csv_parser(
    'test_parser',
    delimiter=':',
    skipinitialspace=True
    )

test_section_reader = tp.SectionParser(
    default_parser=default_parser,
    post_processing_methods=[tp.trim_items,
                             tp.drop_blanks,
                             tp.merge_continued_rows
                             ]
    )


#%% SectionBreak definitions
section_start = tp.SectionBreak(
    name='Single Section',
    trigger=tp.Trigger('Section Name')
    )

section_end = tp.SectionBreak(
    name='Single Section',
    trigger=tp.Trigger('End Section')
    )

multi_section_start = tp.SectionBreak(
    name='Multi Section',
    trigger=tp.Trigger('Multi Section'),
    offset='After'
    )

multi_section_end = tp.SectionBreak(
    name='End Multi Section',
    trigger=tp.Trigger('Done Multi Section'),
    offset='Before'
    )


#%% tests
class TestSectionRead(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
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

            'Multi Section',
            'Single Section',
            'Section Name:B',
            'B Content1:a',
            'B Content2:b',
            'B Content3:c',
            'End Section',

            'Single Section',
            'Section Name:C',
            'C Content1:d',
            'C Content2:e',
            'C Content3:f',
            'End Section',

            'Single Section',
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
            'Test Multi Section': {
                'B':{
                    'Section Name':'B',
                    'B Content1':'a',
                    'B Content2':'b',
                    'B Content3':'c'
                    },
                'C':{
                    'Section Name':'C',
                    'C Content1':'d',
                    'C Content2':'e',
                    'C Content3':'f'
                    },
                'D':{
                    'Section Name':'D',
                    'D Content1':'g',
                    'D Content2':'h',
                    'D Content3':'i'
                    }
                },
            'Section E': {
                'Section Name':'E',
                'E Content1':'1',
                'E Content2':'2',
                'E Content3':'3'
                }
            }

        self.context = {}

    def test_section_read(self):
        test_section = tp.Section(
            section_name='Test Section',
            start_section=section_start,
            end_section=section_end,
            reader=test_section_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )
        source = BufferedIterator(self.test_source)

        test_output = test_section.read(source, start_search=True,
                                        **self.context)
        self.assertDictEqual(test_output, self.test_result['Section A'])

    def test_multi_section_read(self):
        def combine_sections(section_dict_list):
            '''Combine section dictionaries into dictionary of dictionaries.
            '''
            output_dict = dict()
            for section_dict in section_dict_list:
                if section_dict:
                    section_name = section_dict.get('Section Name')
                    output_dict[section_name] = section_dict
            return output_dict

        test_section = tp.Section(
            section_name='Test Section',
            start_section=section_start,
            end_section=section_end,
            reader=test_section_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )
        test_multi_section = tp.Section(
            section_name='Test Multi Section',
            start_section=multi_section_start,
            end_section=multi_section_end,
            reader=test_section,
            aggregate=combine_sections
            )

        source = BufferedIterator(self.test_source)

        section_one = test_section.read(source, start_search=True,
                                        **self.context)
        self.assertDictEqual(section_one, self.test_result['Section A'])

        multi_section = test_multi_section.read(source, start_search=False,
                                                **self.context)
        self.assertDictEqual(multi_section,
                             self.test_result['Test Multi Section'])

        section_dict2 = test_section.read(source, start_search=False,
                                          **self.context)
        self.assertDictEqual(section_dict2,
                             self.test_result['Section E'])

    def test_end_section_read(self):
        test_section = tp.Section(
            section_name='Test Section',
            start_section=multi_section_end,
            end_section=section_end,
            reader=test_section_reader,
            aggregate=partial(tp.to_dict, default_value=None)
            )

        source = BufferedIterator(self.test_source)
        section_dict2 = test_section.read(source, start_search=True,
                                          **self.context)
        self.assertDictEqual(section_dict2,
                             self.test_result['Section E'])


if __name__ == '__main__':
    unittest.main()


