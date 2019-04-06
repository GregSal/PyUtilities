'''Basic CustomVariable class object tests.
'''
import unittest
from custom_variable_sets import IntegerV
from custom_variable_sets import NotValidError, UpdateError, UnMatchedValuesError


class TestIntegerV(unittest.TestCase):
    '''Test IntegerV CustomVariable subclass.
    '''
    def test_init(self):
        '''Verify that IntegerV initializes with integer value.
        '''
        int_var = IntegerV(9)
        self.assertEqual(int_var.value, 9)

    def test_blank(self):
        '''Verify that IntegerV initializes with no value.
        '''
        int_var = IntegerV()
        self.assertIsNone(int_var.value)

    def test_name(self):
        '''Verify the name is the CustomVariable class name.
        '''
        int_var = IntegerV(0)
        self.assertEqual(int_var.name, 'IntegerV')

    def test_int_float(self):
        '''Verify that IntegerV initializes with integer of type float.
        '''
        int_var = IntegerV(3.0)
        self.assertEqual(int_var.value, 3)

    def test_int_str(self):
        '''Verify that IntegerV initializes with a string representation of
        an integer.
        '''
        int_var = IntegerV('3.0')
        self.assertEqual(int_var.value, 3)

    def test_not_number(self):
        '''Verify that initializing with a string raises an error.
        '''
        with self.assertRaises(NotValidError):
            IntegerV('Test String')

    def test_not_int(self):
        '''Verify that initializing with a non-integer number raises an error.
        '''
        with self.assertRaises(NotValidError):
            IntegerV(2.3)

    def test_max_value_check(self):
        '''Verify that the maximum value check is functional
        '''
        int_var = IntegerV(**{'max_value': 12})
        int_var.value = 12
        self.assertTrue(int_var == 12)
        with self.assertRaises(NotValidError):
            int_var.value = 13

    def test_min_value_check(self):
        '''Verify that the minimum value check is functional
        '''
        int_var = IntegerV(**{'min_value': 3})
        int_var.value = 3
        self.assertTrue(int_var == 3)
        with self.assertRaises(NotValidError):
            int_var.value = 2

    def test_too_high_message(self):
        '''Verify that trying to set a value that exceeds the maximum value
        returns the appropriate error message.
        '''
        max_value = 99
        test_value = 100
        int_var = IntegerV(**{'max_value': max_value})
        error_message = str(test_value) + ' is greater than the maximum '
        error_message += 'allowable value of ' + str(max_value) + '.'
        try:
            int_var.value = test_value
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
        int_var = IntegerV(**{'min_value': min_value})
        error_message = str(test_value) + ' is less than the minimum '
        error_message += 'allowable value of ' + str(min_value) + '.'
        try:
            int_var.value = test_value
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_range_value_check(self):
        '''Test a combined maximum and minimum value check.
        '''
        int_var = IntegerV(**{'min_value': 1,
                                'max_value': 5})
        int_var.value = 3
        self.assertTrue(int_var == 3)
        int_var.value = 1
        self.assertTrue(int_var == 1)
        int_var.value = 5
        self.assertTrue(int_var == 5)
        with self.assertRaises(NotValidError):
            int_var.value = 0
        with self.assertRaises(NotValidError):
            int_var.value = 6

    def test_negative_range_value_check(self):
        '''Test a combined maximum and minimum value check.
        '''
        int_var = IntegerV(**{'min_value': -7,
                                'max_value': -5})
        int_var.value = -5
        self.assertTrue(int_var == -5)
        int_var.value = -7
        self.assertTrue(int_var == -7)
        with self.assertRaises(NotValidError):
            int_var.value = -8
        with self.assertRaises(NotValidError):
            int_var.value = 6

    def test_zero_cross_range_value_check(self):
        '''Test a combined maximum and minimum value check.
        '''
        int_var = IntegerV(**{'min_value': -2,
                                'max_value': 2})
        int_var.value = 0
        self.assertTrue(int_var == 0)
        int_var.value = 1
        self.assertTrue(int_var == 1)
        with self.assertRaises(NotValidError):
            int_var.value = -3
        with self.assertRaises(NotValidError):
            int_var.value = 3

    def test_bad_range_check(self):
        '''Test that an impossible number range raises an error.
        '''
        with self.assertRaises(UpdateError):
            IntegerV(**{'min_value': 5, 'max_value': 1})

    def test_group_member(self):
        '''Verify that a member of the value set is a valid value.
        '''
        int_var = IntegerV(**{'value_set': [1, 3, 5]})
        int_var.value = 1
        self.assertEqual(int_var, 1)

    def test_not_group_member(self):
        '''Verify that trying to set a value that is not a member of the
        value set raises NotValidError.
        '''
        int_var = IntegerV(**{'value_set': [1, 3, 5]})
        with self.assertRaises(NotValidError):
            int_var.value = 2

    def test_not_member_message(self):
        '''Verify that trying to set a value that is not a member of the
        value set returns the appropriate error message.
        '''
        int_var = IntegerV(**{'value_set': [1, 3, 5]})
        error_message = '2 is an invalid value for IntegerV.\n\t'
        error_message += 'Possible values are: ' + str({1, 3, 5})
        try:
            int_var.value = 2
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_add_group_member(self):
        '''Verify that it is possible to add an item to the set of possible
        values.
        '''
        int_var = IntegerV(**{'value': 1, 'value_set': [1, 3, 5]})
        int_var.add_items(7)
        int_var.value = 7
        self.assertEqual(int_var.value, 7)

    def test_add_list_of_group_members(self):
        '''Verify that it is possible to add a list of possible values.
        '''
        int_var = IntegerV(**{'value': 1, 'value_set': [1, 2, 3]})
        int_var.add_items([4,5])
        int_var.value = 5
        self.assertEqual(int_var.value, 5)

    def test_add_range_as_value_set(self):
        '''Verify that it is possible to add a range to the set of
        possible values.
        '''
        int_var = IntegerV(**{'value': 2, 'value_set': [0, 2]})
        int_var.add_items(range(2,8,2))
        int_var.value = 6
        self.assertEqual(int_var.value, 6)

    def test_set_range_as_value_set(self):
        '''Verify that it is possible to supply a range as the set of
        possible values.
        '''
        int_var = IntegerV(**{'value': 2, 'value_set': range(2,8,2)})
        int_var.value = 4
        self.assertEqual(int_var.value, 4)

    def test_drop_group_member(self):
        '''Verify that it is possible to remove an item from the set of
        possible values.
        '''
        int_var = IntegerV(**{'value': 1, 'value_set': [1, 3, 5, 7]})
        int_var.drop_item(3)
        with self.assertRaises(NotValidError):
            int_var.value = 3

    def test_cant_drop_existing_group_member(self):
        '''Verify that trying to remove the current value from the set of
        possible values raises UpdateError.
        '''
        int_var = IntegerV(**{'value': 5, 'value_set': [1, 3, 5, 7]})
        with self.assertRaises(UpdateError):
            int_var.drop_item(5)

    def test_drop_non_existing_group_member(self):
        '''Verify that trying to remove a non-existing value from the set of
        possible values raises UnMatchedValuesError.
        '''
        int_var = IntegerV(**{'value': 5, 'value_set': [1, 3, 5, 7]})
        with self.assertRaises(UnMatchedValuesError):
            int_var.drop_item(2)

    def test_add_invalid_group_member(self):
        '''Verify that trying to add an invalid item to the set of possible
        values raises NotValidError.
        '''
        int_var = IntegerV(**{'value': 5, 'value_set': [1, 3, 5, 7]})
        with self.assertRaises(NotValidError):
            int_var.add_items(1.5)

    def test_invalid_group_member(self):
        '''Verify that trying to initialize with an invalid item int the set
        of possible values raises NotValidError.
        '''
        with self.assertRaises(NotValidError):
            IntegerV(**{'value_set': ['one', 2]})

    def test_add_value_at_init(self):
        '''Verify that trying to initialize with a value that is not in the
        set of possible values causes the value to be added to the set of
        possible values.
        '''
        int_var = IntegerV(**{'value': 0, 'value_set': [1, 3]})
        self.assertSetEqual(int_var.value_set, {0, 1, 3})

    def test_too_large_number_at_init(self):
        '''Verify that trying to initialize with a value that is greater than
        the maximum value raises UpdateError.
        '''
        with self.assertRaises(UpdateError):
            IntegerV(**{'value': 4, 'max_value': 3})

    def test_too_small_number_at_init(self):
        '''Verify that trying to initialize with a value that is less than
        the minimum value raises UpdateError.
        '''
        with self.assertRaises(UpdateError):
            IntegerV(**{'value': 2, 'min_value': 3})

    def test_change_max_length(self):
        '''Verify that the maximum value can be changed.
        '''
        int_var = IntegerV(**{'max_value': 3})
        int_var.value = 1
        self.assertTrue(int_var == 1)
        int_var.max_value = 5
        int_var.value = 5
        self.assertTrue(int_var == 5)

    def test_change_min_length(self):
        '''Verify that the minimum value can be changed.
        '''
        int_var = IntegerV(**{'min_value': 5})
        int_var.value = 6
        self.assertTrue(int_var == 6)
        int_var.min_value = 2
        int_var.value = 2
        self.assertTrue(int_var == 2)

    def test_cant_change_max_value(self):
        '''Verify that trying to change the maximum value to be less than
        the current value raises NotValidError.
        '''
        int_var = IntegerV(**{'value': 3, 'max_value': 3})
        self.assertTrue(int_var == 3)
        with self.assertRaises(UpdateError):
            int_var.max_value = 1

    def test_cant_change_min_value(self):
        '''Verify that trying to change the minimum value to be more than
        the current value raises NotValidError.
        '''
        int_var = IntegerV(**{'value': 3, 'min_value': 3})
        self.assertTrue(int_var == 3)
        with self.assertRaises(UpdateError):
            int_var.min_value = 4

    @unittest.skip('Not Yet implemented')
    def test_group_overides_length(self):
        '''Verify that when both a value_set and max_length are given the
        value_set is used and the max_length is ignored.
        '''
        int_var = IntegerV(**{'value': 4, 'min_value': 2, 'max_value': 8,
                                'value_set': range(2,8,2)})
        int_var.add_items(10)
        int_var.value = 10
        self.assertEqual(int_var.value, 10)

    @unittest.skip('Test not working')
    def test_copy(self):
        '''Verify that copy() returns an exact copy of the instance.
        '''
        attr_dict = {'_name': 'Test_Integer_Value',
                     '_value': 1,
                     '_value_set': [0, 1,2],
                     '_max_length': 9,
                     'default': 0}
        int_var = IntegerV(**attr_dict)
        copied_var = int_var.copy()
        attr_dict.update({'_messages': int_var._messages})
        self.maxDiff = None
        self.assertDictEqual(copied_var.__dict__, attr_dict)

    def test_display(self):
        '''Verify that disp() returns a formatted string summary of the
        current state.
        '''
        attr_dict = {'_name': 'Test_Integer_Value',
                     '_value': 1,
                     '_value_set': [0, 1,2],
                     '_max_length': 9,
                     'default': 0}
        int_var = IntegerV(**attr_dict)
        display = 'Test_Integer_Value CustomVariable of class IntegerV,\n'
        display += '\tCurrent value is:\t1\n'
        display += '\tDefault value is:\t0\n'
        display += '\tPossible values are:\t'
        display += str([0, 1, 2])
        # display += '\n\tMaximum length is:\t9'
        self.assertEqual(int_var.disp(), display)


if __name__ == '__main__':
    unittest.main()
