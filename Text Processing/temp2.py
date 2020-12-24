#%% Imports
from pathlib import Path
from itertools import chain
from typing import List
from file_utilities import clean_ascii_text
import Text_Processing as tp
import read_dvh_file
from pprint import pprint
import pandas as pd
from buffered_iterator import BufferedIterator, BufferedIteratorEOF


#%% Logging
import logging_tools as lg
logger = lg.config_logger(prefix='temp', level='DEBUG')

# TODO Convert temp2 into unit tests
#%% Test Text
test_source = [
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
    'E Content3:3'
    'End Section',
    ]


test_result = [
    {
        'A':{
            'Section Name':'A',
            'A Content1':'a',
            'A Content2':'b',
            'A Content3':'c'
            }
        },
    {
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
    {
        'E':{
            'Section Name':'E',
            'E Content1':'1',
            'E Content2':'2',
            'E Content3':'3'
            }
        }
    ]
#%% Context
context = {}


#%% Line Processing
def combine_sections(section_dict_list):
    '''Combine section dictionaries into dictionary of dictionaries.
    '''
    output_dict = dict()
    for section_dict in section_dict_list:
        section_name = section_dict.get('Section Name')
        output_dict[section_name] = section_dict
    return output_dict


#%% Reader definitions
default_parser = tp.define_csv_parser(
    'test_parser',
    delimiter=':',
    skipinitialspace=True
    )

test_section_reader = tp.SectionReader(
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

section_break = tp.SectionBoundaries(
    start_section=section_start,
    end_section=section_end
    )

multi_section_break = tp.SectionBoundaries(
    start_section=multi_section_start,
    end_section=multi_section_end
    )
#%% Section definitions
test_section = tp.Section(
    section_name='Test Section',
    boundaries=section_break,
    reader=test_section_reader,
    aggregate=tp.to_dict
    )

test_multi_section = tp.Section(
    section_name='Test Multi Section',
    boundaries=multi_section_break,
    reader=test_section,
    aggregate=combine_sections
    )

#%% main
def main():
    section_list = list()

    source = BufferedIterator(test_source)

    #section_scan = test_section.initialize_scan(source, **context)
    #section_iter = test_section.catch_break(section_scan)
    #read_iter = test_section.reader.read(section_iter, **context)
    #print('Section A')

    section_dict = test_section.read(source, start_search=True, **context)
    print('Section A')
    pprint(section_dict)

    #section_scan = test_multi_section.initialize_scan(source, **context)

    #section_dict = test_section.read(section_scan, **context)
    ##section_dict = test_section.read(source, **context)
    #print('Section B')
    #pprint(section_dict)

    #section_dict = test_section.read(section_scan, **context)
    #print('Section C')
    #pprint(section_dict)

    #section_dict = test_section.read(section_scan, **context)
    #print('Section D')
    #pprint(section_dict)

    #section_dict = test_section.read(source, **context)
    #print('Section E')
    #pprint(section_dict)

    #multi_section_iter = test_multi_section.scan(source, **context)
    #print('Multi Section')
    #for item in multi_section_iter:
    #    pprint(item)


    section_dict2 = test_multi_section.read(source, **context)
    print('Multi Section')
    pprint(section_dict2)


if __name__ == '__main__':
    main()


