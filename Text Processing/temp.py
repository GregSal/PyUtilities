
from itertools import chain
from typing import List
from file_utilities import clean_ascii_text
import Text_Processing as tp
import read_dvh_file
from pprint import pprint
from buffered_iterator import BufferedIterator


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

plan_info_break = tp.SectionBoundaries(
     start_section=dvh_info_end,
     end_section=plan_info_end)
source = BufferedIterator(test_text)
context['Source'] = source
break_iter = plan_info_break.check_start(source, context, location='Start')
test_output = list()
index = 0
try:
    for index, row in enumerate(break_iter):
        test_output.append(row)
except tp.StartSection as end_marker:
    pprint(end_marker.get_context())
    print(f'Line count = {index}')
    pprint(test_output)
else:
    print('No Break Found')

