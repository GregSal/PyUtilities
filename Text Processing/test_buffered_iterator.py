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
    def setUp(self):
        self.test_lines = TEST_LINES.splitlines()
        self.test_gen = BufferedIterator(self.test_lines)
        self.test_iter = (line for line in self.test_gen)

    def test_backup(self):
        # Advance 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        #Backup 2 lines
        self.test_gen.step_back = 2
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, yielded_lines[-2])

    def test_backup_error(self):
        # Advance 1 line
        yielded_lines = list()
        for i in range(1):
            yielded_lines.append(self.test_iter.__next__())
        #Try to Backup 2 lines
        with self.assertRaises(ValueError):
            self.test_gen.step_back = 2

    def test_backup_method(self):
        # Advance 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        #Backup 2 lines
        self.test_gen.backup(2)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, yielded_lines[-2])

    def test_peak(self):
        # Advance 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        #Look 2 lines ahead
        future_line = self.test_gen.peak(2)
        # Advance 2 more lines
        for i in range(2):
            yielded_lines.append(self.test_iter.__next__())
        self.assertEqual(future_line, yielded_lines[-1])

    def test_skip(self):
        # Advance 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        #Look skip 3 lines ahead
        self.test_gen.skip(3)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, self.test_lines[3+3+1])



if __name__ == '__main__':
    unittest.main()
