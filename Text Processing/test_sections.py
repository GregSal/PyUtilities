import unittest
from pathlib import Path
import re
from file_utilities import clean_ascii_text
import Text_Processing as tp

#%% Test Text
from pprint import pprint
test_source_groups = [(
    'Patient Name         : ____, ____\r\n'
    'Patient ID           : 1234567\r\n'
    'Comment              : DVHs for multiple plans and plan sums\r\n'
    'Date                 : Friday, January 17, 2020 09:45:07\r\n'
    'Exported by          : gsal\r\n'
    'Type                 : Cumulative Dose Volume Histogram\r\n'
    'Description          : The cumulative DVH displays the percentage (relative)\r\n'
    '                       or volume (absolute) of structures that receive a dose\r\n'
    '                       equal to or greater than a given dose.\r\n'
    '\r\n'
    'Plan sum: Plan Sum\r\n'
    'Course: PLAN SUM\r\n'
    ), (
    'Plan sum: Plan Sum\r\n'
    'Course: PLAN SUM\r\n'
    'Prescribed dose [cGy]: not defined\r\n'
    '% for dose (%): not defined\r\n'
    '\r\n'
    'Plan: PARR\r\n'
    ), (
    'Plan: PARR\r\n'
    'Course: C1\r\n'
    'Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal\r\n'
    'Prescribed dose [cGy]: 5000.0\r\n'
    '% for dose (%): 100.0\r\n'
    '\r\n'
    'Structure: PRV5 SpinalCanal\r\n'
    )]
pprint(test_source_groups[0].splitlines())
test_result_dicts = [
    {'Patient Name': '____, ____',
     'Patient ID': '1234567',
     'Comment': 'DVHs for multiple plans and plan sums',
     'Date': 'Friday, January 17, 2020 09:45:07',
     'Exported by': 'gsal',
     'Type': 'Cumulative Dose Volume Histogram',
     'Description': ('The cumulative DVH displays the percentage (relative) '
                     'or volume (absolute) of structures that receive a dose '
                     'equal to or greater than a given dose.')
     },
     {'Plan sum': 'Plan Sum',
     'Course': 'PLAN SUM',
     'Prescribed dose': '',
     'Prescribed dose Unit': '',
     '% for dose (%)': 'not defined'
     },
     {'Plan': 'PARR',
      'Course': 'C1',
      'Plan Status': 'Treatment Approved',
      'Approved on': 'Thursday, January 02, 2020 12:55:56',
      'Approved by': 'gsal',
      'Prescribed dose': 5000.0,
      'Prescribed dose Unit': 'cGy',
      '% for dose (%)': 100.0}
     ]


#%%  Prescribed dose parse tests
class TestSectionS(unittest.TestCase):
    def setUp(self):
        self.context = {
            'File Name': 'trigger_test_text.txt',
            'File Path': base_path / 'trigger_test_text.txt',
            'Line Count': 0
            }

        dvh_info_break = [tp.SectionBreak(tp.Trigger(['Plan:', 'Plan sum:']),
                                          name='dvh_info')]
        csv.register_dialect('dvh_info',
                             delimiter=':',
                             lineterminator='\r\n',
                             skipinitialspace=True,
                             strict=False)

        dvh_info_section = Section(
            preprocessing=[clean_ascii_text],
            break_triggers=dvh_info_break,
            parsing_rules=[date_rule],
            default_parser=partial(csv_parser, dialect_name='dvh_info'),
            processed_lines = [
                tp.trim_items,
                tp.drop_blanks,
                tp.merge_continued_rows
                ],
            output_formatter = tp.to_dict
            )


    def test_dvh_info_section(self):
        source = (line for line in test_source_groups[0])
        section_output = dvh_info_section(source)
        self.assertDictEqual(section_output, test_result_dicts[0])



if __name__ == '__main__':
    unittest.main()
