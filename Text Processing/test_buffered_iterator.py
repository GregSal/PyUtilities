import unittest
from pathlib import Path

from Text_Processing import BufferedIterator

#%% Test Text
TEST_LINES = '''Line 0
First Line
Second Line
Third Line
Fourth Line
Fifth Line
~Line 6
Line 7
Line 8
Line 9
Line 10
Line 11
Line 12
'''
# from pprint import pprint
# pprint(test_lines.splitlines())



#%%  Prescribed dose parse tests
class TestBufferedIterator(unittest.TestCase):
    def test_backup(self):
        test_lines = BufferedIterator(TEST_LINES)
        # Advance 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(test_lines.__next__())
        #Backup 2 lines
        test_lines.step_back = 2
        next_line = test_lines.__next__()
        self.assertEqual(next_line, yielded_lines[-2])

    def test_backup_error(self):
        test_lines = BufferedIterator(TEST_LINES)
        # Advance 1 line
        yielded_lines = list()
        for i in range(1):
            yielded_lines.append(test_lines.__next__())
        #Try to Backup 2 lines
        with self.assertRaises(ValueError):
            test_lines.step_back = 2




if __name__ == '__main__':
    unittest.main()
