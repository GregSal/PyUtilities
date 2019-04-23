'''
Created on Apr 18 2019

@author: Greg Salomons
Manages string references to objects.
Intended for use with building Tkinter GUI from xml definition file.

Classes
    ReferenceTracker:
        Stores and resolves object references.

'''
import re
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Tuple, TypeVar, Union

from Utilities.data_utilities import true_iterable

LookupDict = Dict[str, Any]
LookupDef = Tuple[str, LookupDict]
ReferenceDict = Dict[str, str]
ReferenceList = List[str]
ReferenceSet = TypeVar('ReferenceSet', ReferenceList, ReferenceDict, str)
ObjectList = List
ObjectDict = Dict[str, Any]
ObjectSet = TypeVar('ObjectSet', ObjectList, ObjectDict, Any)


class ReferenceTracker():
    '''Stores and resolves object references.
    Class Attributes:
        token {str} -- The token used to indicate an object reference.
            (default: '::')
        ref_pattern {str} -- A Regular expression template used to search for
            object references. The expression contains two .format references:
                {token}: The token used to indicate an object reference.
                {id_set}: A string containing the 1 character object group
                    identifiers.
                (default: '^[{id_set}]{token}(.*)$')
    '''
    token = '::'
    ref_pattern = r'^([{id_set}]){token}(.*)$'

    def __init__(self, identifier_list: List[str] = None,
                 lookup_list: List[LookupDef] = None):
        '''ReferenceTracker object creation.

        Keyword Arguments:
            identifier_list {List[str]} -- A list of 1 character stings.
                Only the first character of each string is uses as the
                identifier. Default is None.
            lookup_list {List[LookupDef]} -- A list of 2-element tuples
                containing the identifier string and a dictionary with the
                names and objects for that reference group. Default is None.
        '''
        self.lookup_groups: LookupDict = dict()
        self.id_list: List[str] = list()
        self.ref_rx: re.Pattern = None
        if identifier_list:
            for group_id in identifier_list:
                self.add_lookup_group(group_id)
        if lookup_list:
            for (group_id, lookup) in lookup_list:
                self.add_lookup_group(group_id, lookup)
        pass

    def add_lookup_group(self, identifier: str, lookup: LookupDict = None):
        '''Create a new lookup group and assign an identifier.

        Arguments:
            identifier {str} -- A single character used to identify the group.
                Only the first character of the supplied string is uses as the
                identifier.
            lookup {LookupDict} -- A dictionary containing names and objects
                for reference. (default: {None})
        '''
        group_id = identifier[0]  # Single character identifiers only
        if lookup is None:
            lookup = OrderedDict()
        self.lookup_groups[group_id] = lookup
        self.id_list.append(group_id)
        self.build_rx()

    def build_rx(self):
        '''Compile a Regular expression search pattern to find references in a
        string.
        '''
        specs = dict(token=self.token, id_set=''.join(self.id_list))
        full_expression = self.ref_pattern.format(**specs)
        self.ref_rx = re.compile(full_expression)

    def add_item(self, identifier: str, name: str, item: Any):
        '''Add a new item for reference.

        Arguments:
            identifier {str} -- A single character used to identify the
                reference group. Only the first character of the supplied
                string is uses as the identifier.
            name {str} -- The name used to reference the group item.
            item {Any} -- The object to be referenced
        '''
        group_id = identifier[0]
        self.lookup_groups[group_id][name] = item

    def lookup_item(self, group_id: str, item_name: str)->Any:
        '''Fetch an object reference.

        Arguments:
            group_id {str} -- A single character used to identify the
                reference group. Only the first character of the supplied
                string is uses as the identifier.
            item_name {str} -- The reference name of the group item.

        Returns:
            {Any} -- The object referenced.
        '''
        return self.lookup_groups[group_id][item_name]

    def match_reference(self, item_reference: str)-> Any:
        '''Replace string references with object being referred to.
        If no valid reference is found return the original string.

        Arguments:
            item_reference {str} -- A string containing an object reference.

        Returns:
            {Any} -- The object referenced or the original string.
        '''
        matched = self.ref_rx.search(item_reference)
        if matched:
            group_id = matched.group(1)
            item_name = matched.group(2)
            return self.lookup_item(group_id, item_name)
        return item_reference

    def resolve_arg_references(self, arg_set: ReferenceList)->ObjectList:
        '''Convert a list of reference strings to their corresponding objects.

        Arguments:
            arg_set {ReferenceList} -- A list of strings containing object
                references.

        Returns:
            {ObjectList} -- A list in the same order as the original list
                with each element containing The object referenced or the
                original string.
        '''
        updated_references = list()
        for value in arg_set:
            updated_value = self.match_reference(value)
            updated_references.append(updated_value)
        return updated_references

    def resolve_kwarg_references(self, kwarg_set: ReferenceDict)->ObjectDict:
        '''Convert a dictionary of reference strings to their corresponding
            objects.

        Arguments:
            kwarg_set {List[str]} -- A dictionary of strings containing object
                references.

        Returns:
            {ObjectDict} -- A dictionary with the same keys as kwarg_set
                with the values being the object referenced or the
                original string.
        '''
        updated_kwargs = dict()
        for key_word, value in kwarg_set.items():
            updated_value = self.match_reference(value)
            updated_kwargs[key_word] = updated_value
        return updated_kwargs

    def get_attribute(self, ref_str)->Any:
        '''Convert a compound (dotted) reference into the specified attribute
        of the object reference.

        Arguments:
            ref_str {str} -- A string containing an object references and
                possibly a reference to an attribute of the object.

        Returns:
            {Any} -- The object attribute referenced or the input string.
        '''
        if '.' in ref_str:
            # Treat each . as indicating an attribute reference
            ref_set = self.resolve_arg_references(ref_str.split('.'))
            obj_def = ref_set[0]
            # if obj_def is a string, check if it a reference to a module level
            # object.
            if isinstance(obj_def, str):
                obj = self.lookup_item('G', obj_def)
            else:
                obj = obj_def
            # Recursively step through attribute layers
            for atr_str in ref_set[1:]:
                obj = getattr(obj, atr_str, ref_str)
        else:
            obj = self.match_reference(ref_str)
        return obj

    def apply_method(self, ref_str)->Any:
        '''Obtain the output of a compound (dotted) method '()' reference
        applied to the specified object reference.

        Arguments:
            ref_str {str} -- A string containing an object references and
                a reference to a method of the object.

        Returns:
            {Any} -- The output of the object method.
        '''
        # TODO Add method to call function reference
        raise NotImplementedError


    def lookup_references(self, ref_set: ReferenceSet)->ObjectSet:
        '''Convert a one or more reference strings to their corresponding
            objects.  The return container type will match the input container
            type.

        Arguments:
            ref_set {ReferenceSet} -- A dictionary, sequence or individual
            string containing object references.

        Returns:
            {ObjectDict} -- An object or container with the same structure as
                the input, with all string references replaced by the object
                referenced every non-matching element will be left unchanged.
        '''
        # If ref_set consists of a single string, return the match results for
        # that string.
        if true_iterable(ref_set):
            # Try treating ref_set as a ReferenceDict, if this fails treat as a
            # ReferenceList
            try:
                updated_references = self.resolve_kwarg_references(ref_set)
            except AttributeError:
                updated_references = self.resolve_arg_references(ref_set)
        else:
            updated_references = self.get_attribute(ref_set)
        return updated_references


def test_module_function():
    print('This is module_function')


class TestModuleClass():
    class_atr1 = 'This is class atr1'

    def __init__(self):
        self.instance_atr1 = 'This is instance attribute 1'

    def test_method(self):
        print('This is test method')

#%%

def main():
    def test_method():
        print('this is test_method')

    class TestObject():
        def __init__(self):
            self.atr1 = 'this is atr1'
            self.atr2 = 'This is atr2'
    test_lookup = ('M', {'tm': TestModuleClass})
    identifier_list = ['A', 'B']
    lookup_list = [test_lookup]
    to1 = TestObject()
     #%%
    test_ref = ReferenceTracker(identifier_list, lookup_list)
    test_ref.add_lookup_group('New', {'T1': 'test1',
                                      'T2': test_module_function})
    test_ref.add_item('A', 'I1', to1)
    test_ref.add_item('B', 'I1', test_method)
    fnc = test_ref.match_reference('B::I1')
    fnc()
    atr1 = test_ref.get_attribute('A::I1.atr1')
    print(atr1)
    fnc1 = test_ref.lookup_references('N::T2')
    fnc1()


if __name__ == '__main__':
    main()
