import unittest
from pathlib import Path
import re

from read_dvh_file import TextTrigger, ReTrigger


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
        plan_trigger = TextTrigger(['Plan:', 'Plan sum:'])
        line = 'Plan sum: Plan Sum'
        is_break, sentinel = plan_trigger.apply(self.context, line)
        self.assertTrue(is_break)
        self.assertEqual(sentinel, 'Plan sum:')

    def test_not_trigger(self):
        plan_trigger = TextTrigger(['Plan:', 'Plan sum:'])
        info_trigger = TextTrigger(['% for dose (%):'])
        s_trigger = TextTrigger(['Structure:'], name='End of Plan Info')
        line = 'Comment              : DVHs for a plan sum'
        is_break, sentinel = plan_trigger.apply(self.context, line)
        self.assertFalse(is_break)
        self.assertIsNone(sentinel)

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
        dose_trigger = ReTrigger(self.re_pattern, name='Prescribed Dose')
        line = 'Prescribed dose [cGy]: 5000.0'
        results = {
            'unit': 'cGy',
            'dose': '5000.0'
            }
        is_break, sentinel = dose_trigger.apply(self.context, line)
        self.assertTrue(is_break)
        self.assertIsNotNone(sentinel)
        self.assertIsInstance(sentinel, re.Match)
        self.assertDictEqual(sentinel.groupdict(),results)


    def test_re_no_dose_trigger(self):
        dose_trigger = ReTrigger(self.re_pattern, name='Prescribed Dose')
        line = 'Prescribed dose [cGy]: not defined'
        results = {
            'unit': 'cGy',
            'dose': 'not defined'
            }
        is_break, sentinel = dose_trigger.apply(self.context, line)
        self.assertTrue(is_break)
        self.assertIsNotNone(sentinel)
        self.assertIsInstance(sentinel, re.Match)
        self.assertDictEqual(sentinel.groupdict(),results)


    def test_not_trigger(self):
        dose_trigger = ReTrigger(self.re_pattern, name='Prescribed Dose')
        line = 'Comment              : DVHs for a plan sum'
        is_break, sentinel = dose_trigger.apply(self.context, line)
        self.assertFalse(is_break)
        self.assertIsNone(sentinel)


if __name__ == '__main__':
    unittest.main()
