# pylint: disable=anomalous-backslash-in-string
# pylint: disable=unused-argument
# pylint: disable=logging-fstring-interpolation

'''Initial testing of DVH read
'''

#%% Imports
from pathlib import Path

from typing import Callable
import re
import pandas as pd

import logging_tools as lg
from file_utilities import clean_ascii_text
import Text_Processing as tp


#%% Logging
logger = lg.config_logger(prefix='read_dvh.file', level='INFO')


#%% Line Parsing Functions
# Date Rule
def make_date_parse_rule() -> tp.Rule:
    def date_parse(line: str) -> tp.ParseResults:
        '''If Date,don't split beyond first :.'''
        parsed_line = line.split(':', maxsplit=1)
        return parsed_line

    date_rule = tp.Rule('Date', location='START', name='date_rule',
                        pass_method=date_parse, fail_method='None')
    return date_rule


# Approved Status
def make_approved_status_rule() -> tp.Rule:
    '''If Treatment Approved, Split "Plan Status" into 3 lines:
        Plan Status
        Approved on
        Approved by
        '''
    def approved_status_parse(line, event) -> tp.ParseResults:
        '''If Treatment Approved, Split "Plan Status" into 3 lines:

        Return three rows for a line containing "Treatment Approved"
            Prescribed dose [unit]: dose
        Gives:
            [['Plan Status', 'Treatment Approved'],
             ['Approved on', date],
             ['Approved by', person]
        '''
        idx1 = line.find(event.test_value)
        idx2 = idx1 + len(event.test_value)
        idx3 = line.find(' by')
        idx4 = idx3 + 4
        parsed_lines = [
            ['Plan Status', line[idx1:idx2]],
            ['Approved on', line[idx2+1:idx3]],
            ['Approved by', line[idx4:]]
            ]
        return parsed_lines

    approved_status_rule = tp.Rule('Treatment Approved', location='IN',
                                   pass_method=approved_status_parse,
                                   fail_method='None',
                                   name='approved_status_rule')
    return approved_status_rule


# Prescribed Dose Rule
def make_prescribed_dose_rule() -> tp.Rule:
    def parse_prescribed_dose(line, event) -> tp.ParseResults:
        '''Split "Prescribed dose [cGy]" into 2 lines.

        Return two rows for a line containing:
            Prescribed dose [unit]: dose
        Gives:
            [['Prescribed dose', 'dose'],
            ['Prescribed dose unit', 'unit']],
        The line:
            Prescribed dose [unit]: not defined
        Results in:
            [['Prescribed dose', '5000.0'],
             ['Prescribed dose unit', 'cGy']]
        '''
        match_results = event.test_value.groupdict()
        if match_results['dose'] == 'not defined':
            match_results['dose'] = ''
            match_results['unit'] = ''

        parsed_lines = [
            ['Prescribed dose', match_results['dose']],
            ['Prescribed dose unit', match_results['unit']]
            ]
        return parsed_lines

    prescribed_dose_pattern = (
        r'^Prescribed dose\s*'  # Begins with Prescribed dose
        r'\['                   # Unit start delimiter
        r'(?P<unit>[A-Za-z]+)'  # unit group: text surrounded by []
        r'\]'                   # Unit end delimiter
        r'\s*:\s*'              # Dose delimiter with possible whitespace
        r'(?P<dose>[0-9.]+'     # dose group Number
        r'|not defined)'        #"not defined" alternative
        r'[\s\r\n]*'            # drop trailing whitespace
        r'$'                    # end of string
        )
    re_pattern = re.compile(prescribed_dose_pattern)
    dose_rule = tp.Rule(sentinel=re_pattern, name='prescribed_dose_rule',
                        pass_method= parse_prescribed_dose, fail_method='None')
    return dose_rule


def make_default_csv_parser() -> Callable:
    default_csv = tp.define_csv_parser('dvh_info', delimiter=':',
                                       skipinitialspace=True)
    return default_csv



#%% Post Processing Methods
def fix_structure_names(line: tp.ParsedString) -> tp.ParsedString:
    '''If Structure name starts with "=", add "'" to start of name.
    '''
    if len(line) == 2:
        if 'Structure' in line[0]:
            structure_name = line[1]
            if structure_name.startswith('='):
                structure_name = "'" + structure_name
                line[1] = structure_name
    return line


#%% Line Processing
def to_plan_info_dict(plan_info_dict_list):
    '''Combine Plan Info dictionaries into dictionary of dictionaries.
    '''
    output_dict = dict()
    for plan_info_dict in plan_info_dict_list:
        if len(plan_info_dict) == 0:
            continue
        plan_name = plan_info_dict.get('Plan')
        if not plan_name:
            plan_name = plan_info_dict.get('Plan sum')
            if not plan_name:
                plan_name = 'Plan'
        plan_info_dict['Plan'] = plan_name
        output_dict[plan_name] = plan_info_dict
    return output_dict

