'''Make subclass of parameters that accepts a string
		Test instance creation passing:
 Nothing,
				□ Verify not initialized
				□ Verify returns default of None
				□ Verify default can be changed
				□ Verify returns default value
				□ Verify trying to set invalid default raises error
				□ Verify value can be set
				□ Verify invalid value raises error
				□ Verify reset sets value to default
				□ Verify that equality test compares with value
				□ Verify that error message can be altered
				□ Verify that str returns a string version of the value
				□ Verify that __repr__ returns a string representative of the current state
				□ Verify that copy reproduces the instance state

'''

from parameters import Parameter
from parameters import NotValidError

class StringP(Parameter):
    '''A Test String Parameter
    '''
    _name = 'Test String'
    _type = str


    def __init__(self, **kwds):
        '''Create a new instance of the string parameter.'''
        super().__init__(**kwds)

    def isvalid(self, value):
        '''Check that value is a string.
        '''
        return super().isvalid(value)

test_param = StringP()
print('is initialized: ' + str(test_param.is_initialized()))

print('test_param value is: ' + str(test_param.value))

test_param.set_default('default')
print('test_param value is: ' + str(test_param.value))

try:
    test_param.set_default(1)
except NotValidError as err:
    print(err)

test_param.value = 'value'
print('test_param value is: ' + str(test_param.value))

def err_test():
    try:
        test_param.value = 1
    except NotValidError as err:
        return err

print(test_param.__dict__)
print(test_param.__class__)
print(test_param.__class__._type)
print(test_param.__dir__())
print(test_param.__class__.__dict__)

class A(): pass
a = A()
a.__repr__()
