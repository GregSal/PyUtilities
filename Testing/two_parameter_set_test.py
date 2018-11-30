'''	Make subclass of ParameterSet with one required and one optional string
    parameter.
    i. initialize parameter set with no passed values
        - verify that default value is returned for the required parameter
            (get_values)
        - verify that initialized is False for the required parameter
        - Verify that the optional parameter is not in the parameter set
    ii. initialize parameter set with value for the optional parameter
        - verify that default value is returned for the required parameter
        - verify that the value is returned for the optional parameter
        - verify that initialized is True for the optional parameter
    iii. initialize parameter set with value for the required parameter
        - verify that the value is returned for the required parameter
        - Verify that the optional parameter is not in the parameter set
    iv. initialize parameter set with values for both parameters
        - verify that the values are returned for both parameters
    v. initialize parameter set with an invalid value for the optional
        parameter
        - verify that NotValidError is raised
        - verify that Error message includes Parameter name and parameter set
            name.
    vi. initialize parameter set with value for parameter and non-parameter
            arguments
        - verify that value is returned
        - verify that the ParameterSet instance includes dictionary entries for
            the non-parameter arguments.
'''
import unittest
from parameters import Parameter, ParameterSet

@unittest.skip('Not Implemented')
class TestParameter(Parameter):
    '''A Test String Parameter
    '''
    _name = 'test_string'
    _type = str

    def __init__(self, **kwds):
        '''Create a new instance of the string parameter.'''
        super().__init__(**kwds)

    def check_validity(self, value):
        '''Check that value is a string.
        '''
        error_message = super().check_validity(value)
        if error_message is None:
            if len(value) <= 0:
                error_message = 'not_valid'
        return error_message


class TwoStringP(ParameterSet):
    '''A Parameter set with two string Parameters:
            "test_string1"
            "test_string2"
    '''
    test_string2 = TestParameter(name='test_string2',
                                 value='test_string2',
                                 default='string2 default')
    parameter_definitions = [
        {'name': 'test_string1',
         'parameter_type': TestParameter,
         'required': False,
         'on_update': None},
        {'parameter': test_string2,
         'required': True}
        ]


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
        self.test_param_set = TestParameter()

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


if __name__ == '__main__':
    unittest.main()
