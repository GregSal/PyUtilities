'''Basic Parameter class object tests.
'''
import unittest
from parameters import Parameter, get_class_name
from parameters import NotValidError

class TestBaseParameterNoValue(unittest.TestCase):
    '''Test instance creation passing nothing.
    '''
    def setUp(self):
        '''Create an instance of StringP with no initialization.
        name='Test String'
        '''
        self.test_param = TestParameter()

    def test_name(self):
        '''Verify the name is the Parameter class name.
        '''
        self.assertEqual(self.test_param.name, 'TestParameter')

    def test_initialization(self):
        '''Verify that the parameter is not initialized'''
        self.assertFalse(self.test_param.is_initialized())

    def test_none_default(self):
        '''Verify that value returns the default of None
        '''
        self.assertIsNone(self.test_param.value)

    def test_default(self):
        '''Verify that the default value can be changed.
        '''
        self.test_param.set_default('default')
        self.assertEqual(self.test_param.value, 'default')

    def test_blank_default(self):
        '''Verify that the default value can be an empty string.
        '''
        self.test_param.set_default('')
        self.assertEqual(self.test_param.value, '')

    def test_invalid_default(self):
        '''Verify that trying to set an invalid default value raises a
        NotValidError error.
        '''
        with self.assertRaises(NotValidError):
            self.test_param.set_default(1)

    def test_invalid_default_message(self):
        '''Verify that trying to set an invalid default value returns the
        appropriate error message.
        '''
        error_message = '1 is an invalid value for TestParameter.'
        try:
            self.test_param.set_default(1)
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_initialize_value(self):
        '''Verify that when the value is set, is_initialized becomes True.
        '''
        self.test_param.value = 'value'
        self.assertTrue(self.test_param.is_initialized())

    def test_set_value(self):
        '''Verify that the value can be set and returned.
        '''
        self.test_param.value = 'value'
        self.assertEqual(self.test_param.value, 'value')

    def test_reset_value(self):
        '''Verify that after applying the reset method, value returns default
        value.'''
        self.test_param.value = 'value'
        self.test_param.set_default('default')
        self.test_param.reset_value()
        self.assertEqual(self.test_param.value, 'default')

    def test_equality(self):
        '''Verify that equality compares the parameter value.
        '''
        test_value = 'value'
        self.test_param.value = test_value
        self.assertTrue(self.test_param == test_value)

    def test_invalid_value(self):
        '''Verify that seeting an invalid value raises an error.'''
        with self.assertRaises(NotValidError):
            self.test_param.value = 1

    def test_update_settings(self):
        '''Verify that attributes can be set.
        '''
        test_type = str(type(self))
        setting = dict(cls=test_type)
        self.test_param.set_attributes(**setting)
        self.assertEqual(self.test_param.cls, test_type)

    def test_message_mod(self):
        '''Verify that messages can be modified.
        '''
        default_value = 'default'
        test_value = 'value'
        test_name = self.test_param.name
        setting = dict(default=default_value)
        self.test_param.set_attributes(**setting)
        self.test_param.value = test_value
        test_msg = dict(not_valid='{new_value} is invalid for {name}')
        self.test_param.update_messages(test_msg)
        error_message = '1 is invalid for ' + test_name
        try:
            self.test_param.set_default(1)
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_str(self):
        '''Verify that str returns a string version of the value.'''
        test_value = 'value'
        self.test_param.value = test_value
        self.assertEqual(str(self.test_param), test_value)

    @unittest.skip('Not Implemented')
    def test_repr(self):
        '''Verify that __repr__ returns a string representative of the current
        state.
        '''
        self.fail('Not implemented')


class TestBaseParameterValue(unittest.TestCase):
    '''Test instance creation passing name, default and value.
    '''
    def setUp(self):
        '''Create an instance of StringP with initialized values.
        '''
        self.str_value = 'test_param_value'
        self.test_param = TestParameter(
            name='Test_String_Value',
            value=self.str_value,
            default='default_value')

    def test_name(self):
        '''Verify the name.
        '''
        self.assertEqual(self.test_param.name, 'Test_String_Value')

    def test_initialization(self):
        '''Verify that the parameter is initialized'''
        self.assertTrue(self.test_param.is_initialized())

    def test_set_value(self):
        '''Verify that the initialized value is returned.
        '''
        self.assertEqual(self.test_param.value, self.str_value)

    def test_reset_value(self):
        '''Verify that after applying the reset method, value returns default
        value.'''
        self.test_param.reset_value()
        self.assertEqual(self.test_param.value, 'default_value')

    def test_update_settings(self):
        '''Verify that the default can be changes a an attribute.
        '''
        setting = dict(default='new default value')
        self.test_param.set_attributes(**setting)
        self.assertEqual(self.test_param.default, 'new default value')

    def test_copy(self):
        '''Verify that copy() returns an exact copy of the instance.
        '''
        self.max_diff = None
        attr_dict = dict(
            _name='Test_String_Value',
            _value=self.str_value,
            initialized=True,
            default='default_value',
            cls='TestParameter',
            _messages=self.test_param._messages)
        copied_param = self.test_param.copy()
        self.assertDictEqual(copied_param.__dict__, attr_dict)

    def test_display(self):
        '''Verify that disp() returns a formatted string summary of the
        current state.
        name='Test_String_Value',
            value=self.str_value,
            default='default_value'
            '''
        display = 'Test_String_Value parameter of class TestParameter,\n'
        display += '\tCurrent value is:\ttest_param_value\n'
        display += '\tDefault value is:\tdefault_value'
        self.assertEqual(self.test_param.disp(), display)


if __name__ == '__main__':
    unittest.main()
