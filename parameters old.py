'''This module is used for generating custom parameter lists
along with defaults and validity testing'''

from pathlib import Path
from sys import maxsize
import logging
logger = logging.getLogger(__name__)

class ParameterList(dict):
    '''This class is the storage for all of the parameters in a given parameter set.
    The key is an object type which is a subclass of Parameter.
    An instance of this class is the way all individual parameters are accessed
    and instances are used to pass parameters to functions.
    The ParameterList instance is passed to individual parameters in all method calls
    so that valid parameter values can depend on other parameter values.'''

    name = 'ParameterList Template'
    list_of_parameters = set()

    def __init__(self, parameter_name=None, value=None):
        '''Create a new instance of the related parameters'''
        super(ParameterList, self).__init__()
        self.set_parameter(parameter_name, value)

    def isvalid(self, parameter_name):
            '''Tests for valid parameters'''
            if issubclass(parameter_name, Parameter):
                return parameter_name in self.list_of_parameters
            else:
                return False

    def set_parameter(self, parameter_name=None, value=None):
        '''Add a parameter item to the ParameterList'''
        if parameter_name is not None:
            if isinstance(parameter_name, dict):
                if not all(self.isvalid(key) for key in iter(parameter_name)):
                    raise TypeError("Invalid parameter objects")
                else:
                    new_parameter_set = parameter_name
            elif self.isvalid(parameter_name):
                new_parameter_set = {parameter_name:value}
            else:
                raise TypeError('{} is not a valid parameter'.format(parameter_name))
            for (parameter_element, element_value) in new_parameter_set.items():
                parameter = parameter_element(element_value, self)
                self[parameter_element] = parameter.get_value(self)

    def reset_parameter(self, parameter_name):
        '''Reset a parameter item to its default value'''
        if self.isvalid(parameter_name):
            self[parameter_name] = parameter_name().get_default(self)
        else:
            raise TypeError('{} is not a valid parameter'.format(parameter_name))

    def get_parameter(self, parameter_name):
        '''Return the value of the requested parameter.
        If the value is not defined explicitly return the default value.'''
        if self.isvalid(parameter_name):
            test_value = self.get(parameter_name)
            if test_value is not None:
                if parameter_name().isvalid(test_value, self):
                    return test_value
            #Return default value if value isn't set or is not valid
            return parameter_name().get_default(self)
        else:
            raise ValueError('{} is not a valid parameter'.format(str(parameter_name)))
        value = self.get(parameter_name)
        if value is not None:
            return value
        else:
            if self.isvalid(parameter_name):
                return parameter_name().get_default(self)
            else:
                raise ValueError('{} is not a valid parameter'.format(str(parameter_name)))

    def check_parameter(self, parameter_name, value):
        '''Test whether the current_value of Parameter_name matches value.
        If there is no current_value defined test value against the default_value.'''
        #Get parameter and test if it matches value
        test_value = self.get_parameter(parameter_name)
        return test_value == value

    #TODO add method display options

class Parameter(object):
    '''This is a template class for all of the parameter sub classes.
    Methods and attributes are modified and supplemented as necessary for an individual class'''

    name = 'Parameter Template'
    default_value = None
    current_value = None
    error_message = '{} is an invalid parameter value.'.format

    def __init__(self, value=None, parameter_dict=None):
        '''Create a new instance of the Parameter object.'''
        super(Parameter, self).__init__()
        if value is not None:
            self.set_value(value, parameter_dict)
        else:
            self.current_value = self.default_value

    def isvalid(self, value, parameter_dict: ParameterList):
        '''Test to see if value is a valid parameter value.
        In this template class all values are valid.'''
        if isinstance(value, object):
            return isinstance(parameter_dict, ParameterList)
        else:
            return False

    def get_value(self, parameter_dict: ParameterList):
        '''Return the sat value of the parameter.
        If no value is defined return the default value.'''
        if self.current_value is None:
            return self.get_default(parameter_dict)
        else:
            return self.current_value

    def set_value(self, value, parameter_dict: ParameterList):
        '''Set a new value for parameter.'''
        if self.isvalid(value, parameter_dict):
            self.current_value = value
        else:
            raise ValueError(self.error_message(value))

    def get_default(self, parameter_dict: ParameterList):
        '''Return the default value for the parameter'''
        return self.default_value

    def isvalue(self, value, parameter_dict: ParameterList):
        '''Test to see if self is set to "value".'''
        if self.isvalid(value, parameter_dict):
            return self.get_value(parameter_dict) == value
        else:
            return False

    def reset_value(self):
        '''Set parameter to it's default value.'''
        self.current_value = self.default_value

    def set_default(self_class, parameter_dict, value):
        '''set the default value of Parameter to "value".
        self_class is the class rather than an instance.'''
        if self_class.isvalid(self_class(), value, parameter_dict):
            new_default = self_class(value, parameter_dict).current_value
            self_class.default_value = new_default
        else:
            raise ValueError(self_class.error_message(value))
ParameterList.list_of_parameters.update({Parameter})

