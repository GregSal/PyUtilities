'''	Make subclass of Parameters that accepts a string
    Single Parameter Tests
        Make subclass of ParameterSet with one required string parameter
            i. initialize parameter set with no passed values
                d. Verify that set_values can be used to set the parameter
                    value
                e. Verify that after using  set_values  initialized is True
            ii. initialize parameter set with value for parameter
                - verify that value is returned
                - verify that initialized is True
                a. Verify that to_dict returns an the parameter value in a
                    dictionary
                b. Verify that set_values can be used to change the parameter
                    value
                c. After drop is used:
                    a. verify that initialized is False
                    b. Verify that to_dict returns an empty dictionary
            iii. initialize parameter set with invalid value for parameter
                - verify that NotValidError is raised
                - verify that Error message includes Parameter name and
                    parameter set name.
            iv. initialize parameter set with value for parameter and
                    non-parameter arguments
                - verify that value is returned
                - verify that the ParameterSet instance includes dictionary
                    entries for the non-parameter arguments.
'''
import unittest
from parameters import Parameter, ParameterSet, NotValidError


class StringP(Parameter):
    '''A Test String Parameter
    '''
    _name = 'test_string'
    _type = str

    def __init__(self, **kwds):
        '''Create a new instance of the string parameter.'''
        super().__init__(**kwds)

    def isvalid(self, value):
        '''Check that value is a string.
        '''
        return super().isvalid(value)


class OneStringP(ParameterSet):
    '''A Parameter set with one string Parameter:
            "test_string1"
    '''
    parameter_definitions = [
        {'name': 'test_string1',
         'parameter_type': StringP,
         'default': 'string1 default',
         'required': False,
         'on_update': None}
        ]

    def __init__(self, **kwds):
        '''Create a new instance of the Parameter Set.'''
        super().__init__(**kwds)


class TestNoInitialValues(unittest.TestCase):
    '''Make subclass of ParameterSet with one required string parameter
        Initialize parameter set with no passed values
            1. verify that default value is returned (get_values)
            2. verify that initialized is False
            3. Verify that to_dict returns an empty dictionary
            4. Verify that set_values can be used to set the parameter value
            5. Verify that after using set_values initialized is True
    '''

    def setUp(self):
        '''Initialize parameter set with no passed values
        '''
        self.test_param_set = OneStringP()

    def test_for_default(self):
        '''verify that default value is returned (get_values)
        '''
        self.assertEqual(
            self.test_param_set['test_string1'].value,
            'string1 default')

    def test_get_values_for_default(self):
        '''verify that default value is returned (get_values)
        '''
        self.assertEqual(
            self.test_param_set.get_values('test_string1'),
            'string1 default')

    def test_check_not_initialized(self):
        '''verify that initialized is False
        '''
        self.assertFalse(self.test_param_set['test_string1'].is_initialized())

    def test_empty_dict(self):
        '''Verify that to_dict returns an empty dictionary
        '''
        dict_set = self.test_param_set.to_dict()
        self.assertDictEqual(dict_set, {})

    def test_set_value(self):
        '''Verify that set_values can be used to set the parameter value
        '''
        test_value = 'new_value'
        self.test_param_set.set_values(test_value)
        self.assertEqual(
            self.test_param_set.get_values('test_string1'),
            test_value)

    def test_initialized(self):
        '''Verify that after using set_values initialized is True.
        '''
        test_value = {'test_string1': 'new_value'}
        self.assertFalse(self.test_param_set['test_string1'].is_initialized())
        self.test_param_set.set_values(test_value)
        self.assertTrue(self.test_param_set['test_string1'].is_initialized())

    def test_invalid_value(self):
        '''Verify that trying to set an invalid value raises a
        NotValidError error.
        '''
        self.fail('Not yet functional')
        with self.assertRaises(NotValidError):
            self.test_param_set.set_values(list())

    def test_default_NotValid_message(self):
        '''Verify that trying to set an invalid default value returns an
        error message that includes Parameter name and parameter set name.
        '''
        self.fail('Not yet functional')
        error_message = '1 is an invalid value for StringP.'
        try:
            self.test_param.set_default(1)
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_set_default(self):
        '''Verify that parameter attributes can be set
        '''
        new_default = 'new default value'
        attribute_def = {'test_string1': dict(default=new_default)}
        self.test_param_set.initialize_parameters(attribute_def)

    def test_invalid_default(self):
        '''Verify that trying to set an invalid value raises a
        NotValidError error.
        '''
        self.fail('Not yet functional')
        # with self.assertRaises(NotValidError):


