'''Initial testing of dvh read
'''

#%% Imports
from pathlib import Path
from pprint import pprint
from collections import deque
from typing import List, Dict, Any
import csv
from file_utilities import clean_ascii_text
import logging_tools as lg


#%% Logging
logger = lg.config_logger(prefix='read_dvh.file')

#%% Exceptions
class StopSection(GeneratorExit): 
    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context

    def get_context(self):
        return self.context


#%% Classes
#Test class 
#Starting Identifier	string, Regex or callable	No	None	Used to identify starting text line

class TextTrigger():
    def __init__(self, sentinal_list: List[str], name='TextTrigger'):
        '''Define Text strings that signal a trigger event.
        '''
        self.sentinals = sentinal_list
        
    def apply(self, context: Dict[str, any], line: str)->(bool, str):
        logger.debug('in apply trigger')
        for sentinal in self.sentinals:
            if sentinal in line:
                return True,  sentinal
            else:
                return False
# Trigger Types:
# None
# List[str] 
# Regex 
# Callable	
#n
# If None continue  to end of file  / Stream
# If list of strings, a match with any string in the list will be a pass
# The matched string will be added to the Context dict.
# If Regex the re.match object will be added to the Context dict.
# If Callable, a non-None return value will be a pass
# The return value will be added to the Context dict.
# Triggers can be chained for "AND" operations. 
# If n skip n lines then trigger
# If Repeating sub-sections, can be number of repetitions
                
                
class SectionBreak():
    def __init__(self, trigger: TextTrigger, name='SectionBreak',
                 offset='Before'):
        self.step_back = 0
        self.set_step_back(offset)
        self.trigger = trigger            
# starting_offset	[Int or str] if str, one of Before or After
# if 0 or 'Before, Include the line that activates the Trigger in the section.
# if 1 or 'After, Skip the line that activates the Trigger.

    def set_step_back(self, offset):
        try:
            self.step_back = -(int(offset) - 1)
        except ValueError:
            if isinstance(offset, str):
                if 'Before' in offset:
                    self.step_back = 1
                elif 'After' in offset:
                    self.step_back = 0
               
    def check(self, context: Dict[str, any], line: str):
        logger.debug('in section_break.check')
        is_pass, sentinal = self.trigger.apply(context, line)
        if is_pass:
            context['sentinal'] = sentinal  
            raise StopSection(context=context)
        return is_pass, context
        #for line in source:
        #    for trigger in break_triggers:
        #        if trigger in line:    
        #            context['Source'].step_back = 1
        #            raise StopSection
        #        else:
        #            yield line

    def __iter__(self):
        '''Step through a line sequence allowing for retracing steps.
        '''
        for line in self.source:            
            if self._step_back:
                self.rewind()
            while len(self.repeat_lines) > 0:
                old_line = self.repeat_lines.pop()
                self.previous_lines.append(old_line)
                logger.debug(f'In LineIterator.__iter__, yielding old_line: {old_line}')
                yield old_line
            self.previous_lines.append(line)
            logger.debug(f'In LineIterator.__iter__, yielding line: {line}')
            yield line

def section_breaks(source, context, break_triggers):
    logger.debug('in section_breaks')
    for line in source:
        for trigger in break_triggers:
            if trigger in line:    
                context['Source'].step_back = 1
                raise StopSection
        else:
            yield line
                                              
#Break class
#	Apply Test 
#	Update Context(is_pass, *results)
#	If is_pass is True 
#		Do True action 
#	else
#		Do False
#		
#Different types depending on test method 
#	Trigger as string, list of Strings or compiled regex
#	Apply(context, line)
#		If Trigger is str
#			is_pass = Trigger in line
#			match = Trigger.search(line)
#			
#		If Trigger is re apply search 
#		Returns is_pass,  Trigger or match 

