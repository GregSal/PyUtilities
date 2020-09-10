import unittest
from pathlib import Path
import re

from read_dvh_file import Trigger

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
pprint(test_lines.splitlines())

#FIXME Move to read_dvh_file
def parse_prescribed_dose(sentinel):
    '''Split "Prescribed dose [cGy]" into 2 lines:
        Prescribed dose
        Prescribed dose Unit

        Next rule
        Don't split date portion

        Next rule
        By -> new row
            Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal
            Plan Status: Planning Approved

        '''
    parse_template = [
        ['Prescribed dose', '{dose}'],
        ['Prescribed dose Unit', '{unit}']
        ]
    match_results = sentinel.groupdict()
    if match_results['dose'] == 'not defined':
        parsed_lines = [
            ['Prescribed dose', None]
            ]
    else:
        parsed_lines = [
            [string_item.format(**match_results) for string_item in line_tmpl]
            for line_tmpl in parse_template
            ]
    return parsed_lines

#FIXME Move to read_dvh_file
def make_prescribed_dose_trigger():
        prescribed_dose_pattern = (
            r'^'                # Beginning of string
            r'Prescribed dose'  # Row Label
            r'\s*'              # Skip whitespace
            r'[[]'              # Unit start delimiter
            r'(?P<unit>'        # Beginning of unit group
            r'[A-Za-z]+'        # Unit text
            r')'                # end of unit string group
            r'[]]'              # Unit end delimiter
            r'\s*'              # Skip whitespace
            r':'                # Dose delimiter
            r'\s*'              # Skip whitespace
            r'(?P<dose>'        # Beginning of dose group
            r'[0-9.]+'          # Dose value
            r'|not defined'     # Undefined dose alternate
            r')'                # end of value string group
            r'\s*'              # drop trailing whitespace
            r'$'                # end of string
            )
        re_pattern = re.compile(prescribed_dose_pattern)
        dose_trigger = Trigger(re_pattern, name='Prescribed Dose')
        return dose_trigger

#FIXME Move to read_dvh_file
def prescribed_dose_rule(context, line):
    dose_trigger = make_prescribed_dose_trigger()
    is_match, sentinel = dose_trigger.apply(context, line)
    if is_match:
        parsed_lines = parse_prescribed_dose(sentinel)
        return parsed_lines
    return None

#%%  Prescribed dose parse tests
class TestParsePrescribedDose(unittest.TestCase):
    def setUp(self):
        base_path = Path.cwd()
        test_file = base_path / 'trigger_test_text.txt'
        #self.test_lines = self.file_lines()
        self.context = {
            'File Name': test_file.name,
            'File Path': test_file.parent,
            'Line Count': 0
            }


    def test_prescribed_dose_parse(self):
        line = 'Prescribed dose [cGy]: 5000.0'
        parsed_lines = prescribed_dose_rule(self.context, line)
        results = [
            ['Prescribed dose', '5000.0'],
            ['Prescribed dose Unit', 'cGy']
            ]
        self.assertListEqual(parsed_lines, results)



if __name__ == '__main__':
    unittest.main()
