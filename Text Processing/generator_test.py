from inspect import isgenerator, isgeneratorfunction
from collections.abc import Iterable, Iterator, Generator, Sequence
import inspect
from pprint import pprint

# Define a list
basic_list = [1, 2, 3, 4, 5]

basic_range = range(5)



variable = basic_list
variable_name = 'Basic List'
print(f'{variable_name}:\t{variable}')
print(f'Is {variable_name} a Sequence?:\t{isinstance(variable, Sequence)}')
print(f'Is {variable_name} an Iterable?:\t{isinstance(variable, Iterable)}')
print(f'Is {variable_name} an Iterator?:\t{isinstance(variable, Iterator)}')
print(f'Is {variable_name} a Generator?:\t{isinstance(variable, Generator)}')
print(f'Is {variable_name} a Generator?:\t{isgenerator(variable)}')
print(f'Is {variable_name} a Generator Function?:\t{isgeneratorfunction(variable)}')
inspect.getgeneratorstate(a)
try:
    a_gen.__next__()
except:
    print(f"{variable_name} Can't do __next__()"
    "    print('cant do next')

def a_gen(seq):
    for n in seq:
        yield n

def b_gen(seq):
    return (n for n in seq)

seq = range(5)
a = a_gen(seq)
print(a)
b = b_gen(seq)
print(b)
print(b.__next__())
print(a.__next__())
pprint(inspect.getmembers(a))

print(isgenerator(a_gen))
print(isgeneratorfunction(a_gen))

print(isgenerator(b_gen))
print(isgeneratorfunction(b_gen))

print(isgenerator(a))
print(isgenerator(b))
print(isgeneratorfunction(a))
print(isgeneratorfunction(b))
inspect.getgeneratorstate(a)
hasattr(a,'__next__')
hasattr(a,'__iter__')
try:
    a_gen.__next__()
except:
    print('cant do next')
