import unittest
from pathlib import Path
from typing import List
import re
from Text_Processing import Rule, Trigger, RuleSet
import Text_Processing as tp

#%% Test Text
test_lines = '''
Prescribed dose [cGy]: 5000.0
Prescribed dose [cGy]: not defined

Plan Status: Unapproved
Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal

% for dose(%): 100.0
% for dose (%): not defined
'''

#%%  Prescribed dose parse tests
def parse_prescribed_dose(line, event, **context)->List[List[str]]:# pylint: disable=unused-argument
    '''Split "Prescribed dose [cGy]" into 2 lines:
        Prescribed dose
        Prescribed dose Unit
        '''
    parse_template = [
        ['Prescribed dose', '{dose}'],
        ['Prescribed dose Unit', '{unit}']
        ]
    match_results = event.test_value.groupdict()
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
        self.rule = Rule(re_pattern, pass_method=parse_prescribed_dose,
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
def date_parse(line, event, **context)->List[List[str]]:  # pylint: disable=unused-argument
    '''If Date,don't split beyond first :'''
    parsed_lines = [
        [event.test_value, line.split(':',maxsplit=1)[1]]
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
        self.rule = Rule(sentinel='Date', location='START',
                         pass_method=date_parse, name = 'date_rule')

    def test_date_parse(self):
        line = 'Date                 : Thursday, August 13, 2020 15:21:06'
        expected_results = [['Date', ' Thursday, August 13, 2020 15:21:06']]
        parsed_lines = self.rule.apply(line, self.context)
        self.assertListEqual(parsed_lines, expected_results)


#%% Line Parsing
def approved_status_parse(line, event, context)->List[List[str]]:  # pylint: disable=unused-argument
    '''If Treatment Approved, Split "Plan Status" into 3 lines:
        Plan Status
        Approved on
        Approved by
        '''
    idx1 = line.find(event.test_value)
    idx2 = idx1 + len(event.test_value)
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
        self.rule = Rule(sentinel='Treatment Approved', location='IN',
                         pass_method=approved_status_parse, name = 'date_rule')

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


#%%  Parse with single line

# Test data
class TestRuleExceptions(unittest.TestCase):

    @unittest.skip('Currently rule_method(item, context) is allowed')
    def test_no_event_arg(self):
        test_func = lambda item, context: str(item) + repr(context)
        with self.assertRaises(ValueError):
            invalid_rule = tp.Rule('T', pass_method=test_func)

    def test_no_arg(self):
        def test_func():
            return "T"
        with self.assertRaises(ValueError):
            invalid_rule = tp.Rule('T', pass_method=test_func)

    def test_many_arg(self):
        test_func = lambda item1, item2, event, context: 'a'
        with self.assertRaises(ValueError):
            invalid_rule = tp.Rule('T', pass_method=test_func)

    def test_bad_action(self):
        with self.assertRaises(ValueError):
            invalid_rule = tp.Rule('T', pass_method='Not an Action')

class TestRuleActions(unittest.TestCase):
    def test_original_action(self):
        test_text = 'Test Text'
        test_rule = tp.Rule('Text', pass_method='Original')
        result = test_rule.apply(test_text, {})
        self.assertEqual(result, test_text)

    def test_event_action(self):
        test_text = 'Test Text'
        sentinel = 'Text'
        test_rule = tp.Rule(sentinel, pass_method='Event')
        result = test_rule.apply(test_text, {})
        self.assertEqual(result.test_value, sentinel)

    def test_none_action(self):
        test_text = 'Test Text'
        test_rule = tp.Rule('Text', pass_method='None')
        result = test_rule.apply(test_text, {})
        self.assertIsNone(result)

    def test_blank_action(self):
        test_text = 'Test Text'
        test_rule = tp.Rule('Text', pass_method='Blank')
        result = test_rule.apply(test_text, {})
        self.assertEqual(result, '')

class TestRuleFail(unittest.TestCase):
    def test_fail_method(self):
        test_text = 'Test Line'
        test_rule = tp.Rule('Text', pass_method='Blank',
                            fail_method='Original')
        result = test_rule.apply(test_text, {})
        self.assertEqual(result, test_text)
        result2 = test_rule.apply('Test Text', {})
        self.assertEqual(result2, '')


def make_float(item, **context):
    item_c = item.replace('Line','')
    try:
        num = float(item_c.strip())
    except:
        return None
    output =  f'Line {num:5.2f}'
    context['num'] = num
    return output


class TestRuleSet(unittest.TestCase):
    def setUp(self):
        rule1 = Rule(['Data', 'Text'], pass_method='Name')
        rule2 = Rule(['Line', 'Text'], 'START', pass_method='Original',
                     fail_method='Blank')
        rule3 = Rule(make_float, pass_method='Value')
        default = lambda Val: 'This is the Default'

        self.test_set = RuleSet([rule1, rule2, rule3], default)

        self.test_pairs = [
            ('Line 1 Text', 'Text'),
            ('Line 2 Info', 'Line 2 Info'),
            ('123.5', 'Line 123.50'),
            ('Random Info', 'This is the Default'),
            ('Line 12', 'Line 12')
            ]

    def test_first_rule_wins(self):
        context = {}
        line, expected = self.test_pairs[0]
        result = self.test_set.apply(line, context)
        self.assertEqual(result, expected)

    def test_second_rule_only(self):
        context = {}
        line, expected = self.test_pairs[1]
        result = self.test_set.apply(line, context)
        self.assertEqual(result, expected)

    def test_function_rule(self):
        context = {}
        line, expected = self.test_pairs[2]
        result = self.test_set.apply(line, context)
        self.assertEqual(result, expected)

    @unittest.skip('Not working')
    def test_context_update(self):
        context = {'Initial Item': "nothing"}
        line, expected = self.test_pairs[2]
        result = self.test_set.apply(line, context)
        self.assertEqual(context['num'], float(line))

    def test_fail_to_default(self):
        context = {}
        line, expected = self.test_pairs[3]
        result = self.test_set.apply(line, context)
        self.assertEqual(result, expected)

    def test_second_rule_wins(self):
        context = {}
        line, expected = self.test_pairs[4]
        result = self.test_set.apply(line, context)
        self.assertEqual(result, expected)


class TestSingleLineParse(unittest.TestCase):
    def setUp(self):
        test_text = '\n'.join([
            'Text Processing      - Ignore'
            'Text Processing      - Use'
            'Text Processing      - Ignore'
            ])
        self.test_source = test_text.splitlines()
        self.test_result = ['Text Processing','Use']

        self.default_parser = tp.define_csv_parser('comma')
        #use_trigger = Trigger('Use', name='Use')
        self.rule = Rule('Use', location='IN')




if __name__ == '__main__':
    unittest.main()
