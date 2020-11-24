
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

#%% Scan Group
def scan_plan_info_group(test_source, context):
    info_section = tp.Section(
        section_name='DVH Info',
        boundaries=read_dvh_file.dvh_info_break,
        reader=read_dvh_file.dvh_info_reader,
        aggregate=tp.to_dict)

    test_section = tp.Section(
        section_name='Plan Info',
        boundaries=read_dvh_file.plan_info_break,
        reader=read_dvh_file.plan_info_reader,
        aggregate=tp.to_dict)

    group = tp.Section(
        section_name='Plan Info Group',
        boundaries=read_dvh_file.plan_group_break,
        reader=test_section,
        aggregate=list)

    def test_group_output(used_lines):
        output_lines = list()
        for row in used_lines:
            output_lines.append(row)
            logger.debug(f'In PlanGroupOutput, adding line: {row}')
        return output_lines

    def section_iter(section, test_source, context):
        source = BufferedIterator(test_source)
        context['Source'] = source
        find_start = iter(section.boundaries(source, context,
                                             'Start', section.section_name))
        [row for row in find_start]
        section.context = section.boundaries.context
        section.context['Current Section'] = section.section_name
        section_scan = section.boundaries.__iter__(
            source, section.context, 'End', section.section_name)
        try:
            while True:
                section_reader = section.reader.read(section_scan, section.context)
                yield from section_reader
        except (BufferedIteratorEOF, StopIteration) as eof:
            section.context = getattr(section.reader, 'context', section.context)
            section.context['status'] = 'End of Source'
        except (tp.StartSection, tp.StopSection) as marker:
            context = getattr(section.reader, 'context', section.context)
            context.update(marker.get_context())
            context['status'] = f'End of {section.section_name}'
            section.context = context.copy()
            logger.debug(f'End of {section.section_name}')

    list_output = list()
    for item in section_iter(group, test_source, context):
        list_output.append(item)
        pprint(item)
    print('Aggregate')
    pprint(list_output)
    return list_output


