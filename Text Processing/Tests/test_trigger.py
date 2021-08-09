import unittest
from pathlib import Path
import re

from Text_Processing import Trigger


#%%
class TestSimpleTriggers(unittest.TestCase):

    def file_lines(self, test_file):
        with open(test_file) as file:
            for line in file:
                yield line

    def setUp(self):
        base_path = Path.cwd()
        test_file = base_path / 'trigger_test_text.txt'
        #self.test_lines = self.file_lines()
        self.context = {
            'File Name': test_file.name,
            'File Path': test_file.parent,
            'Line Count': 0
            }

    def test_simple_trigger(self):
        s_trigger = Trigger(['Structure:'], name='End of Plan Info')
        line = 'Structure: PRV5 SpinalCanal'
        is_break = s_trigger.evaluate(line, **self.context)
        event = s_trigger.event.test_value
        self.assertTrue(is_break)
        self.assertEqual(event, 'Structure:')

    def test_multi_string_trigger(self):
        plan_trigger = Trigger(['Plan:', 'Plan sum:'])
        line = 'Plan sum: Plan Sum'
        is_break = plan_trigger.evaluate(line, **self.context)
        event = plan_trigger.event.test_value
        self.assertTrue(is_break)
        self.assertEqual(event, 'Plan sum:')

    def test_not_trigger(self):
        plan_trigger = Trigger(['Plan:', 'Plan sum:'])
        line = 'Comment              : DVHs for a plan sum'
        is_break= plan_trigger.evaluate(line, **self.context)
        event = plan_trigger.event.test_value
        self.assertFalse(is_break)
        self.assertIsNone(event)

    def test_info_trigger(self):
        info_trigger = Trigger(['% for dose (%):'])
        line = '% for dose (%): 100.0'
        is_break = info_trigger.evaluate(line, **self.context)
        event = info_trigger.event.test_value
        self.assertTrue(is_break)
        self.assertEqual(event, '% for dose (%):')

class TestReTriggers(unittest.TestCase):

    def file_lines(self, test_file):
        with open(test_file) as file:
            for line in file:
                yield line

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
        self.re_pattern = re.compile(prescribed_dose_pattern)


    def test_re_dose_trigger(self):
        dose_trigger = Trigger(self.re_pattern, name='Prescribed Dose')
        line = 'Prescribed dose [cGy]: 5000.0'
        results = {
            'unit': 'cGy',
            'dose': '5000.0'
            }
        is_break = dose_trigger.evaluate(line, **self.context)
        event = dose_trigger.event.test_value
        self.assertTrue(is_break)
        self.assertIsNotNone(event)
        self.assertIsInstance(event, re.Match)
        self.assertDictEqual(event.groupdict(),results)


    def test_re_no_dose_trigger(self):
        dose_trigger = Trigger(self.re_pattern, name='Prescribed Dose')
        line = 'Prescribed dose [cGy]: not defined'
        results = {
            'unit': 'cGy',
            'dose': 'not defined'
            }
        is_break = dose_trigger.evaluate(line, **self.context)
        event = dose_trigger.event.test_value
        self.assertTrue(is_break)
        self.assertIsNotNone(event)
        self.assertIsInstance(event, re.Match)
        self.assertDictEqual(event.groupdict(),results)


    def test_not_trigger(self):
        dose_trigger = Trigger(self.re_pattern, name='Prescribed Dose')
        line = 'Comment              : DVHs for a plan sum'
        is_break = dose_trigger.evaluate(line, **self.context)
        event = dose_trigger.event.test_value
        self.assertFalse(is_break)
        self.assertIsNone(event)


if __name__ == '__main__':
    unittest.main()
