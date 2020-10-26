import unittest
from pathlib import Path
import re
from file_utilities import clean_ascii_text
import Text_Processing as tp
from typing import List
from buffered_iterator import BufferedIterator
import read_dvh_file
from pprint import pprint
import pandas as pd
from buffered_iterator import BufferedIterator, BufferedIteratorEOF

test_source = [
    'Patient Name         : _y__, ____',
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
    '']
def break_iter(source, break_check):
    source_iter = iter(source)
    while True:
        try:
            row = source_iter.__next__()
            test_output = break_check(row)
        except (tp.StartSection, tp.StopSection) as marker:
            context = marker.get_context()
            break
        except (BufferedIteratorEOF, StopIteration) as eof:
            ##
            # FIXME get context
            ##
            #context['sentinel'] = 'End of Source'
            break
        yield row


context = {}
dvh_info_break = read_dvh_file.dvh_info_break
dvh_info_section = read_dvh_file.dvh_info_section
# scan_section
source = BufferedIterator(test_source)
context['Source'] = source
context['Current Section'] = 'DVH Info'
break_check = dvh_info_break.check_end(context)
section_scan = break_iter(source, break_check)
test_output = dvh_info_section.scan_section(section_scan, context)

for key, value in test_output.items():
    print(f'{key}\t\t{value}\n')
