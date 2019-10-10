# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 11:27:26 2019

@author: gsalomon
"""
# %% test Strings

s1 = '            FieldSSD; 100.0 cm'
s2 = '            FieldActualSSD; -'
s3 = '            X1: +10.0 cm'

# %% define
import re

delim = ':;'      # Possible value delimiters
name_chrs = ' ,='  # allowable name characters (besides letters)
header_name_ptn = (
    '^'                # beginning of string
    '\s*'              # possible space before the header name begins
    '(?P<name>'        # beginning of name string group
    '[\w{chrs}]+'      # name text with allowable name characters
    ')'                # end of name string group
    '[{delim}]{1,2}'   # header delimiter with value delimiters
    '\s*'              # possible space before the header value begins
    )
generic_value_ptn = (
    '(?P<value>'       # beginning of value string group
    '[\w, ]+'          # value string
    ')'                # end of value string group
    '.*'               # possible space after the value ends
    '$'                # end of string
    )
number_value_ptn = (
    '(?P<value>'       # beginning of value number group
    '[-+]?'            # initial sign
    '\d+'              # float value before decimal
    '[.]?'             # decimal Place
    '\d*'              # float value after decimal
    ')'                # end of value string group
    '\s*'              # possible space before the unit begins
    '(?P<unit>'        # beginning of possible unit string group
    '[\w]*'            # value unit
    ')'                # end of unit string group
    '.*'               # possible space after the value ends
    '$'                # end of string
    )
field_size_value_ptn = (
    '(?P<x_value>'     # beginning of x_value string group
    '\d+\.?\d*'        # float value
    ')'                # end of x_value string group
    '\s*x\s*'          # x delimiter with possible space
    '(?P<y_value>'     # beginning of y_value string group
    '\d+\.?\d*'        # float value
    ')'                # end of y_value string group
    '\s*'              # possible space before the unit begins
    '(?P<unit>'        # beginning of possible unit string group
    '[\w]*'            # value unit
    ')'                # end of unit string group
    '.*'               # possible space after the value ends
    '$'                # end of string
    )
# Can't use format method because there are {} in the re expression
name_ptn = header_name_ptn.replace('{delim}', delim)
name_ptn = name_ptn.replace('{chrs}', name_chrs)
# Compile expressions
header_re = re.compile(name_ptn + generic_value_ptn)
number_header_re = re.compile(name_ptn + number_value_ptn)
field_size_header_re = re.compile(name_ptn + field_size_value_ptn)




# %% Run check
str_found = header_re.search(s1)
str_data = str_found.groupdict()
num_found = number_header_re.search(s1)
num_data = num_found.groupdict()

# %% Run check
str_found = header_re.search(s3)
str_data = str_found.groupdict()
num_found = number_header_re.search(s3)
num_data = num_found.groupdict()

# %% Run check
str_found = header_re.search(s2)
str_data = str_found.groupdict()
num_found = number_header_re.search(s2)
num_data = num_found.groupdict()
