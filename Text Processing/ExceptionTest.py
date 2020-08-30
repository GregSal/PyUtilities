#%%  Imports
from pprint import pprint

#%%  Define Exceptions
class TestException(Exception):

    @classmethod
    def print_mro(cls):
        mro_list  = [cl.__name__ for cl in cls.mro()]
        indent = '\n' + ' '*4
        mro_str = indent.join(mro_list)
        print(f'  Creating an instance of class {cls.__name__} '
              f'with parent classes:{indent}{mro_str}')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.print_mro()
        return

class StopSection(TestException):
    pass

class StopIterSection(StopIteration, TestException):
    pass

class StopIterSection2(TestException, StopIteration):
    pass


#%%  Define Helper Methods
def find_defining_class(obj, meth_name):
    for ty in type(obj).mro():
        if meth_name in ty.__dict__:
            return ty

def error_reporting(exception_name, err):
    print(f'  Stopped with Exception "{exception_name}"')
    print(f'{" "*4} Reported as: {repr(err)}')
    print(f'{" "*8} Reported with context: {repr(err.__context__)}')


def exception_print(name, err):
    print(f'Found a {name} exception:\n\t {repr(err)}\n\t'
              f'With Context:\n\t\t{repr(err.__context__)}')


#%%  Define Generators
def test_gen(n, excpt):
    print(f'do_test_gen using {excpt.__name__}')
    for i in range(10):
        if i == n:
            raise excpt
        else:
            yield i

def test_gen_r(n, excpt):
    print(f'do_test_gen using return')
    for i in range(10):
        if i == n:
            return
        else:
            yield i

def test_2nd_gen(n2, excpt2, gen, *args):
    print(f'do_test_2nd_gen using {excpt2.__name__}')
    for i in range(2, 10):
        if i == n2:
            raise excpt2
        else:
            yield from gen(i, *args)
            print(f'    Done with {gen.__name__}({i}).')

def test_2nd_gen_r(n2, excpt2, gen, *args):
    print(f'do_test_2nd_gen using return')
    for i in range(2, 10):
        if i == n2:
            return
        else:
            yield from gen(i, *args)
            print(f'    Done with {gen.__name__}({i}).')

#%% Define Example Methods
def test_sub_exception_class(excpt):
    print(f'test_sub_exception_class using {excpt.__name__}')
    try:
        raise excpt('Boo')
    except StopIteration as err:
        exception_print(StopIteration.__name__, err)
    except TestException as err:
        exception_print(TestException.__name__, err)


def do_test_gen(gen, *args):
    try:
        for j in gen(*args):
            print(f'J = {j}')
        print(f'    Done with {gen.__name__}.')
    except StopSection as err:
        error_reporting('StopSection', err)
    except StopIterSection as err:
        error_reporting('StopIterSection', err)
    except StopIteration as err:
        error_reporting('StopIteration', err)
    except RuntimeError as err:
        error_reporting('RuntimeError', err)


#%%  Run the sub exception examples
print('\n\n')
print('A parent except statement will catch sub-classed exceptions.')
test_sub_exception_class(StopSection)
print('\n\n')
print('The first matching except statement is run, others are ignored.\n'
        'Note: the "print_mro(cls)" method of "TestException" is not run.')
test_sub_exception_class(StopIterSection)
print('\n\n')
print('The order of the sub-classes does not matter here,\n'
        'but the "print_mro(cls)" method of "TestException" is run this time.')
test_sub_exception_class(StopIterSection2)

#%%  Run the single generator examples
print('\n\n')
print('StopSection raised in the generator is caught.')
do_test_gen(test_gen, 5, StopSection)
print('\n\n')
print('StopIterSection raised in the generator is converted to a '
        'RuntimeError.')
do_test_gen(test_gen, 5, StopIterSection)
print('\n\n')
print('With Return instead of a StopIteration subclass.')
do_test_gen(test_gen_r, 5, StopIterSection)


#%%  Run the multi generator examples
print('\n\n')
print('With Return at both levels instead of a StopIteration subclass.')
do_test_gen(test_2nd_gen_r, 5, StopIterSection2, test_gen_r, StopSection)
print('\n\n')
print('With Return at inner level instead of a StopIteration subclass.')
do_test_gen(test_2nd_gen, 5, StopIterSection2, test_gen_r, StopSection)
print('\n\n')
print('With Return at inner level instead of a StopIteration subclass.')
do_test_gen(test_2nd_gen, 5, StopSection, test_gen_r, StopSection)
print('\n\n')
print('With Return at outer level instead of a StopIteration subclass.')
do_test_gen(test_2nd_gen_r, 5, StopIterSection2, test_gen, StopSection)
print('\n\n')
print('With Return at outer level instead of a StopIteration subclass.')
do_test_gen(test_2nd_gen_r, 5, StopIterSection2, test_gen, StopIterSection2)
print('\n\n')
print('With StopSection at both levels.')
do_test_gen(test_2nd_gen, 5, StopSection, test_gen, StopSection)
print('\n\n')
print('With StopIterSection2 at both levels.')
do_test_gen(test_2nd_gen, 5, StopIterSection2, test_gen, StopIterSection2)
print('With StopIteration at both levels.')
do_test_gen(test_2nd_gen, 5, StopIteration, test_gen, StopIteration)


print('\n\n')
print('Really Done')

