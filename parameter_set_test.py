'''	Make subclass of Parameters that accepts a string
	Single Parameter Tests
		Make subclass of ParameterSet with one required string parameter
			i. initialize parameter set with no passed values
				d. Verify that set_values can be used to set the parameter value
				e. Verify that after using  set_values  initialized is True
			ii. initialize parameter set with value for parameter
				- verify that value is returned
				- verify that initialized is True
				a. Verify that to_dict returns an the parameter value in a dictionary
				b. Verify that set_values can be used to change the parameter value
				c. After drop is used:
					a. verify that initialized is False
					b. Verify that to_dict returns an empty dictionary
			iii. initialize parameter set with invalid value for parameter
				- verify that NotValidError is raised
				- verify that Error message includes Parameter name and parameter set name.
			iv. initialize parameter set with value for parameter and non-parameter arguments
				- verify that value is returned
				- verify that the ParameterSet instance includes dictionary entries for the
                non-parameter arguments.
'''
import unittest
from parameters import Parameter, ParameterSet

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

class TwoStringP(ParameterSet):
    '''A Parameter set with two string Parameters:
            "test_string1"
            "test_string2"
    '''
    test_string2 = StringP(name='test_string2',
                           value='test_string2',
                           default='string2 default')
    parameter_definitions = [
        {'name': 'test_string1',
         'parameter_type': StringP,
         'required': False,
         'on_update': None},
        {'parameter': test_string2,
         'required': True}
        ]

    def __init__(self, **kwds):
        '''Create a new instance of the Parameter Set.'''
        super().__init__(**kwds)


class TestNoInitialValues(unittest.TestCase):
    def setUp(self):
        self.test_param_set = OneStringP()

    def test_for_default(self):
        self.assertEqual(
            self.test_param_set['test_string1'].value,
            'string1 default')

    def test_get_values_for_default(self):
        self.assertEqual(
            self.test_param_set.get_values('test_string1'),
            'string1 default')

    def test_check_not_initialized(self):
        self.assertFalse(self.test_param_set['test_string1'].is_initialized())

    @unittest.skip("Not Implemented")
    def test_empty_dict(self):
        dict_set = self.test_param_set.to_dict()
        self.assertDictEqual(dict_set, {})

    @unittest.skip("Not Implemented")
    def test_set_value(self):
        test_value = 'new_value'
        self.test_param_set.set_values(test_value)
        self.assertEqual(
            self.test_param_set.get_values('test_string1'),
            test_value)


if __name__ == '__main__':
    unittest.main()