class TestWithInitialValues(unittest.TestCase):
    '''Initialize parameter set with value for parameter
            - verify that value is returned
            - verify that initialized is True
            - Verify that to_dict returns an the parameter value in a
                dictionary
            - Verify that set_values can be used to change the parameter value
        After drop is used:
            - verify that initialized is False
    '''

    def setUp(self):
        '''Initialize parameter set with no passed values
        '''
        self.test_param_set = OneStringP(
                {'test_string1': dict(value='initial_test_string',
                                      default='initial default')
                })

    def test_for_value(self):
        '''verify that value is returned
        '''
        self.assertEqual(self.test_param_set['test_string1'].value,
                         'initial_test_string')

    def test_get_values(self):
        '''verify that value is returned (get_values)
        '''
        self.assertEqual(self.test_param_set.get_values('test_string1'),
                         'initial_test_string')

    def test_check_is_initialized(self):
        '''verify that initialized is True
        '''
        self.assertTrue(self.test_param_set['test_string1'].is_initialized())

    def test_dict_value(self):
        '''Verify that to_dict returns an the parameter value in a dictionary.
        '''
        dict_set = self.test_param_set.to_dict()
        self.assertDictEqual(dict_set, {'test_string1': 'initial_test_string'})

    def test_set_value(self):
        '''Verify that set_values can be used to set the parameter value
        '''
        test_value = 'new_value'
        self.test_param_set.set_values(test_value)
        self.assertEqual(
            self.test_param_set.get_values('test_string1'),
            test_value)

    def test_initialized(self):
        '''Verify that set_values can be used to change the parameter value.
        '''
        test_value = {'test_string1': 'new_value'}
        self.assertFalse(self.test_param_set['test_string1'].is_initialized())
        self.test_param_set.set_values(test_value)
        self.assertTrue(self.test_param_set['test_string1'].is_initialized())

    def test_drop_initialized(self):
        '''verify that initialized is False after drop()
        '''
        self.test_param_set.drop('test_string1')
        self.assertTrue(self.test_param_set['test_string1'].is_initialized())

    def test_drop_give_default(self):
        '''verify that after drop() value returns default
        '''
        self.test_param_set.drop('test_string1')
        self.assertEqual(self.test_param_set['test_string1'].value,
                         'initial default')


class TestWithAdditionalValues(unittest.TestCase):
    '''Initialize parameter set with value for parameter and non-parameter
    arguments
        - verify that value is returned
        - verify that the ParameterSet instance includes dictionary entries
            for the non-parameter arguments.
    '''

    def setUp(self):
        '''Initialize parameter set with no passed values
        '''
        self.test_param_set = OneStringP(value='base test string;',
                                         default='string2 default',
                                         extra_item1='item1',
                                         extra_item2=2)

    def test_for_value(self):
        '''verify that value is returned
        '''
        self.assertEqual(self.test_param_set['test_string1'].value,
                         'base test string;')

    def test_dict_value(self):
        '''Verify that to_dict returns an the parameter value and extra items
        in a dictionary.
        '''
        dict_set = self.test_param_set.to_dict()
        self.assertDictEqual(dict_set, {
                'test_string1': 'initial_test_string',
                'extra_item1': 'item1',
                'extra_item2': 2})


class TestWithinvalidValues(unittest.TestCase):
    '''Initialize parameter set with value for parameter and non-parameter
    arguments
        - verify that value is returned
        - verify that the ParameterSet instance includes dictionary entries
            for the non-parameter arguments.
    '''

    def setUp(self):
        '''Initialize parameter set with no passed values
        '''
        self.test_param_set = OneStringP(value=1)

    def test_for_value(self):
        '''verify that value is returned
        '''
        self.assertEqual(self.test_param_set['test_string1'].value,
                         'base test string;')


if __name__ == '__main__':
    unittest.main()
