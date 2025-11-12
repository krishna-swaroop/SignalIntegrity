"""
TestPoleZeroFitter.py
"""
# Copyright (c) 2021 Nubis Communications, Inc.
# Copyright (c) 2018-2020 Teledyne LeCroy, Inc.
# All rights reserved worldwide.
#
# This file is part of SignalIntegrity.
#
# SignalIntegrity is free software: You can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>
import unittest

import os
import SignalIntegrity.Lib as si
from SignalIntegrity.Utilities.PZ.PZ import PZ_Fitter

class TestPoleZeroFitterTest(unittest.TestCase,
                             si.test.SignalIntegrityAppTestHelper):
    def __init__(self, methodName='runTest'):
        si.test.SignalIntegrityAppTestHelper.__init__(self,os.path.dirname(os.path.realpath(__file__)))
        unittest.TestCase.__init__(self,methodName)
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.cwd=os.getcwd()
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        os.chdir(self.cwd)
    def FileNameForTest(self):
        return '_'.join(self.id().split('.'))+'.json'
    def Compare(self,result):
        try:
            del result['convergence']['time']
        except KeyError:
            pass
        try:
            del result['convergence']['completed']
        except KeyError:
            pass
        try:
            del result['configuration']['debug']
        except KeyError:
            pass
        try:
            del result['configuration']['profile']
        except KeyError:
            pass
        try:
            del result['configuration']['verbose']
        except KeyError:
            pass
        filename=self.FileNameForTest()
        self.JsonDictRegressionChecker(result,filename)
    def testPZ(self):
        args={'filename': 'MM.s4p',
              'fit_type': 'magnitude',
              'debug': False,
              'profile': False,
              'verbose': False,
              'zero_pairs': 2,
              'pole_pairs': 4,
              'guess_file': None,
              #'output_file': 'guess.json',
              'end_frequency': 100000000000.0,
              'frequency_points': 40,
              'min_delay': 0.0,
              'max_delay': 0.0,
              'max_q': 10.0,
              'initial_delay': 0.0,
              'iterations': 'infinite',
              'precision': 'super',
              'real_zeros': False,
              'lhp_zeros': True,
              'voltage_transfer_function': True,
              'fix_gain': False,
              'fix_delay': True,
              'reference_impedance': 46.0,
              'max_iterations': None,
              'mse_unchanging_threshold': None,
              'initial_lambda': 1000.0,
              'lambda_multiplier': 2.0,
              'tolerance': 1e-06,
              'max_frequency_multiplier': 5}
        result=PZ_Fitter(**args)
        self.Compare(result)
    def testPZ1(self):
        args={'filename': 'MM_s21.csv',
              'fit_type': 'complex',
              'debug': False,
              'profile': False,
              'verbose': False,
              'zero_pairs': 2,
              'pole_pairs': 4,
              'guess_file': 'guess.json',
              #'output_file': 'final.json',
              'end_frequency': 85000000000.0,
              'frequency_points': 20,
              'min_delay': 5e-12,
              'max_delay': 2e-11,
              'max_q': 10.0,
              'initial_delay': 1e-11,
              'iterations': 'infinite',
              'precision': 'super',
              'real_zeros': False,
              'lhp_zeros': True,
              'voltage_transfer_function': True,
              'fix_gain': True,
              'fix_delay': False,
              'reference_impedance': 46.0,
              'max_iterations': None,
              'mse_unchanging_threshold': None,
              'initial_lambda': 100000.0,
              'lambda_multiplier': 1.01,
              'tolerance': 1e-06,
              'max_frequency_multiplier': 5}
        result=PZ_Fitter(**args)
        self.Compare(result)
    def testPZ2(self):
        args={'filename': 'MM.s4p',
              'fit_type': 'complex',
              'debug': False,
              'profile': False,
              'verbose': False,
              'zero_pairs': 2,
              'pole_pairs': 4,
              'guess_file': None,
              #'output_file': 'final.json',
              'end_frequency': 85000000000.0,
              'frequency_points': 20,
              'min_delay': 5e-12,
              'max_delay': 2e-11,
              'max_q': 10.0,
              'initial_delay': 1e-11,
              'iterations': 'infinite',
              'precision': 'super',
              'real_zeros': False,
              'lhp_zeros': True,
              'voltage_transfer_function': True,
              'fix_gain': True,
              'fix_delay': False,
              'reference_impedance': 46.0,
              'max_iterations': None,
              'mse_unchanging_threshold': None,
              'initial_lambda': 100000.0,
              'lambda_multiplier': 1.01,
              'tolerance': 1e-06,
              'max_frequency_multiplier': 5}
        result=PZ_Fitter(**args)
        self.Compare(result)
    def testPZvgf(self):
        args={'filename': 'Fitted.s2p',
              'fit_type': 'magnitude',
              'debug': False,
              'profile': False,
              'verbose': True,
              'zero_pairs': 0,
              'pole_pairs': 40,
              'guess_file': None,
              'end_frequency': 100000000000.0,
              'frequency_points': 200,
              'min_delay': 0.0,
              'max_delay': 0.0,
              'max_q': 5.0,
              'initial_delay': 0.0,
              'iterations': 'infinite',
              'precision': 'super',
              'real_zeros': False,
              'lhp_zeros': False,
              'voltage_transfer_function': False,
              'fix_gain': False,
              'fix_delay': False,
              'reference_impedance': None,
              'max_iterations': None,
              'mse_unchanging_threshold': 1e-10,
              'initial_lambda': 100000.0,
              'lambda_multiplier': 1.01,
              'tolerance': 1e-06,
              'max_frequency_multiplier': 10.0}
        result=PZ_Fitter(**args)
        self.Compare(result)
