from custom_variable_sets import StringV, IntegerV, CustomVariableSet
import logging_tools

logger = logging_tools.config_logger()

test_int = IntegerV(name='test_integer', value=10)
# test_int = IntegerV(name='test_integer', value=10, default=1)

#print(test_int)
#print(test_int.is_initialized())

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


# test_variable_set = OneStringV()
# Verify that set_values can be used to set the CustomVariable value
# test_value = 'new_value'
# test_variable_set.set_values(test_value)


#test_variable_set = TwoVariableSet()
test_variable_set = TwoVariableSet(test_string1='initial value')
# logging_tools.log_dict(logger, test_variable_set)

#value_dict = dict(test_string1='new_value', test_integer=5)
#logging_tools.log_dict(logger, value_dict, 'Input to get_values')
#test_variable_set.set_values(**value_dict)

#test_dict = dict(test_string1='test_value', test_integer=10, dummy_item='anything')
#output_dict = test_variable_set.get_values(test_dict)
#logging_tools.log_dict(logger, output_dict, 'From get_values as dict')

#value_dict['dummy_item'] = 'anything'

#test_dict = test_variable_set.to_dict()
#logging_tools.log_dict(logger, test_dict)
#for var, val in test_variable_set.items():
#    print(var + '\t' + str(val))
#print(test_variable_set['test_int'].value)


