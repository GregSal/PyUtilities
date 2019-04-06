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
from custom_variable_sets import StringV, IntegerV, CustomVariableSet
from custom_variable_sets import NotValidError, UpdateError, UnMatchedValuesError


class OneStringV(CustomVariableSet):
    '''A CustomVariable set with one string CustomVariable:
            "test_string1"
    '''
    variable_definitions = [
        {'name': 'test_string1',
         'variable_type': StringV,
         'default': 'string1 default',
         'required': False,
         'on_update': None}
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
        self.test_variable_set = OneStringV()

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
            'string1 default')

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
        self.assertFalse(self.test_variable_set['test_string1'].initialized)
        self.test_variable_set.set_values(**test_value)
        self.assertTrue(self.test_variable_set['test_string1'].initialized)

    def test_invalid_value(self):
        '''Verify that trying to set an invalid value raises a
        NotValidError error.
        '''
        with self.assertRaises(NotValidError):
            self.test_variable_set.set_values(list())

    @unittest.skip('Not Implemented')
    def test_invalid_default_message(self):
        '''Verify that trying to set an invalid default value returns an
        error message that includes CustomVariable name and CustomVariable set name.
        '''
        self.fail('Not yet functional')
        error_message = '1 is an invalid value for StringV.'
        try:
            self.test_variable_set['test_string1'].set_default(1)
        except NotValidError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('NotValidError not raised')

    def test_set_default(self):
        '''Verify that CustomVariable attributes can be set
        '''
        new_default = 'new default value'
        attribute_def = {'test_string1': dict(default=new_default)}
        self.test_variable_set.update_variables(attribute_def)


class TestWithInitialValues(unittest.TestCase):
    '''Initialize CustomVariable set with value for CustomVariable
            - verify that value is returned
            - verify that initialized is True
            - Verify that to_dict returns an the CustomVariable value in a
                dictionary
            - Verify that set_values can be used to change the CustomVariable value
        After drop is used:
            - verify that initialized is False
    '''
    def setUp(self):
        '''Initialize CustomVariable set with no passed values
        '''
        self.test_variable_set = OneStringV(**{
            'test_string1': dict(value='initial_test_string',
                                 default='initial default')})

    def test_for_value(self):
        '''verify that value is returned
        '''
        self.assertEqual(self.test_variable_set['test_string1'].value,
                         'initial_test_string')

    def test_get_values(self):
        '''verify that value is returned (get_values)
        '''
        self.assertEqual(self.test_variable_set.get_values('test_string1'),
                         'initial_test_string')

    def test_check_is_initialized(self):
        '''verify that initialized is True
        '''
        self.assertTrue(self.test_variable_set['test_string1'].is_initialized())

    def test_dict_value(self):
        '''Verify that to_dict returns an the CustomVariable value in a dictionary.
        '''
        dict_set = self.test_variable_set.to_dict()
        self.assertDictEqual(dict_set, {'test_string1': 'initial_test_string'})

    def test_set_value(self):
        '''Verify that set_values can be used to set the CustomVariable value
        '''
        test_value = 'new_value'
        self.test_variable_set.set_values(test_value)
        self.assertEqual(
            self.test_variable_set.get_values('test_string1'),
            test_value)

    def test_drop_initialized(self):
        '''verify that initialized is False after drop()
        '''
        self.test_variable_set.drop('test_string1')
        self.assertFalse(self.test_variable_set['test_string1'].is_initialized())

    def test_drop_give_default(self):
        '''verify that after drop() value returns default
        '''
        self.test_variable_set.drop('test_string1')
        self.assertEqual(self.test_variable_set['test_string1'].value,
                         'initial default')


class TestWithAdditionalValues(unittest.TestCase):
    '''Initialize CustomVariable set with value for CustomVariable and non-CustomVariable
        arguments
        - verify that value is returned
        - verify that the CustomVariableSet instance includes dictionary entries
            for the non-CustomVariable arguments.
    '''
    def setUp(self):
        '''Initialize CustomVariable set with non CustomVariable values
        '''
        self.initial_value = 'base test string;'
        test_string1_initial = dict(value=self.initial_value,
                                                     default='string2 default')
        extra_items = dict(extra_item1='item1',
                                         extra_item2=2)
        self.variable_set_initial = {'test_string1': test_string1_initial}
        self.variable_set_initial.update(extra_items)
        self.test_variable_set = OneStringV(**self.variable_set_initial)

    def test_for_value(self):
        '''verify that value is returned
        '''
        self.assertEqual(self.test_variable_set['test_string1'].value,
                         self.initial_value)

    def test_dict_value(self):
        '''Verify that to_dict returns an the CustomVariable value and extra items
        in a dictionary.
        '''
        self.variable_set_initial['test_string1'] = self.initial_value
        dict_set = self.test_variable_set.to_dict()
        self.assertDictEqual(dict_set, self.variable_set_initial)


class TestWithinvalidValues(unittest.TestCase):
    '''Initialize CustomVariable set with value for CustomVariable and non-CustomVariable
    arguments
        - verify that value is returned
        - verify that the CustomVariableSet instance includes dictionary entries
            for the non-CustomVariable arguments.
    '''
    def test_for_value_error(self):
        '''verify that an error is returned
        '''
        test_string1_initial = {'test_string1': dict(value=1)}
        with self.assertRaises(NotValidError):
            OneStringV(**test_string1_initial)


if __name__ == '__main__':
    unittest.main()
