'''Basic CustomVariable class object tests.
'''
import unittest
from custom_variable_sets import CustomVariable, get_class_name
from custom_variable_sets import NotValidError
class TestVariable(CustomVariable):
    '''Test custom variable class
    '''
    _name = 'test variable'
    _type = str

    def __init__(self, *args, **kwds):
        '''Create a new instance of the CustomVariable.
        '''
        super().__init__(*args, **kwds)

    def check_validity(self, value)->bool:
        '''Check the value is a string.
        '''
        return super().check_validity(value)

class TestCustomVariableNoValue(unittest.TestCase):
    '''Test instance creation passing nothing.
    '''
    def setUp(self):
        '''Create an instance of TestVariable with no initialization.
        name='Test String'
        '''
        self.test_var = TestVariable()

    def test_name(self):
        '''Verify the name is the CustomVariable class name.
        '''
        self.assertEqual(self.test_var.name, 'TestVariable')

    def test_initialization(self):
        '''Verify that the CustomVariable is not initialized'''
        self.assertFalse(self.test_var.is_initialized())

    def test_none_default(self):
        '''Verify that value returns the default of None
        '''
        self.assertIsNone(self.test_var.value)

    def test_default(self):
        '''Verify that the default value can be changed.
        '''
        self.test_var.set_default('default')
        self.assertEqual(self.test_var.value, 'default')

    def test_blank_default(self):
        '''Verify that the default value can be an empty string.
        '''
        self.test_var.set_default('')
        self.assertEqual(self.test_var.value, '')

    def test_invalid_default(self):
        '''Verify that trying to set an invalid default value raises a
        NotValidError error.
        '''
        with self.assertRaises(NotValidError):
            self.test_var.set_default(1)

    def test_invalid_default_message(self):
        '''Verify that trying to set an invalid default value returns the
        appropriate error message.
        '''
        error_message = '1 is an invalid value for TestVariable.'
        try:
            self.test_var.set_default(1)
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_initialize_value(self):
        '''Verify that when the value is set, is_initialized becomes True.
        '''
        self.test_var.value = 'value'
        self.assertTrue(self.test_var.is_initialized())

    def test_set_value(self):
        '''Verify that the value can be set and returned.
        '''
        self.test_var.value = 'value'
        self.assertEqual(self.test_var.value, 'value')

    def test_reset_value(self):
        '''Verify that after applying the reset method, value returns default
        value.'''
        self.test_var.value = 'value'
        self.test_var.set_default('default')
        self.test_var.reset_value()
        self.assertEqual(self.test_var.value, 'default')

    def test_equality(self):
        '''Verify that equality compares the CustomVariable value.
        '''
        test_value = 'value'
        self.test_var.value = test_value
        self.assertTrue(self.test_var == test_value)

    def test_invalid_value(self):
        '''Verify that setting an invalid value raises an error.'''
        with self.assertRaises(NotValidError):
            self.test_var.value = 1

    def test_update_settings(self):
        '''Verify that attributes can be set.
        '''
        test_type = str(type(self))
        setting = dict(cls=test_type)
        self.test_var.set_attributes(**setting)
        self.assertEqual(self.test_var.cls, test_type)

    def test_message_mod(self):
        '''Verify that messages can be modified.
        '''
        default_value = 'default'
        test_value = 'value'
        test_name = self.test_var.name
        setting = dict(default=default_value)
        self.test_var.set_attributes(**setting)
        self.test_var.value = test_value
        test_msg = dict(not_valid='{new_value} is invalid for {name}')
        self.test_var.update_messages(test_msg)
        error_message = '1 is invalid for ' + test_name
        try:
            self.test_var.set_default(1)
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_str(self):
        '''Verify that str returns a string version of the value.'''
        test_value = 'value'
        self.test_var.value = test_value
        self.assertEqual(str(self.test_var), test_value)

    @unittest.skip('Not Implemented')
    def test_repr(self):
        '''Verify that __repr__ returns a string representative of the current
        state.
        '''
        self.fail('Not implemented')


class TestCustomVariableValue(unittest.TestCase):
    '''Test instance creation passing name, default and value.
    '''
    def setUp(self):
        '''Create an instance of StringV with initialized values.
        '''
        self.str_value = 'test__value'
        self.test_var = TestVariable(
            name='Test_String_Value',
            value=self.str_value,
            default='default_value')

    def test_name(self):
        '''Verify the name.
        '''
        self.assertEqual(self.test_var.name, 'Test_String_Value')

    def test_initialization(self):
        '''Verify that the CustomVariable is initialized'''
        self.assertTrue(self.test_var.is_initialized())

    def test_set_value(self):
        '''Verify that the initialized value is returned.
        '''
        self.assertEqual(self.test_var.value, self.str_value)

    def test_reset_value(self):
        '''Verify that after applying the reset method, value returns default
        value.'''
        self.test_var.reset_value()
        self.assertEqual(self.test_var.value, 'default_value')

    def test_update_settings(self):
        '''Verify that the default can be changes a an attribute.
        '''
        setting = dict(default='new default value')
        self.test_var.set_attributes(**setting)
        self.assertEqual(self.test_var.default, 'new default value')

    @unittest.skip('Test broken')
    def test_copy(self):
        '''Verify that copy() returns an exact copy of the instance.
        '''
        self.max_diff = None
        attr_dict = dict(
            _name='Test_String_Value',
            _value=self.str_value,
            initialized=True,
            default='default_value',
            cls='TestVariable',
            _messages=self.test_var._messages)
        copied_var = self.test_var.copy()
        self.assertDictEqual(copied_var.__dict__, attr_dict)

    @unittest.skip('Test broken')
    def test_display(self):
        '''Verify that disp() returns a formatted string summary of the
        current state.
        name='Test_String_Value',
            value=self.str_value,
            default='default_value'
            '''
        display = 'Test_String_Value CustomVariable of class TestVariable,\n'
        display += '\tCurrent value is:\ttest_param_value\n'
        display += '\tDefault value is:\tdefault_value'
        self.assertEqual(self.test_var.disp(), display)


if __name__ == '__main__':
    unittest.main()
