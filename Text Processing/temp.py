
from itertools import chain
from typing import List
from file_utilities import clean_ascii_text
import Text_Processing as tp
import read_dvh_file
from pprint import pprint
from buffered_iterator import BufferedIterator, BufferedIteratorEOF


test_text = [
    'Patient Name: ____, ____',
    'Patient ID: 1234567',
    'Comment: DVHs for multiple plans and plan sums',
    'Exported by: gsal',
    'Type: Cumulative Dose Volume Histogram',
    '',
    'Plan sum: Plan Sum',
    'Course: PLAN SUM',
    'Prescribed dose [cGy]: not defined',
    '% for dose (%): not defined',
    '',
    'Plan: PARR',
    'Course: C1',
    'Prescribed dose [cGy]: 5000.0',
    '% for dose (%): 100.0',
    '',
    'Structure: PRV5 SpinalCanal',
    'Approval Status: Approved',
    'Plan: Plan Sum',
    'Course: PLAN SUM',
    'Volume [cm³]: 121.5',
    'Conformity Index: N/A',
    'Gradient Measure [cm]: N/A'
    ]
context = {}
dvh_info_end = tp.SectionBreak(
    name='End of DVH Info',
    trigger=tp.Trigger(['Plan:', 'Plan sum:'])
    )
plan_info_end = tp.SectionBreak(
    name='End of Plan Info',
    trigger=tp.Trigger(['% for dose (%):']),
    offset='After'
    )
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
dvh_info_break = tp.SectionBoundaries(
    start_section=None,
    end_section=dvh_info_end)
plan_info_break = tp.SectionBoundaries(
     start_section=dvh_info_end,
     end_section=plan_info_end)
plan_info_break = tp.SectionBoundaries(
     start_section=dvh_info_end,
     end_section=plan_info_end)
structure_info_break = tp.SectionBoundaries(
     start_section=structure_info_start,
     end_section=structure_info_end)

source = BufferedIterator(test_text)
context['Source'] = source
start_list = [
    structure_info_break.check_start(context),
    plan_info_break.check_start(context)
    ]
stop_list = [
    structure_info_break.check_end(context),
    plan_info_break.check_end(context),
    dvh_info_break.check_end(context)
    ]
test_source = iter(source)
break_iter = iter(tp.cascading_iterators(test_source, stop_list))
section_output = list()
break_output = list()
index = 0
while True:
    try:
        print(f'\nNext Line')
        line = break_iter.__next__()
        index += 1
        section_output.append(line)
        print(f'Checking line: {line}\n')
    except tp.StartSection as marker:
        sentinel = marker.get_context()['sentinel']
        section_output = list()
        break_output.append({
            'Break Type': 'Start',
            'Sentinel': sentinel})
        print(f'Break on: {sentinel}\n')
        break_iter = iter(tp.cascading_iterators(test_source, stop_list))
    except tp.StopSection as marker:
        sentinel = marker.get_context()['sentinel']
        break_output.append({
            'Break Type': 'End',
            'Sentinel': sentinel,
            'Section Lines': section_output,
            'Line count': index})
        print(f'Break on: {sentinel}\n')
        section_output = list()
        break_iter = iter(tp.cascading_iterators(test_source, start_list))
    except (BufferedIteratorEOF, StopIteration) as eof:
        print(eof)
        sentinel = 'End of Text'
        break_output.append({
            'Break Type': 'End',
            'Sentinel': sentinel,
            'Section Lines': section_output,
            'Line count': index})
        break
    else:
        print('No Break Found')
    print('Done Loop\n')
pprint(break_output)
