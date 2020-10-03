
from itertools import chain
from typing import List
from file_utilities import clean_ascii_text
import Text_Processing as tp
import read_dvh_file
from pprint import pprint


test_text = [
    'Patient Name: ____, ____',
    'Patient ID  : 1234567',
    'Comment     : DVHs for multiple plans and plan sums',
    'Date        : Friday, January 17, 2020 09:45:07',
    'Exported by : gsal',
    'Type        : Cumulative Dose Volume Histogram',
    'Description : The cumulative DVH displays the percentage',
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
    ['Comment ', 'DVHs for multiple plans and plan sums'],
    ['Date', ' Friday, January 17, 2020 09:45:07'],
    ['Exported by ', 'gsal'],
    ['Type', 'Cumulative Dose Volume Histogram'],
    ['Description ', 'The cumulative DVH displays the percentage (relative)'],
    ['or volume (absolute) of structures that receive a dose'],
    ['equal to or greater than a given dose.'],
    [''],
    ['Plan sum', 'Plan Sum'],
    ['Course', 'PLAN SUM'],
    ['Prescribed dose', ''],
    ['Prescribed dose unit', ''],
    [''],
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
pprint(test_output)