'''	Make subclass of CustomVariable that accepts a string
    Single CustomVariable Tests
        Make subclass of CustomVariableSet with one required string CustomVariable
            i. initialize CustomVariable set with no passed values
                d. Verify that set_values can be used to set the CustomVariable
                    value
                e. Verify that after using  set_values  initialized is True
            ii. initialize CustomVariable set with value for CustomVariable
                - verify that value is returned
                - verify that initialized is True
                a. Verify that to_dict returns an the CustomVariable value in a
                    dictionary
                b. Verify that set_values can be used to change the CustomVariable
                    value
                c. After drop is used:
                    a. verify that initialized is False
                    b. Verify that to_dict returns an empty dictionary
            iii. initialize CustomVariable set with invalid value for CustomVariable
                - verify that NotValidError is raised
                - verify that Error message includes CustomVariable name and
                    CustomVariable set name.
            iv. initialize CustomVariable set with value for CustomVariable and
                    non-CustomVariable arguments
                - verify that value is returned
                - verify that the CustomVariableSet instance includes dictionary
                    entries for the non-CustomVariable arguments.
'''
import unittest
from custom_variable_sets import CustomVariableSet, StringV


@unittest.skip('Not Implemented')
class TwoStringV(CustomVariableSet):
    '''A CustomVariable set with two string Variables:
            "test_string1"
            "test_string2"
    '''
    test_string2 = StringV(name='test_string2',
                           value='test_string2',
                           default='string2 default')
    variable_definitions = [
        {'name': 'test_string1',
         'variable_type': StringV,
         'required': False,
         'on_update': None},
        {'CustomVariable': test_string2,
         'required': True}
        ]

    def __init__(self, **kwds):
        '''Create a new instance of the CustomVariable Set.'''
        super().__init__(**kwds)


@unittest.skip('Not implemented')
class TestNoInitialValues(unittest.TestCase):
    '''Make subclass of CustomVariableSet with one required string CustomVariable
        Initialize CustomVariable set with no passed values
            1. verify that default value is returned (get_values)
            2. verify that initialized is False
            3. Verify that to_dict returns an empty dictionary
            4. Verify that set_values can be used to set the CustomVariable value
            5. Verify that after using set_values initialized is True
    '''

    def setUp(self):
        '''Initialize CustomVariable set with no passed values
        '''
        pass



if __name__ == '__main__':
    unittest.main()
