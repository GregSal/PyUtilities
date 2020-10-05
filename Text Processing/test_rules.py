import unittest
from pathlib import Path
from typing import Dict, List, Sequence, TypeVar, Pattern, Match, Iterator, Any,Callable
import re
from Text_Processing import Rule, Trigger

#%% Test Text
from pprint import pprint
test_lines = '''
Prescribed dose [cGy]: 5000.0
Prescribed dose [cGy]: not defined

Plan Status: Unapproved
Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal

% for dose(%): 100.0
% for dose (%): not defined
'''

#%%  Prescribed dose parse tests
def parse_prescribed_dose(line, sentinel, context)->List[List[str]]:
    '''Split "Prescribed dose [cGy]" into 2 lines:
        Prescribed dose
        Prescribed dose Unit
        '''
    parse_template = [
        ['Prescribed dose', '{dose}'],
        ['Prescribed dose Unit', '{unit}']
        ]
    match_results = sentinel.groupdict()
    if match_results['dose'] == 'not defined':
        parsed_lines = [
            ['Prescribed dose', ''],
            ['Prescribed dose Unit', '']
            ]
    else:
        parsed_lines = [
            [string_item.format(**match_results) for string_item in line_tmpl]
            for line_tmpl in parse_template
            ]
    return parsed_lines


class TestPrescribedDoseParse(unittest.TestCase):
    def setUp(self):
        base_path = Path.cwd()
        test_file = base_path / 'trigger_test_text.txt'
        #self.test_lines = self.file_lines()
        self.context = {
            'File Name': test_file.name,
            'File Path': test_file.parent,
            'Line Count': 0
            }

        prescribed_dose_pattern = (
            r'^Prescribed dose\s*'            # Begins with Prescribed dose
            r'[[]'                            # Unit start delimiter
            r'(?P<unit>[A-Za-z]+)'            # unit group: text surrounded by []
            r'[]]'                            # Unit end delimiter
            r'\s*:\s*'                        # Dose delimiter with possible whitespace
            r'(?P<dose>[0-9.]+|not defined)'  # dose group Number or "not defined"
            r'[\s\r\n]*'                      # drop trailing whitespace
            r'$'                              # end of string
            )
        re_pattern = re.compile(prescribed_dose_pattern)
        dose_trigger = Trigger(re_pattern, name='Prescribed Dose')
        self.rule = Rule(dose_trigger, pass_method=parse_prescribed_dose,
                         name = 'prescribed_dose_rule')

    def test_prescribed_dose_parse(self):
        line = 'Prescribed dose [cGy]: 5000.0'
        parsed_lines = self.rule.apply(line, self.context)
        results = [
            ['Prescribed dose', '5000.0'],
            ['Prescribed dose Unit', 'cGy']
            ]
        self.assertListEqual(parsed_lines, results)

    def test_no_prescribed_dose_parse(self):
        line = 'Prescribed dose [cGy]: not defined'
        parsed_lines = self.rule.apply(line, self.context)
        results = [
            ['Prescribed dose', ''],
            ['Prescribed dose Unit', '']
            ]
        self.assertListEqual(parsed_lines, results)


#%%  Date parse tests
def date_parse(line, sentinel, context)->List[List[str]]:
    '''If Date,don't split beyond first :'''
    parsed_lines = [
        [sentinel, line.split(':',maxsplit=1)[1]]
        ]
    return parsed_lines


class TestDateParse(unittest.TestCase):
    def setUp(self):
        base_path = Path.cwd()
        test_file = base_path / 'trigger_test_text.txt'
        #self.test_lines = self.file_lines()
        self.context = {
            'File Name': test_file.name,
            'File Path': test_file.parent,
            'Line Count': 0
            }

        date_trigger = Trigger('Date', name='Starts With Date', location='START')
        self.rule = Rule(date_trigger, pass_method=date_parse,
                         name = 'date_rule')

    def test_date_parse(self):
        line = 'Date                 : Thursday, August 13, 2020 15:21:06'
        expected_results = [['Date', ' Thursday, August 13, 2020 15:21:06']]
        parsed_lines = self.rule.apply(line, self.context)
        self.assertListEqual(parsed_lines, expected_results)


#%% Line Parsing
def approved_status_parse(line, sentinel, context)->List[List[str]]:
    '''If Treatment Approved, Split "Plan Status" into 3 lines:
        Plan Status
        Approved on
        Approved by
        '''
    idx1 = line.find(sentinel)
    idx2 = idx1 + len(sentinel)
    idx3 = line.find('by')
    idx4 = idx3 + 3
    parsed_lines = [
        ['Plan Status', line[idx1:idx2]],
        ['Approved on', line[idx2:idx3]],
        ['Approved by', line[idx4:]]
        ]
    return parsed_lines


#%%  Approval Status parse tests
class TestApprovalParse(unittest.TestCase):
    def setUp(self):
        base_path = Path.cwd()
        test_file = base_path / 'trigger_test_text.txt'
        #self.test_lines = self.file_lines()
        self.context = {
            'File Name': test_file.name,
            'File Path': test_file.parent,
            'Line Count': 0
            }

        status_trigger = Trigger('Treatment Approved', location='IN',
                                 name='Treatment Approved')
        self.rule = Rule(status_trigger, pass_method=approved_status_parse,
                         name = 'date_rule')

    def test_approval_parse(self):
        line = ('Plan Status: Treatment Approved Thursday, January 02, 2020 '
                '12:55:56 by gsal')
        expected_results = [
            ['Plan Status', 'Treatment Approved'],
            ['Approved on', ' Thursday, January 02, 2020 12:55:56 '],
            ['Approved by', 'gsal']
            ]
        parsed_lines = self.rule.apply(line, self.context)
        self.assertListEqual(parsed_lines, expected_results)


if __name__ == '__main__':
    unittest.main()
