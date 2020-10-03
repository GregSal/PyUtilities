'''Test the Regular expression parsing of file data.
Defines Regular Expressions for parsing file data in the format:
date  time  file size file name
eg:
    07/03/2017  09:45          29274112 Course Planning.one
    2016-04-21  02:06 PM              3491 xcopy.txt

Allows for the following date and time formats
Short date
	yyyy-MM-dd
	dd/MM/yyyy
	dd/MM/yy
	d/M/yy
	yy-MM-dd
	M/dd/yy
	dd-MMM-yy
	dd-MMM-yy
Long date
	MMMM d, yyyy
	dddd, MMMM dd, yyyy
	MMMM-dd-yy
	d-MMM-yy
Long time
	h:mm:ss tt
	hh:mm:ss tt
	HH:mm:ss
	H:mm:ss
Short Time
	h:mm tt
	hh:mm tt
	HH:mm tt
	H:mm
'''

from pathlib import Path
import re


def build_file_re():
    pattern = (
        '^'                 # beginning of string
        '(?P<date>'         # beginning of date string group
         '[a-zA-Z0-9]+'     # Month Day or year as a number or text
         '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
         '[a-zA-Z0-9]+'     # Month Day or year as a number or text
         '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
         '\d{2,4}'          # day or year as a number
         '((?<=, )\d{2,4})?'# Additional year section if the day name was included
        ')'                 # end of date string group
        '\s+'               # gap between date and time
        '(?P<time>'         # beginning of time string group
         '\d{1,2}'          # Hour as 1 or 2 digits
         ':'                # Time delimiter
         '\d{1,2}'          # Minutes as 1 or 2 digits
         ':?'               # Time delimiter
         '\d{0,2}'          # Seconds (optional) as 0,  1 or 2 digits
         '\s?'              # possible space separating time from AM/PM indicator
         '[aApPmM]{0,2}'    # possible AM/PM in upper or lower case
         ')'                # end of time string group
        '\s+'               # space between date & time and file size
        '(?P<size>\d+)'     # file size as digits  (group)
        '\s+'               # space between file size and file name
        '(?P<name>[^.]+)'   # File name (group)
        '(?P<ext>[.]?\w*)'  # Extension including'.' (group)
        '$'                 # end of string
        )
    file_re_p = re.compile(pattern)
    return file_re_p


def build_summary_re():
    '''Compile a regular expression for parsing a dir summary line.
    '''
    num_files_pattern = (
        '^'                # beginning of string
        '\s*'              # possible initial white space
        '(?P<num_files>'   # beginning of number of files string group
        '[\d,]+'           # Digits and comma to form an integer
        ')'                # end of number of files string group
        '\s+'              # gap between number and text
        'File\(s\)'        # Files delimiter
        )
    size_pattern = (
        '\s+'              # gap between number of files and dir size
        '(?P<size>'        # beginning of dir size string group
        '[\d,]+'           # Digits and comma to form an integer
        ')'                # end of dir size string group
        '\s+'              # gap between number and text
        'bytes'            # dir size delimiter
        '\s+'              # ending white space
        '$'                # end of string
        )
    summary_re = re.compile(num_files_pattern + size_pattern)
    return summary_re

def output_str(data_dict, variables):
    '''Build a comma separated string from the parsed file data.
    '''
    if data_dict:
        item_list = [data_dict.get(item,'').strip()
                     for item in variables]
        item_str = ','.join(item_list) + '\n'
    else:
        item_str = ''
    return item_str


def search_files(test_data, file_re_p, variables):
    '''Scan through all lines and parse file data.
    '''
    file_re_test_str = ''
    for line in test_data:
        found = file_re_p.search(line)
        if found:
            data_dict = found.groupdict()
            item_str = output_str(data_dict, variables)
            file_re_test_str += item_str
    return file_re_test_str


def main():
    base_path = Path.cwd() / 'Testing code and Data'
    test_dir_file1 = base_path / 'test_files.txt'
    test_dir_file2 = base_path / r'OneDrive Test Data\Old OneDrive for Business dir_output.txt'
    test_data = test_dir_file1.read_text().split('\n')
    test_data2 = test_dir_file2.read_text().split('\n')
    test_data.extend(test_data2)

    file_re_p = build_file_re()
    variables = ['date', 'time', 'size', 'name', 'ext']
    file_re_test_results = search_files(test_data, file_re_p, variables)

    file_re_test_str = ','.join(variables) + '\n' + file_re_test_results
    out_file = base_path / 'test_regex_out.txt'
    out_file.write_text(file_re_test_str)

    if __name__ == '__main__':
        main()