class OptionList(Parameter):
    '''This Parameter subclass is for parameters with values that are one of a
    set of possible values'''
    name = 'Option Template'
    description = 'This it the template class for Option Lists'
    selection_list = ('choice 1', 'choice 2', 'choice 3')
    default_value = 0
    error_message = '{} is not a valid selection'

    def set_selections(self, parameter_dict, choices):
        '''define the possible set of choices'''
        #Test type of selections_list
        if not isinstance(choices, (list, tuple, set)):
            raise TypeError('Wanted Tuple, List or Set, got {0}'.format(str(type(choices))))
        else:
            #set as new selections list
            self.selection_list = tuple(choices)

    def isvalid(self, selection, parameter_dict):
        if selection in self.selection_list:
            return True
        else:
            return False

    def get_default(self, parameter_dict):
        return self.selection_list[self.default_value]

    def set_value(self, selection, parameter_dict):
        if self.isvalid(selection, parameter_dict):
            value = [i for (i,v) in enumerate(self.selection_list) if v == selection]
            self.current_value = value[0]
        else:
            raise ValueError('{0} is not a valid choice'.format(selection))

    def get_value(self, parameter_dict):
        if self.current_value is not None:
            return self.selection_list[self.current_value]
        else:
            return self.get_default(parameter_dict)
ParameterList.list_of_parameters.update({OptionList})

class BinaryOption(Parameter):
    '''A parameter with Boolean True or False values'''
    name = 'Binary Option Template'
    description = 'This it the template class for True/False Options'
    default_value = False
    error_message = '{} is not valid. only "True" or "False" values allowed.'.format 
    
    def isvalid(self, value, parameter_dict):
        if isinstance(value, bool):
            return isinstance(parameter_dict, ParameterList)
        else:
            return False

ParameterList.list_of_parameters.update({BinaryOption})
    
class IntegerOption(Parameter):
    '''A parameter which accepts a limited range of integer values'''
    name = 'Integer Option Template'
    description = 'This it the template class for Integer Options'
    default_value = 0
    valid_range = range(-maxsize,maxsize)
    message = '{} is not a valid integer for:' + name + '.'
    error_message = message.format

    def isvalid(self, value, parameter_dict):
        '''Verify that value is an integer in valid_range'''
        if isinstance(value, int):
            return value in self.valid_range
        else:
            return False

    def set_range(self_class, parameter_dict, min=-maxsize, max=maxsize, step=1):
        if    isinstance(min, int) and \
              isinstance(max, int) and \
              isinstance(step, int):
            self_class.valid_range = range(min, max, step)
            #check for valid default value
            current_default = self_class().default_value
            if not self_class.isvalid(self_class, current_default, parameter_dict):
                self_class.default_value = None
                print('{} default value no longer valid'.format(self_class.name))
        else:
            raise ValueError('min, max and step must be integers')
ParameterList.list_of_parameters.update({IntegerOption})

class RangeOption(Parameter):
    '''A parameter which accepts a range as its value'''
    name = 'Range Option Template'
    description = 'This it the template class for range Options'
    default_value = range(1)
    error_message = '{} is not valid. Only values of type Range are allowed.'.format

    def isvalid(value, parameter_dict):
        return isinstance(value,range)
ParameterList.list_of_parameters.update({RangeOption})

class TextOption(Parameter):
    '''A parameter which accepts a test string of limited size'''
    name = 'Text Option Template'
    description = 'This it the template class for Text Options'
    default_value = ''
    max_str_length = 64
    message = '{} is not a valid text string for:' + name + '.'
    error_message = message.format

    def isvalid(self, value, parameter_dict):
        '''Verify that value is text with length less than max_size'''
        if isinstance(value, str):
            return len(value) < self.max_str_length
        else:
            return False

    def set_max_length(self_class, parameter_dict, max_len=64):
        if    isinstance(max_len, int):
            self_class.max_str_length = max_len
            #check for valid default value
            current_default = self_class().default_value
            if not self_class.isvalid(self_class, current_default, parameter_dict):
                self_class.default_value = None
                logger.debug('{} default value no longer valid'.format(self_class.name))
        else:
            raise ValueError('min, max and step must be integers')
ParameterList.list_of_parameters.update({TextOption})

class PathOption(Parameter):
    '''A parameter which accepts an object of type Path
    must_exist cane be True or False
    Path_type can be one of "any", "file", ""dir". '''
    name = 'Path Option Template'
    description = 'This it the template class for Path Options'
    default_value = Path.cwd()
    path_type = 'any' #can be "any", "file", ""dir"
    possible_path_types = {'any', 'file', 'dir'}
    must_exist = False
    message = '{} is not a valid path for:' + name + '.'
    error_message = message.format

    def isvalid(self, value, parameter_dict):
        '''Verify that value is type path and perform other tests 
        based on must_exist and Path_type'''
        if not isinstance(value, Path):
            return False
        if 'dir' in  path_type:
            if must_exist:
                if value.is_dir():
                    return True
                else:
                    return False
            else:
                if value.suffix == '':
                    return True
                else:
                    return false
        elif 'file' in  path_type:
            if must_exist:
                if value.is_file():
                    return True
                else:
                    return False
            else:
                if not value.suffix == '':
                    return True
                else:
                    return False

    def set_must_exist(self_class, parameter_dict, exist_choice=False):
        if not isinstance(exist_choice, bool):
            raise ValueError('exist_choice must be True or False')
        self_class.must_exist = exist_choice

    def set_path_type(self_class, parameter_dict, path_choice='any'):
        if not path_choice in possible_path_types:
            raise ValueError('exist_choice must be True or False')
        self_class.path_type = path_choice

ParameterList.list_of_parameters.update({PathOption})

#TODO add parameter for range of float values 

