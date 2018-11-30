'''Basic Parameter class object tests.
'''
import unittest
from parameters import StringP
from parameters import NotValidError


class TestStringP(unittest.TestCase):
    '''Test instance creation passing nothing.
    '''
    def test_init(self):
        '''Verify that StringP initializes with string value.
        '''
        string_param = StringP('Test String')
        self.assertEqual(string_param, 'Test String')

    def test_blank(self):
        '''Verify that StringP initializes with string value.
        '''
        string_param = StringP('')
        self.assertEqual(string_param, '')

    def test_name(self):
        '''Verify the name is the Parameter class name.
        '''
        string_param = StringP('Test String')
        self.assertEqual(string_param.name, 'StringP')

    def test_length_check(self):
        '''Verify that the string length check is functional
        '''
        length8string = '12345678'
        length9string = '123456789'
        string_param = StringP(**{'max_length': 8})
        string_param.value = length8string
        with self.assertRaises(NotValidError):
            string_param.value = length9string

    def test_too_long_message(self):
        '''Verify that trying to set a value that exceeds the maximum length
        returns the appriopriate error message.
        '''
        length9string = '123456789'
        string_param = StringP(**{'max_length': 8})
        error_message = (length9string + ' is longer than the maximum ' +
                        'allowable length of 8.')
        try:
            string_param.value = 'three'
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_group_member(self):
        '''Verify that a member of the value set is a valid value.
        '''
        string_param = StringP(**{'value_set': ['one', 'two']})
        string_param.value = 'one'
        self.assertEqual(string_param, 'one')

    def test_not_group_member(self):
        '''Verify that trying to set a value that is not a member of the
        value set raises NotValidError.
        '''
        string_param = StringP(**{'value_set': ['one', 'two']})
        with self.assertRaises(NotValidError):
            string_param.value = 'three'

    def test_not_member_message(self):
        '''Verify that trying to set a value that is not a member of the
        value set returns the appriopriate error message.
        '''
        string_param = StringP(**{'value_set': ['one', 'two']})
        error_message = 'StringP must be one of;\n'
        error_message += '["one", "two"]\n\tGot:\tthree'
        try:
            string_param.value = 'three'
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_add_group_member(self):
        '''Verify that it is possible to add an item to the set of possible
        values.
        '''
        string_param = StringP(**{'value': 'one',
                                'value_set': ['one', 'two']})
        string_param.add_item('three')
        self.assertEqual(string_param.value, 'three')

    def test_drop_group_member(self):
        '''Verify that it is possible to remove an item from the set of
        possible values.
        '''
        string_param = StringP(**{'value': 'one',
                                'value_set': ['one', 'two', 'three']})
        string_param.drop_item('three')

    def test_cant_drop_existing_group_member(self):
        '''Verify that trying to remove the current value from the set of
        possible values raises NotValidError.
        '''
        string_param = StringP(**{'value': 'three',
                                'value_set': ['one', 'two', 'three']})
        with self.assertRaises(NotValidError):
            string_param.drop_item('three')

    def test_add_invalid_group_member(self):
        '''Verify that trying to add an invalid item to the set of possible
        values raises NotValidError.
        '''
        string_param = StringP(**{'value_set': ['one', 'two']})
        with self.assertRaises(NotValidError):
            string_param.add_item(1)

    def test_invalid_group_member(self):
        '''Verify that trying to initialize with an invalid item int the set
        of possible values raises NotValidError.
        '''
        with self.assertRaises(NotValidError):
            string_param = StringP(**{'value_set': ['one', 2]})

    def test_invalid_value_at_init(self):
        '''Verify that trying to initialize with a value that is not in the
        set of possible values raises NotValidError.
        '''
        with self.assertRaises(NotValidError):
            string_param = StringP(**{'value': 'three',
                                    'value_set': ['one', 'two']})

    def test_invalid_length_at_init(self):
        '''Verify that trying to initialize with a value that is longer that the
        max string length raises NotValidError.
        '''
        length9string = '123456789'
        with self.assertRaises(NotValidError):
            string_param = StringP(**{'value': length9string,
                                    'max_length': 8})

    def test_change_max_length(self):
        '''Verify that the max string length can be changed.
        '''
        length8string = '12345678'
        length9string = '123456789'
        string_param = StringP(**{'max_length': 8})
        string_param.value = length8string
        self.assertEqual(string_param, length8string)
        string_param.max_length = 9
        string_param = StringP(**{'max_length': 8})
        string_param.value = length9string
        self.assertEqual(string_param, length9string)

    def test_cant_change_max_length(self):
        '''Verify that trying to change the max string length to be less than
        The length of the current value raises NotValidError.
        '''
        length9string = '123456789'
        string_param = StringP(**{'value': length9string,
                                    'max_length': 9})
        self.assertEqual(string_param, length9string)
        with self.assertRaises(NotValidError):
            string_param = StringP(**{'max_length': 8})

    def test_group_overides_length(self):
        '''Verify that trying to change the max string length to be less than
        The length of the current value raises NotValidError.
        '''
        length8string = '12345678'
        length9string = '123456789'
        string_param = StringP(**{'value': length9string,
                                'value_set': [length8string, length9string],
                                'max_length': 8})
        self.assertEqual(string_param, length9string)

    def test_copy(self):
        '''Verify that copy() returns an exact copy of the instance.
        '''
        length8string = '12345678'
        length9string = '123456789'
        attr_dict = {'name': 'Test_String_Value',
                     'value': length9string,
                     'value_set': [length8string, length9string],
                     'max_length': 8,
                     '_messages': StringP.initial_templates,
                     'default': 'default_value'}
        string_param = StringP(**attr_dict)
        copied_param = string_param.copy()
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
                     'max_length': 8,
                     '_messages': StringP.initial_templates,
                     'default': 'default_value'}
        string_param = StringP(**attr_dict)

        display = '{name} parameter of class {cls}P\n,'
        display += '\tCurrent Value is:\t{value}\n'
        display += '\tDefault value is:\t{default}\n'
        display += '\tPossible Values are:\t{value_set}\n'
        display += '\tMaximum length is:\t{max_length}'
        display_str = display.format(attr_dict)
        self.assertEqual(self.test_param.disp(), display_str)


if __name__ == '__main__':
    unittest.main()
