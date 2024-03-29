'''StringV CustomVariable class object tests.
'''
import unittest
from custom_variable_sets import StringV
from custom_variable_sets import NotValidError, UpdateError, UnMatchedValuesError


class TestStringV(unittest.TestCase):
    '''Test instance creation passing nothing.
    '''
    def test_init(self):
        '''Verify that StringV initializes with string value.
        '''
        string_var = StringV('Test String')
        self.assertEqual(string_var, 'Test String')

    def test_blank(self):
        '''Verify that StringV initializes with string value.
        '''
        string_var = StringV('')
        self.assertTrue(string_var == '')

    def test_name(self):
        '''Verify the name is the CustomVariable class name.
        '''
        string_var = StringV('Test String')
        self.assertEqual(string_var.name, 'StringV')

    def test_length_check(self):
        '''Verify that the string length check is functional
        '''
        length8string = '12345678'
        length9string = '123456789'
        string_var = StringV(**{'max_length': 8})
        string_var.value = length8string
        with self.assertRaises(NotValidError):
            string_var.value = length9string

    def test_too_long_message(self):
        '''Verify that trying to set a value that exceeds the maximum length
        returns the appropriate error message.
        '''
        length9string = '123456789'
        string_var = StringV(**{'max_length': 8})
        error_message = length9string + ' is longer than the maximum '
        error_message += 'allowable length of 8.'
        try:
            string_var.value = length9string
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_group_member(self):
        '''Verify that a member of the value set is a valid value.
        '''
        string_var = StringV(**{'value_set': ['one', 'two']})
        string_var.value = 'one'
        self.assertEqual(string_var, 'one')

    def test_not_group_member(self):
        '''Verify that trying to set a value that is not a member of the
        value set raises NotValidError.
        '''
        string_var = StringV(**{'value_set': ['one', 'two']})
        with self.assertRaises(NotValidError):
            string_var.value = 'three'

    def test_not_member_message(self):
        '''Verify that trying to set a value that is not a member of the
        value set returns the appropriate error message.
        '''
        string_var = StringV(**{'value_set': ['one', 'two']})
        error_message = 'three is an invalid value for StringV.\n\t'
        error_message += 'Possible values are: ' + str({'one', 'two'})
        try:
            string_var.value = 'three'
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_add_group_member(self):
        '''Verify that it is possible to add an item to the set of possible
        values.
        '''
        string_var = StringV(**{'value': 'one',
                                  'value_set': ['one', 'two']})
        string_var.add_item('three')
        string_var.value = 'three'
        self.assertEqual(string_var.value, 'three')

    def test_drop_group_member(self):
        '''Verify that it is possible to remove an item from the set of
        possible values.
        '''
        string_var = StringV(**{'value': 'one',
                                  'value_set': ['one', 'two', 'three']})
        string_var.drop_item('three')
        with self.assertRaises(NotValidError):
            string_var.value = 'three'

    def test_cant_drop_existing_group_member(self):
        '''Verify that trying to remove the current value from the set of
        possible values raises UpdateError.
        '''
        string_var = StringV(**{'value': 'three',
                                  'value_set': ['one', 'two', 'three']})
        with self.assertRaises(UpdateError):
            string_var.drop_item('three')

    def test_drop_non_existing_group_member(self):
        '''Verify that trying to remove a non-existing value from the set of
        possible values raises UnMatchedValuesError.
        '''
        string_var = StringV(**{'value': 'three',
                                  'value_set': ['one', 'two', 'three']})
        with self.assertRaises(UnMatchedValuesError):
            string_var.drop_item('four')

    def test_add_invalid_group_member(self):
        '''Verify that trying to add an invalid item to the set of possible
        values raises NotValidError.
        '''
        string_var = StringV(**{'value_set': ['one', 'two']})
        with self.assertRaises(NotValidError):
            string_var.add_item(1)

    def test_invalid_group_member(self):
        '''Verify that trying to initialize with an invalid item int the set
        of possible values raises NotValidError.
        '''
        with self.assertRaises(NotValidError):
            StringV(**{'value_set': ['one', 2]})

    def test_add_value_at_init(self):
        '''Verify that trying to initialize with a value that is not in the
        set of possible values causes the value to be added to the set of
        possible values.
        '''
        string_var = StringV(**{'value': 'three',
                                  'value_set': ['one', 'two']})
        self.assertSetEqual(string_var.value_set, {'one', 'two', 'three'})

    def test_invalid_length_at_init(self):
        '''Verify that trying to initialize with a value that is longer that the
        max string length raises UpdateError.
        '''
        length9string = '123456789'
        with self.assertRaises(UpdateError):
            StringV(**{'value': length9string, 'max_length': 8})

    def test_change_max_length(self):
        '''Verify that the max string length can be changed.
        '''
        length8string = '12345678'
        length9string = '123456789'
        string_var = StringV(**{'max_length': 8})
        string_var.value = length8string
        self.assertTrue(string_var == length8string)
        string_var.max_length = 9
        string_var.value = length9string
        self.assertTrue(string_var == length9string)

    def test_cant_change_max_length(self):
        '''Verify that trying to change the max string length to be less than
        The length of the current value raises NotValidError.
        '''
        length9string = '123456789'
        string_var = StringV(**{'value': length9string,
                                  'max_length': 9})
        self.assertTrue(string_var == length9string)
        with self.assertRaises(UpdateError):
            string_var.max_length = 8

    def test_group_overides_length(self):
        '''Verify that when both a value_set and max_length are given the
        value_set is used and the max_length is ignored.
        '''
        length8string = '12345678'
        length9string = '123456789'
        string_var = StringV(**{'value_set': [length8string],
                                  'max_length': 8})
        string_var.add_item(length9string)
        string_var.value = length9string
        self.assertEqual(string_var.value, length9string)

    @unittest.skip('Test Broken')
    def test_copy(self):
        '''Verify that copy() returns an exact copy of the instance.
        '''
        length8string = '12345678'
        length9string = '123456789'
        attr_dict = {'_name': 'Test_String_Value',
                     '_value': length9string,
                     '_value_set': [length8string, length9string],
                     '_max_length': 9,
                     'default': 'default_value'}
        string_var = StringV(**attr_dict)
        copied_param = string_var.copy()
        attr_dict.update({'_messages': string_var._messages})
        self.maxDiff = None
        self.assertDictEqual(copied_param.__dict__, attr_dict)

    def test_display(self):
        '''Verify that disp() returns a formatted string summary of the
        current state.
        '''
        length8string = '12345678'
        length9string = '123456789'
        attr_dict = {'name': 'Test_String_Value',
                     'value': length9string,
                     'value_set': [length8string, length9string],
                     'max_length': 9,
                     'default': 'default_value'}
        string_var = StringV(**attr_dict)
        display = 'Test_String_Value CustomVariable of class StringV,\n'
        display += '\tCurrent value is:\t123456789\n'
        display += '\tDefault value is:\tdefault_value\n'
        display += '\tPossible values are:\t'
        display += str({length8string, length9string})
        # display += '\n\tMaximum length is:\t9'
        self.assertEqual(string_var.disp(), display)


if __name__ == '__main__':
    unittest.main()
