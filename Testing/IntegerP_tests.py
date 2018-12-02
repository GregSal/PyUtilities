'''Basic Parameter class object tests.
'''
import unittest
from parameters import IntegerP
from parameters import NotValidError, UpdateError, UnMatchedValuesError


class TestIntegerP(unittest.TestCase):
    '''Test IntegerP Parameter subclass.
    '''
    def test_init(self):
        '''Verify that IntegerP initializes with integer value.
        '''
        int_param = IntegerP(9)
        self.assertEqual(int_param.value, 9)

    def test_blank(self):
        '''Verify that IntegerP initializes with no value.
        '''
        int_param = IntegerP()
        self.assertIsNone(int_param.value)

    def test_name(self):
        '''Verify the name is the Parameter class name.
        '''
        int_param = IntegerP(0)
        self.assertEqual(int_param.name, 'IntegerP')

    def test_int_float(self):
        '''Verify that IntegerP initializes with integer of type float.
        '''
        int_param = IntegerP(3.0)
        self.assertEqual(int_param.value, 3)

    def test_int_str(self):
        '''Verify that IntegerP initializes with a string representation of
        an integer.
        '''
        int_param = IntegerP('3.0')
        self.assertEqual(int_param.value, 3)

    def test_not_number(self):
        '''Verify that initializing with a string raises an error.
        '''
        with self.assertRaises(NotValidError):
            int_param = IntegerP('Test String')

    def test_not_int(self):
        '''Verify that initializing with a non-integer number raises an error.
        '''
        with self.assertRaises(NotValidError):
            int_param = IntegerP(2.3)

    def test_max_value_check(self):
        '''Verify that the maximum value check is functional
        '''
        int_param = IntegerP(**{'max_value': 12})
        int_param.value = 12
        self.assertTrue(int_param == 12)
        with self.assertRaises(NotValidError):
            int_param.value = 13

    def test_min_value_check(self):
        '''Verify that the minimum value check is functional
        '''
        int_param = IntegerP(**{'min_value': 3})
        int_param.value = 3
        self.assertTrue(int_param == 3)
        with self.assertRaises(NotValidError):
            int_param.value = 2

    def test_too_high_message(self):
        '''Verify that trying to set a value that exceeds the maximum value
        returns the appropriate error message.
        '''
        max_value = 99
        test_value = 100
        int_param = IntegerP(**{'max_value': max_value})
        error_message = str(test_value) + ' is larger than the maximum '
        error_message += 'allowable value of ' + str(max_value) + '.'
        try:
            int_param.value = test_value
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_too_low_message(self):
        '''Verify that trying to set a value that is less than the minimum
        value returns the appropriate error message.
        '''
        min_value = 51
        test_value = 50
        int_param = IntegerP(**{'min_value': min_value})
        error_message = str(test_value) + ' is less than the maximum '
        error_message += 'allowable value of ' + str(min_value) + '.'
        try:
            int_param.value = test_value
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_range_value_check(self):
        '''Test a combined maximum and minimum value check.
        '''
        int_param = IntegerP(**{'min_value': 1,
                                'max_value': 5})
        int_param.value = 3
        self.assertTrue(int_param == 3)
        int_param.value = 1
        self.assertTrue(int_param == 1)
        int_param.value = 5
        self.assertTrue(int_param == 5)
        with self.assertRaises(NotValidError):
            int_param.value = 0
        with self.assertRaises(NotValidError):
            int_param.value = 6

    def test_negative_range_value_check(self):
        '''Test a combined maximum and minimum value check.
        '''
        int_param = IntegerP(**{'min_value': -7,
                                'max_value': -5})
        int_param.value = -5
        self.assertTrue(int_param == -5)
        int_param.value = -7
        self.assertTrue(int_param == -7)
        with self.assertRaises(NotValidError):
            int_param.value = -8
        with self.assertRaises(NotValidError):
            int_param.value = 6

    def test_zero_cross_range_value_check(self):
        '''Test a combined maximum and minimum value check.
        '''
        int_param = IntegerP(**{'min_value': -2,
                                'max_value': 2})
        int_param.value = 0
        self.assertTrue(int_param == 0)
        int_param.value = 1
        self.assertTrue(int_param == 1)
        with self.assertRaises(NotValidError):
            int_param.value = -3
        with self.assertRaises(NotValidError):
            int_param.value = 3

    def test_bad_range_check(self):
        '''Test that an impossible number range raises an error.
        '''
        with self.assertRaises(UpdateError):
            int_param = IntegerP(**{'min_value': 5,
                                    'max_value': 1})

    def test_group_member(self):
        '''Verify that a member of the value set is a valid value.
        '''
        int_param = IntegerP(**{'value_set': [1, 3, 5]})
        int_param.value = 1
        self.assertEqual(int_param, 1)

    def test_not_group_member(self):
        '''Verify that trying to set a value that is not a member of the
        value set raises NotValidError.
        '''
        int_param = IntegerP(**{'value_set': [1, 3, 5]})
        with self.assertRaises(NotValidError):
            int_param.value = 2

    def test_not_member_message(self):
        '''Verify that trying to set a value that is not a member of the
        value set returns the appropriate error message.
        '''
        int_param = IntegerP(**{'value_set': [1, 3, 5]})
        error_message = '2 is an invalid value for IntegerP.\n\t'
        error_message += 'Possible values are: ' + str({1, 3, 5})
        try:
            int_param.value = 2
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_add_group_member(self):
        '''Verify that it is possible to add an item to the set of possible
        values.
        '''
        int_param = IntegerP(**{'value': 1, 'value_set': [1, 3, 5]})
        int_param.add_items(7)
        int_param.value = 7
        self.assertEqual(int_param.value, 7)

    def test_add_list_of_group_members(self):
        '''Verify that it is possible to add a list of possible values.
        '''
        int_param = IntegerP(**{'value': 1, 'value_set': [1, 2, 3]})
        int_param.add_items(4,5)
        int_param.value = 5
        self.assertEqual(int_param.value, 5)

    def test_add_range_as_value_set(self):
        '''Verify that it is possible to supply a range as the set of
        possible values.
        '''
        int_param = IntegerP(**{'value': 2, 'value_set': [0, 2]})
        int_param.add_items(range(2,8,2))
        int_param.value = 6
        self.assertEqual(int_param.value, 6)

    def test_add_range_as_value_set(self):
        '''Verify that it is possible to supply a range as the set of
        possible values.
        '''
        int_param = IntegerP(**{'value': 2, 'value_set': range(2,8,2)})
        int_param.value = 4
        self.assertEqual(int_param.value, 4)

    def test_drop_group_member(self):
        '''Verify that it is possible to remove an item from the set of
        possible values.
        '''
        int_param = IntegerP(**{'value': 1, 'value_set': [1, 3, 5, 7]})
        int_param.drop_item(3)
        with self.assertRaises(NotValidError):
            int_param.value = 3

    def test_cant_drop_existing_group_member(self):
        '''Verify that trying to remove the current value from the set of
        possible values raises UpdateError.
        '''
        int_param = IntegerP(**{'value': 5, 'value_set': [1, 3, 5, 7]})
        with self.assertRaises(UpdateError):
            int_param.drop_item(5)

    def test_add_invalid_group_member(self):
        '''Verify that trying to add an invalid item to the set of possible
        values raises NotValidError.
        '''
        int_param = IntegerP(**{'value': 5, 'value_set': [1, 3, 5, 7]})
        with self.assertRaises(NotValidError):
            int_param.add_item(1.5)

    def test_invalid_group_member(self):
        '''Verify that trying to initialize with an invalid item int the set
        of possible values raises NotValidError.
        '''
        with self.assertRaises(NotValidError):
            IntegerP(**{'value_set': ['one', 2]})

    def test_add_value_at_init(self):
        '''Verify that trying to initialize with a value that is not in the
        set of possible values causes the value to be added to the set of
        possible values.
        '''
        int_param = IntegerP(**{'value': 0, 'value_set': [1, 3]})
        self.assertSetEqual(int_param.value_set, {0, 1, 3})

    def test_too_large_number_at_init(self):
        '''Verify that trying to initialize with a value that is greater than
        the maximum value raises UpdateError.
        '''
        with self.assertRaises(UpdateError):
            IntegerP(**{'value': 4, 'max_value': 3})

    def test_too_small_number_at_init(self):
        '''Verify that trying to initialize with a value that is less than
        the minimum value raises UpdateError.
        '''
        with self.assertRaises(UpdateError):
            IntegerP(**{'value': 2, 'min_value': 3})

    def test_change_max_length(self):
        '''Verify that the maximum value can be changed.
        '''
        int_param = IntegerP(**{'max_value': 3}})
        int_param.value = 1
        self.assertTrue(int_param == 1)
        int_param.max_value = 5
        string_param.value = 5
        self.assertTrue(string_param == 5)

    def test_change_max_length(self):
        '''Verify that the minimum value can be changed.
        '''
        int_param = IntegerP(**{'min_value': 5})
        int_param.value = 6
        self.assertTrue(int_param == 6)
        int_param.min_value = 2
        string_param.value = 2
        self.assertTrue(string_param == 2)

    def test_cant_change_max_value(self):
        '''Verify that trying to change the maximum value to be less than
        the current value raises NotValidError.
        '''
        int_param = IntegerP(**{'value': 3, 'max_value': 3})
        self.assertTrue(int_param == 3)
        with self.assertRaises(UpdateError):
            int_param.max_value = 1

    def test_cant_change_max_value(self):
        '''Verify that trying to change the minimum value to be more than
        the current value raises NotValidError.
        '''
        int_param = IntegerP(**{'value': 3, 'min_value': 3})
        self.assertTrue(int_param == 3)
        with self.assertRaises(UpdateError):
            int_param.min_value = 4

    def test_group_overides_length(self):
        '''Verify that when both a value_set and max_length are given the
        value_set is used and the max_length is ignored.
        '''
        int_param = IntegerP(**{'value': 4, 'min_value': 2, 'max_value': 8,
                                'value_set': range(2,8,2)})
        int_param.add_item(10)
        int_param.value = 10
        self.assertEqual(int_param.value, 10)

    def test_copy(self):
        '''Verify that copy() returns an exact copy of the instance.
        '''
        attr_dict = {'_name': 'Test_Integer_Value',
                     '_value': 1,
                     '_value_set': [0, 1,2],
                     '_max_length': 9,
                     'default': 0}
        int_param = IntegerP(**attr_dict)
        copied_param = int_param.copy()
        attr_dict.update({'_messages': int_param._messages})
        self.maxDiff = None
        self.assertDictEqual(copied_param.__dict__, attr_dict)

    def test_display(self):
        '''Verify that disp() returns a formatted string summary of the
        current state.
        '''
        attr_dict = {'_name': 'Test_Integer_Value',
                     '_value': 1,
                     '_value_set': [0, 1,2],
                     '_max_length': 9,
                     'default': 0}
        int_param = IntegerP(**attr_dict)
        display = 'Test_Integer_Value parameter of class IntegerP,\n'
        display += '\tCurrent value is:\t1\n'
        display += '\tDefault value is:\t0\n'
        display += '\tPossible values are:\t'
        display += str({0, 1, 2})
        # display += '\n\tMaximum length is:\t9'
        self.assertEqual(int_param.disp(), display)


if __name__ == '__main__':
    unittest.main()