def to_structure_data_tuple(structure_data_list):
    '''Combine Structure and DVH data.
    '''
    structures_dict = dict()
    dvh_data_list = list()
    for structure_data, dvh_data in structure_data_list:
        plan_name = structure_data['Plan']
        course_id = structure_data['Course']
        structure_id = structure_data['Structure']
        logger.info(f'Reading DVH data for: {structure_id}.')
        indx = (course_id, plan_name, structure_id)
        structures_dict[indx] = structure_data
        data_columns = list(dvh_data.columns)
        indx_d = [indx + (d,) for d in data_columns]
        indx_names = ['Course', 'Plan', 'Structure', 'Data']
        index = pd.MultiIndex.from_tuples(indx_d, names=indx_names)
        dvh_data.columns = index
        dvh_data_list.append(dvh_data)
    structures_df = pd.DataFrame(structures_dict)
    dvh_df = pd.concat(dvh_data_list, axis='columns')
    return (structures_df, dvh_df)

#%% Reader definitions
default_parser = tp.define_csv_parser('dvh_info', delimiter=':',
                                      skipinitialspace=True)
dvh_info_reader = tp.ProcessingMethods([
    clean_ascii_text,
    tp.RuleSet([make_date_parse_rule()], default=default_parser),
    tp.trim_items,
    tp.drop_blanks,
    tp.merge_continued_rows
    ])
plan_info_reader = tp.ProcessingMethods([
    clean_ascii_text,
    tp.RuleSet([make_prescribed_dose_rule(), make_approved_status_rule()],
               default=default_parser),
    tp.trim_items,
    tp.drop_blanks,
    tp.convert_numbers
    ])
structure_info_reader = tp.ProcessingMethods([
    clean_ascii_text,
    default_parser,
    tp.trim_items,
    tp.drop_blanks,
    tp.convert_numbers,
    fix_structure_names
    ])
dvh_data_reader = tp.ProcessingMethods([
    clean_ascii_text,
    tp.define_fixed_width_parser(widths=10),
    tp.trim_items,
    tp.drop_blanks,
    tp.convert_numbers
    ])

#%% SectionBreak definitions
plan_info_start = tp.SectionBreak(
    name='Start of Plan Info',
    sentinel=['Plan:', 'Plan sum:'],
    break_offset='Before'
    )
plan_info_end = tp.SectionBreak(
    name='End of Plan Info',
    sentinel='% for dose (%):',
    break_offset='After'
    )
structure_info_start = tp.SectionBreak(
    name='Start of Structure Info',
    sentinel='Structure:',
    break_offset='Before'
    )
structure_info_end = tp.SectionBreak(
    name='End of Structure Info',
    sentinel='Gradient Measure',
    break_offset='After'
    )
dvh_data_start = tp.SectionBreak(
    name='Start of DVH Data',
    sentinel='Ratio of Total Structure Volume',
    break_offset='Before'
    )

#%% Section definitions
dvh_info_section = tp.Section(
    section_name='DVH Info',
    start_section=None,
    end_section=plan_info_start,
    processor=dvh_info_reader,
    aggregate=tp.to_dict
    )
plan_info_section = tp.Section(
    section_name='Plan Info',
    start_section=None,
    end_section=plan_info_end,
    processor=plan_info_reader,
    aggregate=tp.to_dict
    )
plan_info_group = tp.Section(
    section_name='Plan Info Group',
    start_section=plan_info_start,
    end_section=structure_info_start,
    processor=plan_info_section,
    aggregate=to_plan_info_dict
    )
structure_info_section = tp.Section(
    section_name='Structure',
    start_section=structure_info_start,
    end_section=structure_info_end,
    processor=structure_info_reader,
    aggregate=tp.to_dict
    )
dvh_data_section = tp.Section(
    section_name='DVH',
    start_section=dvh_data_start,
    end_section=structure_info_start,
    processor=dvh_data_reader,
    aggregate=tp.to_dataframe
    )
dvh_group_section = tp.Section(
    section_name='DVH Groups',
    start_section=structure_info_start,
    processor=[structure_info_section, dvh_data_section],
    aggregate=to_structure_data_tuple
    )


def date_processing():
    pass
def number_processing():
    pass


#%% Main Iteration
def main():
    # Test File
    base_path = Path.cwd()

    test_file_path = r'Text Files'
    test_file = base_path / test_file_path / 'PlanSum vs Original.dvh'

    # Call Primary routine
    context = {
        'File Name': test_file.name,
        'File Path': test_file.parent,
        'Line Count': 0,
        }

    source = tp.file_reader(test_file)

    dvh_info = dvh_info_section.read(source, context)
    plan_info = plan_info_group.read(source, context)
    structures_df, dvh_df = dvh_group_section.read(source, context)

    # Output DVH Data
    dvh_info_df = pd.Series(dvh_info)
    plan_data = pd.DataFrame(plan_info)
    struct_indx_names = ['Course', 'Plan', 'Structure']
    dvh_indx_names = ['Course', 'Plan', 'Structure', 'Data']
    output_file = base_path / 'read_dvh_test_results.xlsx'

    with pd.ExcelWriter(output_file) as writer:  # pylint: disable=abstract-class-instantiated
        dvh_info_df.to_excel(writer, 'DVH Info')
        plan_data.to_excel(writer, 'Plan Data')
        structures_df.to_excel(writer, 'Structures Data',
                               index_label=struct_indx_names)
        dvh_df.to_excel(writer, 'DVH Data',
                        index_label=dvh_indx_names)

    print('done')

if __name__ == '__main__':
    main()
