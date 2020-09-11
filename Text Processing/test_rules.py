import unittest
from pathlib import Path
import re

from read_dvh_file import prescribed_dose_rule

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
# pprint(test_lines.splitlines())



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
