#%% Imports
import unittest
from pathlib import Path
from functools import partial
import re
from typing import List
from pprint import pprint
import pandas as pd
import xlwings as xw

from file_utilities import clean_ascii_text
from data_utilities import true_iterable
import logging_tools as lg
from buffered_iterator import BufferedIterator
import Text_Processing as tp
import read_dvh_file

#%% Logging
logger = lg.config_logger(prefix='Temp3', level='INFO')

class TestSectionSequencer(unittest.TestCase):
    def setUp(self):
        self.test_source = [
            'Patient Name         : ____, ____',
            'Patient ID           : 1234567',
            'Comment              : DVHs for multiple plans and plan sums',
            'Date                 : Friday, January 17, 2020 09:45:07',
            'Exported by          : gsal',
            'Type                 : Cumulative Dose Volume Histogram',
            ('Description          : The cumulative DVH displays the '
            'percentage (relative)'),
            ('                       or volume (absolute) of structures '
            'that receive a dose'),
            '                      equal to or greater than a given dose.',
            ''
            'Plan sum: Plan Sum',
            'Course: PLAN SUM',
            'Prescribed dose [cGy]: not defined',
            '% for dose (%): not defined',
            ''
            'Plan: PARR',
            'Course: C1',
            'Plan Status: Treatment Approved Thursday, January 02, '
            '2020 12:55:56 by gsal',
            'Prescribed dose [cGy]: 5000.0',
            '% for dose (%): 100.0',
            ''
            'Structure: PRV5 SpinalCanal',
            'Approval Status: Approved',
            'Plan: Plan Sum',
            'Course: PLAN SUM',
            'Volume [cm³]: 121.5',
            'Dose Cover.[%]: 100.0',
            'Sampling Cover.[%]: 100.1',
            'Min Dose [cGy]: 36.7',
            'Max Dose [cGy]: 3670.1',
            'Mean Dose [cGy]: 891.9',
            'Modal Dose [cGy]: 44.5',
            'Median Dose [cGy]: 863.2',
            'STD [cGy]: 621.9',
            'NDR: ',
            'Equiv. Sphere Diam. [cm]: 6.1',
            'Conformity Index: N/A',
            'Gradient Measure [cm]: N/A',
            ''
            'Dose [cGy] Ratio of Total Structure Volume [%]',
            '         0                       100',
            '         1                       100',
            '         2                       100',
            '         3                       100',
            '         4                       100',
            '         5                       100',
            '      3667              4.23876e-005',
            '      3668              2.87336e-005',
            '      3669              1.50797e-005',
            '      3670               1.4257e-006',
            '',
            'Structure: PTV 50',
            'Approval Status: Approved',
            'Plan: Plan Sum',
            'Course: PLAN SUM',
            'Volume [cm³]: 363.6',
            'Dose Cover.[%]: 100.0',
            'Sampling Cover.[%]: 100.0',
            'Min Dose [cGy]: 3985.9',
            'Max Dose [cGy]: 5442.0',
            'Mean Dose [cGy]: 5144.5',
            'Modal Dose [cGy]: 5177.3',
            'Median Dose [cGy]: 5166.9',
            'STD [cGy]: 131.9',
            'NDR: ',
            'Equiv. Sphere Diam. [cm]: 8.9',
            'Conformity Index: N/A',
            'Gradient Measure [cm]: N/A',
            '',
            'Dose [cGy] Ratio of Total Structure Volume [%]',
            '         0                       100',
            '         1                       100',
            '         2                       100',
            '         3                       100',
            '         4                       100',
            '         5                       100',
            '      5437               9.4777e-005',
            '      5438              6.35607e-005',
            '      5439              3.62425e-005',
            '      5440              1.82336e-005',
            '      5441              9.15003e-006',
            '      5442               6.6481e-008'
                        ]
        self.test_result = {
            'DVH Info': {
                    'Patient Name': '____, ____',
                    'Patient ID': '1234567',
                    'Comment': 'DVHs for multiple plans and plan sums',
                    'Date': 'Friday, January 17, 2020 09:45:07',
                    'Exported by': 'gsal',
                    'Type': 'Cumulative Dose Volume Histogram',
                    'Description': ('The cumulative DVH displays the '
                                    'percentage (relative) or volume '
                                    '(absolute) of structures that receive a '
                                    'dose equal to or greater than a '
                                    'given dose.')
                    },
            'Plan Info': {
                'Plan Sum': {'Plan sum': 'Plan Sum',
                                'Plan': 'Plan Sum',
                                'Course': 'PLAN SUM',
                                'Prescribed dose': '',
                                'Prescribed dose unit': '',
                                '% for dose (%)': 'not defined'},
                'PARR': {'Plan': 'PARR',
                            'Course': 'C1',
                            'Plan Status': 'Treatment Approved',
                            'Approved on': 'Thursday, January 02, 2020 12:55:56',
                            'Approved by': 'gsal',
                            'Prescribed dose': 5000.0,
                            'Prescribed dose unit': 'cGy',
                            '% for dose (%)': 100.0}
                },
            'Structures': pd.DataFrame([{
                    'Structure': 'PRV5 SpinalCanal',
                    'Approval Status': 'Approved',
                    'Plan': 'Plan Sum',
                    'Course': 'PLAN SUM',
                    'Volume [cc]': 121.5,
                    'Dose Cover.[%]': 100.0,
                    'Sampling Cover.[%]': 100.1,
                    'Min Dose [cGy]': 36.7,
                    'Max Dose [cGy]': 3670.1,
                    'Mean Dose [cGy]': 891.9,
                    'Modal Dose [cGy]': 44.5,
                    'Median Dose [cGy]': 863.2,
                    'STD [cGy]': 621.9,
                    'NDR': '',
                    'Equiv. Sphere Diam. [cm]': 6.1,
                    'Conformity Index': 'N/A',
                    'Gradient Measure [cm]': 'N/A'
                    },{
                    'Structure': 'PTV 50',
                    'Approval Status': 'Approved',
                    'Plan': 'Plan Sum',
                    'Course': 'PLAN SUM',
                    'Volume [cc]': 363.6,
                    'Dose Cover.[%]': 100.0,
                    'Sampling Cover.[%]': 100.0,
                    'Min Dose [cGy]': 3985.9,
                    'Max Dose [cGy]': 5442.0,
                    'Mean Dose [cGy]': 5144.5,
                    'Modal Dose [cGy]': 5177.3,
                    'Median Dose [cGy]': 5166.9,
                    'STD [cGy]': 131.9,
                    'NDR': '',
                    'Equiv. Sphere Diam. [cm]': 8.9,
                    'Conformity Index': 'N/A',
                    'Gradient Measure [cm]': 'N/A'
                    }]),
            'DVH': pd.DataFrame([
                {
                    'Structure': 'PRV5 SpinalCanal',
                    'Plan': 'Plan Sum',
                    'Dose [cGy]': [0, 1, 2, 3, 4, 5, 3667, 3668, 3669, 3670],
                    'Ratio of Total Structure Volume [%]': [100, 100, 100, 100,
                                                            100, 100,
                                                            4.23876e-005,
                                                            2.87336e-005,
                                                            1.50797e-005,
                                                            1.4257e-006]
                    },
                {
                    'Structure': 'PTV 50',
                    'Plan': 'Plan Sum',
                    'Dose [cGy]': [0,1,2,3,4,5,5437,5438,5439,5440,5441,5442],
                    'Ratio of Total Structure Volume [%]': [100, 100, 100, 100,
                                                            100, 100,
                                                            9.4777e-005,
                                                            6.35607e-005,
                                                            3.62425e-005,
                                                            1.82336e-005,
                                                            9.15003e-006,
                                                            6.6481e-008]
                    }])
            }
        self.context = {
            'File Name': 'Test_DVH_Sections.txt',
            'File Path': Path.cwd() / 'Text Files' / 'Test_DVH_Sections.txt',
            'Line Count': 0
            }

    def test_dvh_info_section(self):
        dvh_info_section = read_dvh_file.dvh_info_section
        # scan_section
        source = BufferedIterator(self.test_source)
        test_output = dvh_info_section.read(source, **self.context)
        self.assertDictEqual(test_output, self.test_result['DVH Info'])

    def test_plan_info_group(self):
        plan_info_group = read_dvh_file.plan_info_group
        # scan_section
        source = BufferedIterator(self.test_source)
        plan_info = plan_info_group.read(source, **self.context)
        plan_data = pd.DataFrame(plan_info)
        self.maxDiff=None
        self.assertDictEqual(plan_data.to_dict(),
                             self.test_result['Plan Info'])

    def test_dvh_group(self):
        dvh_group_section = read_dvh_file.dvh_group_section
        # scan_section
        source = BufferedIterator(self.test_source)
        structures_df, dvh_df = dvh_group_section.read(source, **self.context)
        self.maxDiff=None
        self.assertDictEqual(structures_df.to_dict(),
                             self.test_result['Structures'].to_dict())
        self.assertDictEqual(dvh_df.to_dict(),
                             self.test_result['DVH'].to_dict())
