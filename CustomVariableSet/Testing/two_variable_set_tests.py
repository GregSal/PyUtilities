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
from custom_variable_sets import StringV, IntegerV, CustomVariableSet
from custom_variable_sets import NotValidError, UpdateError, UnMatchedValuesError

test_int = IntegerV(name='test_integer', value=10, default=1)

class TwoVariableSet(CustomVariableSet):
    '''A CustomVariable set with two variables:
            "test_string1"
            "test_integer"
    '''
    variable_definitions = [
        {'name': 'test_string1',
         'variable_type': StringV,
         'default': 'default_value',
         'required': False},
         {'CustomVariable': test_int,  'required': True}
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
        '''Initialize CustomVariable set with no passed values'''
        self.test_variable_set = TwoVariableSet()

    def tearDown(self):
        '''Remove the CustomVariable set.'''
        del self.test_variable_set
        self.test_variable_set = None

    def test_for_value(self):
        '''verify that default value is returned (get_values)
        '''
        self.assertEqual(self.test_variable_set['test_integer'].value, 10)

    def test_for_default(self):
        '''verify that initial value is returned (get_values)
        '''
        self.assertEqual(
            self.test_variable_set['test_string1'].value,
            'default_value')

    def test_get_values_for_default(self):
        '''verify that default value is returned (get_values)
        '''
        self.assertEqual(
            self.test_variable_set.get_values('test_string1'),
            'default_value'
            )

    def test_check_not_initialized(self):
        '''verify that initialized is False
        '''
        self.assertFalse(self.test_variable_set['test_string1'].is_initialized())

    def test_to_dict(self):
        '''Verify that to_dict returns an empty dictionary
        '''
        dict_set = self.test_variable_set.to_dict()
        self.assertDictEqual(dict_set, {'test_integer': 10})

    def test_to_list(self):
        '''Verify that to_dict returns an empty dictionary
        '''
        value_list = self.test_variable_set.get_values(['test_string1', 'test_integer'])
        self.assertListEqual(value_list, ['default_value', 10])

    def test_set_value(self):
        '''Verify that set_values can be used to set the CustomVariable value
        '''
        test_value = 'new_value'
        self.test_variable_set.set_values(test_string1=test_value)
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


    def test_set_value_to_dict(self):
        '''Verify that set_values can be used to set the CustomVariable value
        and return a dictionary of values.
        '''
        test_dict = dict(test_string1='test_value', test_integer=10)
        self.test_variable_set.set_values(**test_dict)
        self.assertDictEqual(self.test_variable_set.to_dict(), test_dict)


    def test_get_value_as_dict(self):
        '''Verify that set_values can be used to set the CustomVariable value
        and return a dictionary of values.
        '''
        test_dict = dict(test_string1='test_value', test_integer=10, dummy_item='anything')
        value_dict = dict(test_string1='new_value', test_integer=5)
        self.test_variable_set.set_values(**value_dict)
        value_dict['dummy_item'] = 'anything'
        self.assertDictEqual(self.test_variable_set.get_values(test_dict), value_dict)

class TestWithInitialValues(unittest.TestCase):
    '''Make subclass of CustomVariableSet with one required string CustomVariable
    ii. initialize CustomVariableSet with value for the optional CustomVariable
        - verify that default value is returned for the required CustomVariable
        - verify that the value is returned for the optional CustomVariable
        - verify that initialized is True for the optional CustomVariable
    iv. initialize CustomVariableSet with values for both variables
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

    def test_for_initialized_optional(self):
        '''verify that initial value is returned (get_values)'''
        test_variable_set = TwoVariableSet(test_string1='initial value')
        self.assertEqual(test_variable_set.get_values('test_string1'),
                                      'initial value')

    def test_check_is_initialized(self):
        '''verify that initialized is True'''
        test_variable_set = TwoVariableSet(test_string1='initial value')
        self.assertTrue(test_variable_set['test_string1'].is_initialized())

    def test_initial_to_dict(self):
        '''Verify that to_dict returns a dictionary with the two values.'''
        test_variable_set = TwoVariableSet(test_string1='initial value')
        dict_set = test_variable_set.to_dict()
        self.assertDictEqual(dict_set, {'test_string1': 'initial value', 'test_integer': 10})

    def test_both_initial_to_dict(self):
        '''Verify that to_dict returns a dictionary with the two values.'''
        test_variable_set = TwoVariableSet(test_string1='initial value', test_integer=-5)
        dict_set = test_variable_set.to_dict()
        self.assertDictEqual(dict_set, {'test_string1': 'initial value', 'test_integer': -5})


if __name__ == '__main__':
    unittest.main()