class LineIterator():
    '''Iterate through line sequence.
    '''
    def __init__(self, source, max_lines=5):
        self.source = source
        self.previous_lines = deque(maxlen=max_lines)
        self._step_back = 0
        self.repeat_lines = deque(maxlen=max_lines)
        return 

    @property
    def step_back(self):
        return self._step_back

    @step_back.setter
    def step_back(self, num_lines):
        if num_lines < 0:
            raise ValueError("Can't step back negative lines")
        if len(self.previous_lines) < num_lines:
            msg = (f"Can't step back {num_lines} lines.\n\t"
                   f"only have {len(self.previous_lines)} previous lines "
                    "available.")
            raise ValueError(msg)
        self._step_back =  num_lines

    def __iter__(self):
        '''Step through a line sequence allowing for retracing steps.
        '''
        for line in self.source:            
            if self._step_back:
                self.rewind()
            while len(self.repeat_lines) > 0:
                old_line = self.repeat_lines.pop()
                self.previous_lines.append(old_line)
                logger.debug(f'In LineIterator.__iter__, yielding old_line: {old_line}')
                yield old_line
            self.previous_lines.append(line)
            logger.debug(f'In LineIterator.__iter__, yielding line: {line}')
            yield line
        

    def rewind(self):
        for step in range(self._step_back):
            self._step_back -= 1
            if len(self.previous_lines) > 0:
                self.repeat_lines.append(self.previous_lines.pop())
        self._step_back = 0


#%% Test File
base_path = Path.cwd()

test_file_path = r'..\Testing\Test Data\Text Files'
test_file = base_path / test_file_path / 'PlanSum vs Original.dvh'

#%% Functions
def clean_lines(file):
    for raw_line in file:
        #logger.debug(f'In clean_lines, yielding raw_line: {raw_line}')
        yield clean_ascii_text(raw_line)

def trim_lines(parsed_lines):
    for parsed_line in parsed_lines:
        trimed_lines = [item.strip() for item in parsed_line]
        #logger.debug(f'In trim_lines, yielding trimed_lines: {trimed_lines}')
        yield trimed_lines


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



#%% Section definitions


def scan_section(context, break_triggers):    
    cleaned_lines = clean_lines(context['Source'])
    section = section_breaks(cleaned_lines, context, break_triggers)
    csvreader = csv.reader(section, delimiter=':', quotechar='"')
    trimmed_lined = trim_lines(csvreader)
    section_lines = list()
    while True:
        try:
            row = trimmed_lined.__next__()
            logger.debug(f'found row: {row}.')
            section_lines.append(row)
        except StopSection as stop_sign:
            pprint(stop_sign)            
            logger.debug('end of the section')
            break
        except IndexError as eof:
            pprint(eof)
            logger.debug('End of Source')
            break
        else:
            #logger.debug('next line')
            continue
    return section_lines

def plan_info_section(cleaned_lines):
    logger.debug('in plan_info section')
    for cleaned_line in cleaned_lines:
        if '% for dose (%)' in cleaned_line:
            logger.debug(f'In plan_info_section, yielding cleaned_line: {cleaned_line}')
            yield cleaned_line
            raise StopSection
        else:
            logger.debug(f'In plan_info_section, yielding cleaned_line: {cleaned_line}')
            yield cleaned_line

def plan_data_section(cleaned_lines):
    logger.debug('in plan_data section')
    for cleaned_line in cleaned_lines:
        if 'Plan:' in cleaned_line:
            cleaned_lines.step_back = 2
            logger.debug(f'In plan_data_section, yielding cleaned_lines')
            yield from plan_info_section(cleaned_lines)
        elif 'Plan sum:' in cleaned_line:
            cleaned_lines.step_back = 2
            logger.debug(f'In plan_data_section, yielding cleaned_lines')
            yield from plan_info_section(cleaned_lines)
        elif 'Structure' in cleaned_line:
            cleaned_lines.step_back = 2
            raise StopSection
        else:
            continue



#%% Main Iteration


with open(test_file, newline='') as csvfile:
    raw_lines = LineIterator(csvfile)
    context = {
        'File Name': test_file.name,
        'File Path': test_file.parent,
        'Line Count': 0,
        'Source': raw_lines
        }
    section_lines = scan_section(context, break_triggers = ['Plan:', 'Plan sum:'])
    pprint(section_lines)
    section_lines = scan_section(context, break_triggers = ['% for dose (%):', 'Structure'])
    pprint(section_lines)
print('done')

