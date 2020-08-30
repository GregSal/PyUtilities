'''Initial testing of dvh read
'''

#%% Imports
from pathlib import Path
from pprint import pprint
import csv
from file_utilities import clean_ascii_text

#%% Exceptions
class StopSection(Exception): pass

#%% Test File
base_path = Path.cwd()

test_file_path = r'..\Testing\Test Data\Text Files'
test_file = base_path / test_file_path / 'PlanSum vs Original.dvh'

#%% Functions
def clean_lines(file):
    for raw_line in file:
        yield clean_ascii_text(raw_line)

def trim_lines(parsed_lines):
    for parsed_line in parsed_lines:
        yield[item.strip() for item in parsed_line]

def dvh_info_section(cleaned_lines):
    yield 'in dvh_info section'
    for cleaned_line in cleaned_lines:
        if 'Plan:' in cleaned_line:
            raise StopSection
        elif 'Plan sum:' in cleaned_line:
            raise StopSection
        else:
            yield cleaned_line

def plan_info_section(cleaned_lines):
    yield 'in plan_info section'
    for cleaned_line in cleaned_lines:
        if '% for dose (%)' in cleaned_line:
            yield cleaned_line
            raise StopSection
        else:
            yield cleaned_line

def plan_data_section(cleaned_lines):
    yield 'in plan_data section'
    for cleaned_line in cleaned_lines:
        if 'Plan:' in cleaned_line:
            yield from plan_info_section(cleaned_lines)
        elif 'Plan sum:' in cleaned_line:
            yield from plan_info_section(cleaned_lines)
        elif 'Structure' in cleaned_line:
            raise StopSection
        else:
            continue


def drop_units(text: str)->float:
    number_value_pattern = (
        '^'                # beginning of string
        '\s*'              # Skip leading whitespace
        '(?P<value>'       # beginning of value integer group
        '[-+]?'            # initial sign
        '\d+'              # float value before decimal
        '[.]?'             # decimal Place
        '\d*'              # float value after decimal
        ')'                # end of value string group
        '\s*'              # skip whitespace
        '(?P<unit>'        # beginning of value integer group
        '[^\s]*'           # units do not contain spaces
        ')'                # end of unit string group
        '\s*'              # drop trailing whitespace
        '$'                # end of string
        )
    #find_num = re.compile(number_value_pattern)
    find_num = re.findall(number_value_pattern, text)
    if find_num:
        value, unit = find_num[0]
        return value
    return text



#%% Main Iteration
with open(test_file, newline='') as csvfile:
    cleaned_lines = clean_lines(csvfile)
    section = dvh_info_section(cleaned_lines)
    csvreader = csv.reader(section, delimiter=':', quotechar='"')
    trimmed_lined = trim_lines(csvreader)
    for rownum in range(25):
        try:
            row = trimmed_lined.__next__()
            print(row)
        except StopSection:
            section = plan_data_section(cleaned_lines)
            csvreader = csv.reader(section, delimiter=':', quotechar='"')
            trimmed_lined = trim_lines(csvreader)
            for rownum in range(25):
                try:
                    row = trimmed_lined.__next__()
                    print(row)
                except StopSection as stop_sign:
                    pprint(stop_sign)
                    print('end of the line')
                    break
                else:
                    continue
        else:
            continue
        break
print('done')


