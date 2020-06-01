import unittest
from data_utilities import *

class Test_value2num(unittest.TestCase):
    def test_value2num_SSD(self):
        '''Test that value2num works with '100.00 cm'
        '''
        value = '100.00 cm'
        number = value2num(value)
        self.assertEqual(number, 100)

    def test_value2num_degrees(self):
        '''Test that value2num works with degrees
        '''
        value = '0.5 °'
        number = value2num(value)
        self.assertEqual(number, 0.5)

    @unittest.skip("Not Implimented")
    def test_value2num_percent(self):
        '''Test that value2num works with percent
        '''
        value = '0.60%'
        number = value2num(value)
        self.assertEqual(number, 0.006)

    def test_value2num_multi_space(self):
        '''Test that value2num works with multiple spaces
        '''
        value = '0.39 cm - 0.39 cm'
        number = value2num(value)
        self.assertEqual(number, 0.39)

    def test_value2num_time(self):
        '''Test that value2num works with time
        '''
        value = '8:39 AM'
        number = value2num(value)
        self.assertEqual(number, '8:39 AM')

    def test_value2num_date(self):
        '''Test that value2num works with date
        '''
        value = '05-09-18'
        number = value2num(value)
        self.assertEqual(number, '05-09-18')

    def test_value2num_text(self):
        '''Test that value2num works with no initial number
        '''
        value = 'TR3'
        number = value2num(value)
        self.assertEqual(number, 'TR3')

if __name__ == '__main__':
    unittest.main()
