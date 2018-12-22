'''	Make subclass of CustomVariableSet with one required and one optional string
    CustomVariable.
    i. initialize CustomVariableSet with no passed values
        - verify that default value is returned for the required CustomVariable
            (get_values)
        - verify that initialized is False for the required CustomVariable
        - Verify that the optional CustomVariable is not in the CustomVariable set
    ii. initialize CustomVariableSet with value for the optional CustomVariable
        - verify that default value is returned for the required CustomVariable
        - verify that the value is returned for the optional CustomVariable
        - verify that initialized is True for the optional CustomVariable
    iii. initialize CustomVariableSet with value for the required CustomVariable
        - verify that the value is returned for the required CustomVariable
        - Verify that the optional CustomVariable is not in the CustomVariable set
    iv. initialize CustomVariableSet with values for both variable_
        - verify that the values are returned for both variables
    v. initialize CustomVariableSet with an invalid value for the optional
        CustomVariable
        - verify that NotValidError is raised
        - verify that Error message includes CustomVariable name and CustomVariable set
            name.
    vi. initialize CustomVariable set with value for CustomVariable and non-CustomVariable
            arguments
        - verify that value is returned
        - verify that the CustomVariableSet instance includes dictionary entries for
            the non-CustomVariable arguments.
'''
import unittest
from custom_variable_sets import CustomVariable, CustomVariableSet

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

# FIXME Use StringV and IntegerV here
@unittest.skip('Not Implemented')
class TwoStringV(CustomVariableSet):
    '''A CustomVariable set with two string variables:
            "test_string1"
            "test_string2"
    '''
    test_string2 = TestVariable(name='test_string2',
                                 value='test_string2',
                                 default='string2 default')
    parameter_definitions = [
        {'name': 'test_string1',
         'variable_type': TestVariable,
         'required': False,
         'on_update': None},
        {'CustomVariable': test_string2,
         'required': True}
        ]


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
        self.test_variable_set = TwoStringV()

    def test_for_default(self):
        '''verify that default value is returned (get_values)
        '''
        self.assertEqual(
            self.test_variable_set['test_string1'].value,
            'string1 default')

    def test_get_values_for_default(self):
        '''verify that default value is returned (get_values)
        '''
        self.assertEqual(
            self.test_variable_set.get_values('test_string1'),
            'string1 default'
            )


    def test_check_not_initialized(self):
        '''verify that initialized is False
        '''
        self.assertFalse(self.test_variable_set['test_string1'].is_initialized())

    def test_empty_dict(self):
        '''Verify that to_dict returns an empty dictionary
        '''
        dict_set = self.test_variable_set.to_dict()
        self.assertDictEqual(dict_set, {})

    def test_set_value(self):
        '''Verify that set_values can be used to set the CustomVariable value
        '''
        test_value = 'new_value'
        self.test_variable_set.set_values(test_value)
        self.assertEqual(
            self.test_variable_set.get_values('test_string1'),
            test_value)

    def test_initialized(self):
        '''Verify that after using set_values initialized is True.
        '''
        test_value = {'test_string1': 'new_value'}
        self.assertFalse(self.test_variable_set['test_string1'].is_initialized())
        self.test_variable_set.set_values(**test_value)
        self.assertTrue(self.test_variable_set['test_string1'].is_initialized())


if __name__ == '__main__':
    unittest.main()
