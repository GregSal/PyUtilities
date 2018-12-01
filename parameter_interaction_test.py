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
from parameters import Parameter, ParameterSet, StringP


class TwoStringP(ParameterSet):
    '''A Parameter set with two string Parameters:
            "test_string1"
            "test_string2"
    '''
    # FIXME update StringP creater call
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


@unittest.skip('Not implimented')
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
        pass



if __name__ == '__main__':
    unittest.main()