#%% main
def main():

    #%% Test Text
    test_source = [
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


    test_result = {
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
        'Plan Info': [{
                'Plan sum': 'Plan Sum',
                'Course': 'PLAN SUM',
                'Prescribed dose': '',
                'Prescribed dose unit': '',
                '% for dose (%)': 'not defined'
                }, {
                'Plan': 'PARR',
                'Course': 'C1',
                'Plan Status': 'Treatment Approved',
                'Approved on': 'Thursday, January 02, 2020 12:55:56',
                'Approved by': 'gsal',
                'Prescribed dose': 5000.0,
                'Prescribed dose unit': 'cGy',
                '% for dose (%)': 100.0
                }],
        'Structures': pd.DataFrame([{
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
                },{
                'Structure': 'PTV 50',
                'Approval Status': 'Approved',
                'Plan': 'Plan Sum',
                'Course': 'PLAN SUM',
                'Volume [cc]': 363.6,
                'Dose Cover.[%]': 100.0,
                'Sampling Cover.[%]': 100.0,
                'Min Dose [cGy]': 3985.9,
                'Max Dose [cGy]': 5442.0,
                'Mean Dose [cGy]': 5144.5,
                'Modal Dose [cGy]': 5177.3,
                'Median Dose [cGy]': 5166.9,
                'STD [cGy]': 131.9,
                'NDR': '',
                'Equiv. Sphere Diam. [cm]': 8.9,
                'Conformity Index': 'N/A',
                'Gradient Measure [cm]': 'N/A'
                }]),
        'DVH': pd.DataFrame([
            {
                'Structure': 'PRV5 SpinalCanal',
                'Plan': 'Plan Sum',
                'Dose [cGy]': [0, 1, 2, 3, 4, 5, 3667, 3668, 3669, 3670],
                'Ratio of Total Structure Volume [%]': [100, 100, 100, 100,
                                                        100, 100,
                                                        4.23876e-005,
                                                        2.87336e-005,
                                                        1.50797e-005,
                                                        1.4257e-006]
                },
            {
                'Structure': 'PTV 50',
                'Plan': 'Plan Sum',
                'Dose [cGy]': [0,1,2,3,4,5,5437,5438,5439,5440,5441,5442],
                'Ratio of Total Structure Volume [%]': [100, 100, 100, 100,
                                                        100, 100,
                                                        9.4777e-005,
                                                        6.35607e-005,
                                                        3.62425e-005,
                                                        1.82336e-005,
                                                        9.15003e-006,
                                                        6.6481e-008]
                }])
        }
    #%% Context
    context = {
        'File Name': 'Test_DVH_Sections.txt',
        'File Path': Path.cwd() / 'Text Files' / 'Test_DVH_Sections.txt',
        'Line Count': 0
        }

    #%% Readers
    #dvh_info, context = scan_dvh_info_section(test_source, context)
    #plan_info, context = scan_plan_info_group(test_source, context)
    #test_plan_info_break(test_source, context)
    #test_plan_group_break(test_source, context)
    scan_plan_info_group(test_source, context)


if __name__ == '__main__':
    main()


#%% Old code
def scan_sections(source, context):
    [row for row in info_section.break_iter(source, context, 'Start')]
    context['Current Section'] = info_section.section_name
    section_scan = info_section.break_iter(source, context, 'End')

    info_items1 = info_section.reader.read(BufferedIterator(section_scan), context)
    info_output1 = info_section.aggregate(info_items1)
    print('info_output1')
    pprint(info_output1)
    info_items2 = info_section.reader.read(BufferedIterator(section_scan), context)
    info_output2 = info_section.aggregate(info_items2)
    print('info_output2')
    pprint(info_output2)

    [row for row in group.break_iter(source, context, 'Start')]
    context['Current Section'] = group.section_name
    section_scan = group.break_iter(source, context, 'End')

    section_items1 = group.reader.read(BufferedIterator(section_scan), context)
    print('section_items1')
    pprint(section_items1)
    section_items2 = group.reader.read(BufferedIterator(section_scan), context)
    print('section_items2')
    pprint(section_items2)
    section_items3 = group.reader.read(BufferedIterator(section_scan), context)
    print('section_items3')
    pprint(section_items3)


def scan_dvh_info_section(test_source, context):
    dvh_info_section = read_dvh_file.dvh_info_section
    source = BufferedIterator(test_source)
    context['Source'] = source
    print('Reading DVH Info Section')
    dvh_info = dvh_info_section.read(source, context)
    context = dvh_info_section.context
    for key, value in dvh_info.items():
        print(f'{key}\t\t{value}')
    return dvh_info, context


def test_plan_info_break(test_source, context):
    plan_info_break = tp.SectionBoundaries(
        start_section=read_dvh_file.plan_info_start,
        end_section=read_dvh_file.plan_info_end)
    source = BufferedIterator(test_source)
    context['Source'] = source
    start_check = plan_info_break.check_start(context)
    skipped_lines = list()
    try:
        for row in source:
            skipped_lines.append(start_check(row))
    except tp.StartSection as start_marker:
        context = start_marker.get_context()
        pprint(context)
    else:
        print('Section not found')

    end_check = plan_info_break.check_end(context)
    used_lines = list()
    try:
        for row in source:
            used_lines.append(end_check(row))
    except tp.StopSection as end_marker:
        context = end_marker.get_context()
        pprint(context)
    else:
        print('End of text')
    pprint(used_lines)
    return used_lines, context


def test_plan_group_break(test_source, context):
    def test_plan_output(used_lines):
        output_lines = list()
        for row in used_lines:
            line = ''.join(row)
            output_lines.append(line)
            logger.debug(f'In PlanOutput, adding line: {line}')
        return output_lines
    def test_group_output(used_lines):
        output_lines = list()
        for row in used_lines:
            output_lines.append(row)
            logger.debug(f'In PlanGroupOutput, adding line: {row}')
        return output_lines

    test_parser = tp.define_csv_parser('Test Reader', delimiter='~')
    test_reader = tp.SectionReader(default_parser=test_parser)
    test_section = tp.Section(
        section_name='Test Section',
        boundaries=read_dvh_file.plan_info_break,
        reader=test_reader,
        aggregate=test_plan_output)

    plan_info_group = tp.Section(
        section_name='Plan Info Group',
        boundaries=read_dvh_file.plan_group_break,
        reader=test_section,
        aggregate=test_group_output)

    source = BufferedIterator(test_source)
    context['Source'] = source
    print('Reading Plan Info Group')
    plan_info = plan_info_group.read(source, context)
    for plan in plan_info:
        for row in plan:
            print(row)
    return plan_info


def scan_section():
    source = BufferedIterator(test_source)
    context['Source'] = source
    print('Reading DVH Info Section')
    output, context = read_dvh_file.dvh_info_section.read(source, context)
    for key, value in output.items():
        print(f'{key}\t\t{value}')

    print('\\n\nReading Plan Info Section 1')
    output, context = read_dvh_file.plan_info_section.read(source, context)
    for key, value in output.items():
        print(f'{key}\t\t{value}')

    print('\n\nReading Plan Info Section 2')
    output, context = read_dvh_file.plan_info_section.read(source, context)
    for key, value in output.items():
        print(f'{key}\t\t{value}')

    print('\n\nReading Structure Section')
    output, context = read_dvh_file.structure_info_section.read(source, context)
    for key, value in output.items():
        print(f'{key}\t\t{value}')

    print('Reading DVH Section')
    output, context = read_dvh_file.dvh_data_section.read(source, context)
    print(output)

    print('\n\nReading Structure Section')
    output, context = read_dvh_file.structure_info_section.read(source, context)
    for key, value in output.items():
        print(f'{key}\t\t{value}')
    print('Reading DVH Section')
    output, context = read_dvh_file.dvh_data_section.read(source, context)
    print(output)
