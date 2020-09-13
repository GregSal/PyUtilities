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
        self.buffer_size = 5
        self.test_gen = BufferedIterator(self.test_lines,
                                         buffer_size=self.buffer_size)
        self.test_iter = (line for line in self.test_gen)

    def test_backup(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        #Backup 2 lines
        self.test_gen.step_back = 2
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, yielded_lines[-2])

    def test_backup_error(self):
        # Step through 1st line
        yielded_lines = list()
        for i in range(1):
            yielded_lines.append(self.test_iter.__next__())
        #Try to Backup 2 lines
        with self.assertRaises(ValueError):
            self.test_gen.step_back = 2

    def test_backup_beyond_buffer_error(self):
        #  Step through more lines than buffer size
        yielded_lines = list()
        for i in range(self.buffer_size+1):
            yielded_lines.append(self.test_iter.__next__())
        #Try to Backup 2 lines
        with self.assertRaises(ValueError):
            self.test_gen.step_back = self.buffer_size+1

    def test_backup_method(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        #Backup 2 lines
        self.test_gen.backup(2)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, yielded_lines[-2])

    def test_look_back(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        #Backup 2 lines
        previous_line = self.test_gen.look_back(2)
        self.assertEqual(previous_line, yielded_lines[-2])
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, self.test_lines[3 + 1])

    def test_look_ahead(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        #Look 2 lines ahead
        future_line = self.test_gen.look_ahead(2)
        # Step through 2 more lines
        for i in range(2):
            yielded_lines.append(self.test_iter.__next__())
        self.assertEqual(future_line, yielded_lines[-1])

    def test_skip(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        previous_line = yielded_lines[-1]
        #Skip 3 lines ahead
        self.test_gen.skip(3)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, self.test_lines[3+3+1])
        #Backup 2 lines
        self.test_gen.backup(2)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, previous_line)


    def test_advance(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):
            yielded_lines.append(self.test_iter.__next__())
        previous_line = yielded_lines[-1]
        #Advance 3 lines ahead
        self.test_gen.advance(3)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, self.test_lines[3+3+1])
        #Backup 3+2 lines
        self.test_gen.backup(3+2)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, previous_line)

    def test_max_backup(self):
        # Advance to fill the buffer
        yielded_lines = list()
        for i in range(self.buffer_size):
            yielded_lines.append(self.test_iter.__next__())
        #Backup the entire buffer
        self.test_gen.backup(2)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, yielded_lines[1-self.buffer_size])


if __name__ == '__main__':
    unittest.main()
