'''Define a set of unit tests for the Parameters module'''

from ParametersList import *

class test_parameter_list(unittest.TestCase):
    #Define the set of parameters
    class TestParameterSet(ParameterList):
        '''A set of parameters for testing'''
        list_of_parameters = set()

        #define the test parameter class
        class TestOptions(OptionList):
            name = 'Test Options1'
            description = 'This it a test class for options selection'
            selection_list = ('Test choice A', 'Test choice B', 'Test choice C')

        class TestChoice(BinaryOption):
            name = 'Test Choice'
            description = 'This it a test class for True/False selection'

        class TestInt(IntegerOption):
            name = 'Test Integer Option from 1 to 10'
            description = 'This it a test integer parameter with range from 1 to 10'
            default_value = 8
            valid_range = range(1,11)

        list_of_parameters.update({TestOptions, TestChoice, TestInt})

    def test_create_empty_parameter_list(self):
        option_set = self.TestParameterSet()
        self.assertEqual(option_set.get_parameter(option_set.TestOptions), 'Test choice A')
        option_set.set_parameter(option_set.TestOptions, 'Test choice B')
        self.assertEqual(option_set.get_parameter(option_set.TestOptions), 'Test choice B')
        self.assertTrue(option_set.check_parameter(option_set.TestOptions, 'Test choice B'))
        self.assertFalse(option_set.check_parameter(option_set.TestOptions, 'Test choice A'))
        with self.assertRaises(ValueError):
            option_set.set_parameter(option_set.TestOptions, 'a')

    def test_parameter_access(self):
        option_set = self.TestParameterSet(self.TestParameterSet().TestOptions, 'Test choice B')
        self.assertEqual(option_set.get_parameter(option_set.TestOptions), 'Test choice B')
        with self.assertRaises(ValueError):
            option_set.set_parameter(option_set.TestOptions, 'Test choice D')
        new_selection_list = list(option_set.TestOptions().selection_list)
        new_selection_list.append('Test choice D')
        new_selections = tuple(new_selection_list)
        option_set.TestOptions.set_selections(option_set.TestOptions, option_set, new_selections)
        self.assertTupleEqual(option_set.TestOptions().selection_list, new_selections)
        option_set.set_parameter(option_set.TestOptions, 'Test choice D')
        self.assertEqual(option_set.get_parameter(option_set.TestOptions), 'Test choice D')

    def test_Choice_parameter(self):
        option_set = self.TestParameterSet()
        self.assertTrue(option_set.check_parameter(option_set.TestChoice, False))
        option_set = self.TestParameterSet(option_set.TestChoice, True)
        self.assertEqual(option_set.get_parameter(option_set.TestChoice), True)
        with self.assertRaises(ValueError):
            option_set.set_parameter(option_set.TestChoice, 'a')
        option_set.TestChoice.set_default(option_set.TestChoice, option_set, True)
        option_set = self.TestParameterSet()
        self.assertTrue(option_set.check_parameter(option_set.TestChoice, True))

    def test_int_parameter(self):
        option_set = self.TestParameterSet(self.TestParameterSet().TestInt, 5)
        self.assertTrue(option_set.check_parameter(option_set.TestInt, 5))
        option_set.TestInt.set_range(option_set.TestInt, option_set, -10, 10, 2)
        self.assertFalse(option_set.check_parameter(option_set.TestInt, 5))
        self.assertTrue(option_set.check_parameter(option_set.TestInt, 8))
        with self.assertRaises(ValueError):
            option_set.set_parameter(option_set.TestInt, 5)
        option_set.TestInt.set_range(option_set.TestInt, option_set, 1, 6)
        option_set.reset_parameter(option_set.TestInt)
        self.assertTrue(option_set.check_parameter(option_set.TestInt, None))


class test_options(unittest.TestCase):
    #define the test parameter class
    class TestOption(OptionList):
        name = 'Test Options1'
        description = 'This it a test class for options selection'
        selection_list = ('Test choice A', 'Test choice B', 'Test choice C')


    #def setUp(self):
    #def tearDown(self):

    def test_empty_options(self):
        dummy_options = dict()
        this_option = self.TestOption()
        self.assertEqual(this_option.get_default(this_option), 'Test choice A')
        self.assertEqual(this_option.get_value(dummy_options), 'Test choice A')
        self.assertTrue(this_option.isvalid('Test choice A', dummy_options))
        self.assertFalse(this_option.isvalid('a', dummy_options))
        self.assertFalse(this_option.isvalid(0, dummy_options))
        self.assertTrue(this_option.isvalue('Test choice A', dummy_options))

    def test_options_set(self):
        dummy_options = dict()
        this_option = self.TestOption()
        this_option.set_value('Test choice B', dummy_options)
        self.assertEqual(this_option.get_value(dummy_options), 'Test choice B')
        self.assertTrue(this_option.isvalue('Test choice B', dummy_options))
        with self.assertRaises(ValueError):
            this_option.set_value('a', dummy_options)

    def test_options_defined(self):
        dummy_options = dict()
        this_option = self.TestOption('Test choice C', dummy_options)
        self.assertEqual(this_option.get_value(dummy_options), 'Test choice C')
        with self.assertRaises(ValueError):
            this_option = self.TestOption('Test choice D', dummy_options)

    def test_options_reset(self):
        dummy_options = dict()
        this_option = self.TestOption()
        this_option.set_value('Test choice C', dummy_options)
        self.assertEqual(this_option.get_value(dummy_options), 'Test choice C')
        self.assertTrue(this_option.isvalue('Test choice C', dummy_options))
        this_option.reset_value()
        self.assertEqual(this_option.get_value(dummy_options), 'Test choice A')
        this_option.set_value('Test choice B', dummy_options)
        self.assertEqual(this_option.get_value(dummy_options), 'Test choice B')
        self.TestOption.set_default(self.TestOption, dummy_options, this_option.get_value(dummy_options))
        self.assertEqual(this_option.get_default(dummy_options), 'Test choice B')
        this_option.set_value('Test choice C', dummy_options)
        self.assertTrue(this_option.isvalue('Test choice C', dummy_options))
        this_option.reset_value()
        self.assertTrue(this_option.isvalue('Test choice B', dummy_options))


    def test_set_new_selections(self):
        dummy_options = dict()
        this_option = self.TestOption()
        with self.assertRaises(ValueError):
            this_option = self.TestOption('Test choice D', dummy_options)
        new_selection_list = list(this_option.selection_list)
        new_selection_list.append('Test choice D')
        new_selections = tuple(new_selection_list)
        self.TestOption.set_selections(self.TestOption, dummy_options, new_selections)
        self.assertTupleEqual(this_option.selection_list, new_selections)
        this_option = self.TestOption('Test choice D', dummy_options)
        self.assertEqual(this_option.get_value(dummy_options), 'Test choice D')
        self.TestOption.set_default(self.TestOption, dummy_options, this_option.get_value(dummy_options))
        self.assertEqual(this_option.get_default(dummy_options), 'Test choice D')

if __name__ == '__main__':
    unittest.main()
