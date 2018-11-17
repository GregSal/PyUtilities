import unittest
from parameters import Parameter
from parameters import NotValidError

class StringP(Parameter):
    '''A Test String Parameter
    '''
    _type = str

    def __init__(self, **kwds):
        '''Create a new instance of the string parameter.'''
        super().__init__(**kwds)

    def isvalid(self, value):
        '''Check that value is a string.
        '''
        return super().isvalid(value)


class TestSingleParameter(unittest.TestCase):
    def setUp(self):
        print('done setup')
        self.test_param = StringP(name='Test String')

    def test_initialization(self):
        print('start test')
        self.assertFalse(self.test_param.is_initialized())

    def test_none_default(self):
        self.assertIsNone(self.test_param.value)

    def test_default(self):
        self.test_param.set_default('default')
        self.assertEqual(self.test_param.value, 'default')

    def test_blank_default(self):
        self.test_param.set_default('')
        self.assertEqual(self.test_param.value, '')

    def test_invalid_default(self):
        with self.assertRaises(NotValidError):
            self.test_param.set_default(1)

    def test_default_NotValid_message(self):
        error_message = '1 is an invalid value for Test String.'
        try:
            self.test_param.set_default(1)
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_initialize_value(self):
        self.test_param.value = 'value'
        self.assertTrue(self.test_param.is_initialized())

    def test_set_value(self):
        self.test_param.value = 'value'
        self.assertEqual(self.test_param.value, 'value')

    def test_reset_value(self):
        self.test_param.value = 'value'
        self.test_param.set_default('default')
        self.test_param.reset_value()
        self.assertEqual(self.test_param.value, 'default')

    def test_equality(self):
        test_value = 'value'
        self.test_param.value = test_value
        self.assertTrue(self.test_param == test_value)

    def test_invalid_value(self):
        with self.assertRaises(NotValidError):
            self.test_param.value = 1

    def test_update_settings(self):
        test_type = str(type(self))
        setting = dict(type=test_type)
        self.test_param.set_attributes(setting)
        self.assertEqual(self.test_param.type, test_type)

    def test_NotValid_message(self):
        default_value = 'default'
        test_value = 'value'
        test_type = str(type(self))
        self.test_param.type = test_type
        self.test_param.set_default(default_value)
        self.test_param.value = test_value
        test_msg = dict(not_valid='{new_value} is invalid for {type}')
        self.test_param.update_messages(test_msg)
        error_message = '1 is invalid for ' + test_type
        try:
            self.test_param.set_default(1)
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_str(self):
        test_value = 'value'
        self.test_param.value = test_value
        self.assertEqual(str(self.test_param), test_value)

    @unittest.skip('Not Implemented')
    def test_repr(self):
        self.fail('Not implemented')

    @unittest.skip('Not Implemented')
    def test_copy(self):
        self.fail('Not implemented')
if __name__ == '__main__':
    unittest.main()
