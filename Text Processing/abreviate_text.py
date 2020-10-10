# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from pathlib import Path
import re

base_dir = Path.cwd()
keep_line1 = re.compile('^.+[a-zA-Z].*\n')
drop_line1 = re.compile('^ +[ 1234]?[0-9]{1,3}.*\n')
drop_line2 = re.compile('^ +5[0-3][0-9]{2}.*\n')

def abr_file(source_file, target_file):
    new_text= list()
    with source_file.open('r',encoding='UTF-8') as file:
        for line in file:
            if keep_line1.match(line) is not None:
                new_text.append(line)
            elif drop_line1.match(line) is None:
                if drop_line2.match(line) is None:
                    new_text.append(line)

    target_file.write_text(''.join(new_text),encoding='UTF-8')


source_file = base_dir / 'PlanSum Only.dvh'
target_file = base_dir / 'PlanSum Only Abbreviated.txt'
abr_file(source_file, target_file)

source_file = base_dir / 'PlanSum vs Original.dvh'
target_file = base_dir / 'PlanSum vs Original Abbreviated.txt'
abr_file(source_file, target_file)

source_file = base_dir / 'Test1.dvh'
target_file = base_dir / 'Test1 Abbreviated.txt'
abr_file(source_file, target_file)

# #%%
# file = text_file.open('r',encoding='UTF-8')
# line = file.readline()
# for i in range(30):
#     line = file.readline()