'''Initial testing of dvh read
'''

#%% Imports
from pathlib import Path
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

def do_section_break(cleaned_lines):
    for cleaned_line in cleaned_lines:
        if 'Plan:' in cleaned_line:
            return
        elif 'Plan sum:' in cleaned_line:
            return
        else:
            yield cleaned_line

#%% Main Iteration
with open(test_file, newline='') as csvfile:
    cleaned_lines = clean_lines(csvfile)
    section = do_section_break(cleaned_lines)
    csvreader = csv.reader(section, delimiter=':', quotechar='"')
    trimmed_lined = trim_lines(csvreader)
    for rownum in range(16):
        row = trimmed_lined.__next__()
        print(row)
print('done')
