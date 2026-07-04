"""
TestStatisticalNoise.py
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
import SignalIntegrity.Lib as si
import SignalIntegrity.App.SignalIntegrityAppHeadless as siapp
import os
import math
import SignalIntegrity.App.Project as proj
from SignalIntegrity.Lib.Test.SignalIntegrityAppTestHelper import SignalIntegrityAppTestHelper

class TestStatisticalNoiseTest(unittest.TestCase,
        si.test.SParameterCompareHelper,si.test.SignalIntegrityAppTestHelper,
        si.test.RoutineWriterTesterHelper):
    relearn=True
    plot=False
    debug=False
    checkPictures=True
    epsilon=50e-12
    plotErrors=True
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.cwd=os.getcwd()
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        from SignalIntegrity.App.SignalIntegrityAppHeadless import SignalIntegrityAppHeadless
        import SignalIntegrity.App.Project
        pysi=SignalIntegrityAppHeadless()
        self.UseSinX=SignalIntegrity.App.Preferences['Calculation.UseSinX']
        SignalIntegrity.App.Preferences['Calculation.UseSinX']=True
        SignalIntegrity.App.Preferences.SaveToFile()
        pysi=SignalIntegrityAppHeadless()
        SignalIntegrity.App.Preferences['Calculation'].ApplyPreferences()
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        os.chdir(self.cwd)
        from SignalIntegrity.App.SignalIntegrityAppHeadless import SignalIntegrityAppHeadless
        import SignalIntegrity.App.Project
        pysi=SignalIntegrityAppHeadless()
        SignalIntegrity.App.Preferences['Calculation.UseSinX']=self.UseSinX
        SignalIntegrity.App.Preferences.SaveToFile()
        pysi=SignalIntegrityAppHeadless()
        SignalIntegrity.App.Preferences['Calculation'].ApplyPreferences()
    def __init__(self, methodName='runTest'):
        si.test.SParameterCompareHelper.__init__(self)
        unittest.TestCase.__init__(self,methodName)
        si.test.SignalIntegrityAppTestHelper.__init__(self,os.path.dirname(os.path.realpath(__file__)))
        si.test.RoutineWriterTesterHelper.__init__(self)
    def testStatisticalNoise(self):
        self.SimulationResultsChecker('StatisticalNoise.si',checkNoise = True)
    def testStatisticalNoiseAbove(self):
        self.SimulationResultsChecker('StatisticalNoiseExternal.si',checkNoise = True)
    def testNoiseWaveform(self):
        """
        This simulation has five probes VO1-VO5.

        The first is for an actual noise waveform specified: 10 mVrms of noise at 80 GS/s (to 40 GHz).
        The second is a statistical noise source specified with 10 mVrms of noise to 40 GHz.
        The third is a statistical noise source specified with a waveform generated in 1.
        The fourth is the time domain waveform used for the third statistical noise source.
        The fifth is a statistical noise source specified with a spectral density file with 15.81 nV/sqrt(Hz) to 100 GHz.

        Therefore, VO1 and VO4 produce actual waveforms and zero noise spectral density.
        VO2 and VO3 and V04 produce a 0V DC waveform with spectral density.
        
        """
        results = self.SimulationResultsChecker('StatisticalNoiseWaveforms.si',checkNoise = True, checkWaveforms = False)
        VO1_wf = results['output waveforms'][results['output waveform labels'].index('VO1')]
        VO2_wf = results['output waveforms'][results['output waveform labels'].index('VO2')]
        VO3_wf = results['output waveforms'][results['output waveform labels'].index('VO3')]
        VO4_wf = results['output waveforms'][results['output waveform labels'].index('VO4')]
        VO5_wf = results['output waveforms'][results['output waveform labels'].index('VO5')]
        VO1_sd = results['noise']['output_noise_spectral_density']['VO1']
        VO2_sd = results['noise']['output_noise_spectral_density']['VO2']
        VO3_sd = results['noise']['output_noise_spectral_density']['VO3']
        VO4_sd = results['noise']['output_noise_spectral_density']['VO4']
        VO5_sd = results['noise']['output_noise_spectral_density']['VO5']
        from SignalIntegrity.Lib.ToSI import ToSI

        # VO1
        self.assertEqual(ToSI(VO1_wf.rms(),'Vrms',round=2),'10.0 mVrms')
        self.assertEqual(ToSI(VO1_wf.SpectralDensity().TotalRMS(),'Vrms',round=2),'10.0 mVrms')
        self.assertEqual(ToSI(VO1_sd['Vrms'],'Vrms'),'0 Vrms')

        # VO2
        self.assertEqual(ToSI(VO2_sd['Vrms'],'Vrms',round=2),'10.0 mVrms')
        self.assertEqual(ToSI(VO2_wf.rms(),'Vrms'),'0 Vrms')

        # VO3
        self.assertEqual(ToSI(VO3_sd['Vrms'],'Vrms',round=2),'10.0 mVrms')
        self.assertEqual(ToSI(VO3_wf.rms(),'Vrms'),'0 Vrms')

        # VO4
        self.assertEqual(ToSI(VO4_wf.rms(),'Vrms',round=2),'10.0 mVrms')
        self.assertEqual(ToSI(VO4_wf.SpectralDensity().TotalRMS(),'Vrms',round=2),'10.0 mVrms')
        self.assertEqual(ToSI(VO4_sd['Vrms'],'Vrms'),'0 Vrms')

        # VO5
        # this generates 10 mVrms of total noise by having 10 lanes of noise
        self.assertEqual(ToSI(VO5_sd['Vrms'],'Vrms',round=2),'10.0 mVrms')
        self.assertEqual(ToSI(VO5_wf.rms(),'Vrms'),'0 Vrms')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()