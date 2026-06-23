"""
TestDFTUtilites.py
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
from SignalIntegrity.App import SignalIntegrityAppHeadless
from SignalIntegrity.App import TpX
from SignalIntegrity.App import TikZ
import SignalIntegrity.Lib as si
from numpy import fft
import numpy as np

import os

class TestDFTUtilitiesTest(unittest.TestCase,si.test.SParameterCompareHelper,si.test.SignalIntegrityAppTestHelper):
    relearn=True
    debug=False
    checkPictures=True
    def __init__(self, methodName='runTest'):
        si.test.SignalIntegrityAppTestHelper.__init__(self,os.path.dirname(os.path.realpath(__file__)))
        si.test.SParameterCompareHelper.__init__(self)
        unittest.TestCase.__init__(self,methodName)
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.cwd=os.getcwd()
        os.chdir(self.path)
        from SignalIntegrity.App.SignalIntegrityAppHeadless import SignalIntegrityAppHeadless
        import SignalIntegrity.App.Project
        pysi=SignalIntegrityAppHeadless()
        self.UseSinX=SignalIntegrity.App.Preferences['Calculation.UseSinX']
        SignalIntegrity.App.Preferences['Calculation.UseSinX']=True
        self.Caching=SignalIntegrity.App.Preferences['Cache.CacheResults']
        SignalIntegrity.App.Preferences['Cache.CacheResults']=False
        self.TextLimit=SignalIntegrity.App.Preferences['Appearance.LimitText']
        SignalIntegrity.App.Preferences['Appearance.LimitText']=60
        self.RoundDisplayedValues=SignalIntegrity.App.Preferences['Appearance.RoundDisplayedValues']
        SignalIntegrity.App.Preferences['Appearance.RoundDisplayedValues']=4
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
        SignalIntegrity.App.Preferences['Cache.CacheResults']=self.Caching
        SignalIntegrity.App.Preferences['Appearance.LimitText']=self.TextLimit
        SignalIntegrity.App.Preferences['Appearance.RoundDisplayedValues']=self.RoundDisplayedValues
        SignalIntegrity.App.Preferences.SaveToFile()
        pysi=SignalIntegrityAppHeadless()
        SignalIntegrity.App.Preferences['Calculation'].ApplyPreferences()
    def testSpectralDensityToRMSAndBackKeven(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = True)
        rho2 = si.fd.DFTUtilities.rms_to_rho(rms, delta_f, Keven = True)
        for r, r2 in zip(rho, rho2):
            self.assertAlmostEqual(r, r2, places=20)
    def testSpectralDensityAddsUpToRightRMSNoiseInFDKeven(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = True)
        rms0 = si.fd.DFTUtilities.TotalSpectralContentRMS(rms)
        self.assertEqual(si.ToSI.ToSI(rms0,'V'),'5.0 mV') # should amount to 5 mV RMS noise when integrated over spectrum
    def testSpectralDensityAddsUpToRightdBmNoiseInFDKeven(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = True)
        dBm = si.fd.DFTUtilities.rms_to_dBm(rms)
        dBm0 = si.fd.DFTUtilities.TotalSpectralContentdBm(dBm)
        dBm_calc = 10*np.log10(si.ToSI.FromSI('5 mV','V')**2/si.ToSI.FromSI('50 ohm','ohm')/si.ToSI.FromSI('1 mW','W')) # power in watts of 5 mV RMS noise across 50 ohms, converted to mW
        self.assertEqual(si.ToSI.ToSI(dBm0,'dBm'),si.ToSI.ToSI(dBm_calc,'dBm')) # should amount to 5 mV RMS noise when integrated over spectrum
    def testSpectralDensityAddsUpToRightRMSNoiseInTDKeven(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = True)
        A = si.fd.DFTUtilities.rms_to_A(rms, Keven = True)
        XH = si.fd.DFTUtilities.A_to_X(A, Keven = True, random_phase = True)
        X = si.fd.DFTUtilities.Half_to_Full(XH, Keven = True)
        x = fft.ifft(X).real
        K=si.fd.DFTUtilities.K(N, Keven = True)
        rms0 = si.fd.DFTUtilities.TotalSpectralContentRMS(rms)
        self.assertEqual(si.ToSI.ToSI(rms0,'V'),'5.0 mV') # should amount to 5 mV RMS noise in time domain
    def testSpectralDensitytoTDAndBackAgainKeven(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        K=si.fd.DFTUtilities.K(N, Keven = True)
        Keven = si.fd.DFTUtilities.Keven(K)
        self.assertTrue(Keven, 'K is even')
        N2 = si.fd.DFTUtilities.N(K)
        self.assertEqual(N, N2, 'N and K consistent')
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = True)
        A = si.fd.DFTUtilities.rms_to_A(rms, Keven = True)
        XH = si.fd.DFTUtilities.A_to_X(A, Keven = True, random_phase = True)
        X = si.fd.DFTUtilities.Half_to_Full(XH, Keven = True)
        x = fft.ifft(X).real
        K=si.fd.DFTUtilities.K(N, Keven = True)
        # rms0 = (sum([v**2 for v in x])/K)**0.5
        # self.assertEqual(si.ToSI.ToSI(rms0,'V'),'5.0 mV') # should amount to 5 mV RMS noise in time domain
        X2 = fft.fft(x)
        X2H = si.fd.DFTUtilities.Full_to_Half(X2)
        A2 = si.fd.DFTUtilities.X_to_A(X2H, Keven = True)
        rms2 = si.fd.DFTUtilities.A_to_rms(A2, Keven = True)
        rho2 = si.fd.DFTUtilities.rms_to_rho(rms2, delta_f, Keven = True)
        self.assertEqual(len(rho), len(rho2))
        for r, r2 in zip(rho, rho2):
            self.assertAlmostEqual(r, r2, places=20)
    def testSpectralDensityToRMSAndBackKodd(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = False)
        rho2 = si.fd.DFTUtilities.rms_to_rho(rms, delta_f, Keven = False)
        for r, r2 in zip(rho, rho2):
            self.assertAlmostEqual(r, r2, places=20)
    def testSpectralDensityAddsUpToRightRMSNoiseInFDKodd(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = False)
        rms0 = si.fd.DFTUtilities.TotalSpectralContentRMS(rms)
        self.assertEqual(si.ToSI.ToSI(rms0,'V'),'5.0 mV') # should amount to 5 mV RMS noise when integrated over spectru
    def testSpectralDensityAddsUpToRightdBmNoiseInFDKodd(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = False)
        dBm = si.fd.DFTUtilities.rms_to_dBm(rms)
        dBm0 = si.fd.DFTUtilities.TotalSpectralContentdBm(dBm)
        dBm_calc = 10*np.log10(si.ToSI.FromSI('5 mV','V')**2/si.ToSI.FromSI('50 ohm','ohm')/si.ToSI.FromSI('1 mW','W')) # power in watts of 5 mV RMS noise across 50 ohms, converted to mW
        self.assertEqual(si.ToSI.ToSI(dBm0,'dBm'),si.ToSI.ToSI(dBm_calc,'dBm')) # should amount to 5 mV RMS noise when integrated over spectrum
    def testSpectralDensityAddsUpToRightRMSNoiseInTDKodd(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        Fe = 100e9
        f = [n/N*Fe for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = Fe/N
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = False)
        A = si.fd.DFTUtilities.rms_to_A(rms, Keven = False)
        XH = si.fd.DFTUtilities.A_to_X(A, Keven = False, random_phase = True)
        X = si.fd.DFTUtilities.Half_to_Full(XH, Keven = False)
        x = fft.ifft(X).real
        K=si.fd.DFTUtilities.K(N, Keven = False)
        rms0 = si.fd.DFTUtilities.TotalSpectralContentRMS(rms)
        self.assertEqual(si.ToSI.ToSI(rms0,'V'),'5.0 mV') # should amount to 5 mV RMS noise in time domain
    def testSpectralDensitytoTDAndBackAgainKodd(self):
        rho0 = si.ToSI.FromSI('5 mV','V')/si.ToSI.FromSI('100 GHz','Hz')**0.5 # spectral density for noise in 100 GHZ bandwidth with 5 mV RMS noise
        N = 50
        K=si.fd.DFTUtilities.K(N, Keven = False)
        Keven = si.fd.DFTUtilities.Keven(K)
        self.assertFalse(Keven, 'K is odd')
        N2 = si.fd.DFTUtilities.N(K)
        self.assertEqual(N, N2, 'N and K consistent')
        Fe_nominal = 100e9
        Fs = 2*Fe_nominal
        Fe = si.fd.DFTUtilities.EndFrequency(K, Fs)
        Fs2 = si.fd.DFTUtilities.SampleRate(K, Fe)
        self.assertEqual(Fs, Fs2, 'sample rate correct')
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        rho = [rho0 for n in range(N+1)]
        delta_f = si.fd.DFTUtilities.DeltaFrequency(K, Fs)
        rms = si.fd.DFTUtilities.rho_to_rms(rho, delta_f, Keven = False)
        A = si.fd.DFTUtilities.rms_to_A(rms, Keven = False)
        XH = si.fd.DFTUtilities.A_to_X(A, Keven = False, random_phase = True)
        X = si.fd.DFTUtilities.Half_to_Full(XH, Keven = False)
        x = fft.ifft(X).real
        
        # rms0 = (sum([v**2 for v in x])/K)**0.5
        # self.assertEqual(si.ToSI.ToSI(rms0,'V'),'5.0 mV') # should amount to 5 mV RMS noise in time domain
        X2 = fft.fft(x).tolist()
        X2H = si.fd.DFTUtilities.Full_to_Half(X2)
        A2 = si.fd.DFTUtilities.X_to_A(X2H, Keven = False)
        rms2 = si.fd.DFTUtilities.A_to_rms(A2, Keven = False)
        rho2 = si.fd.DFTUtilities.rms_to_rho(rms2, delta_f, Keven = False)
        self.assertEqual(len(rho), len(rho2))
        for r, r2 in zip(rho, rho2):
            self.assertAlmostEqual(r, r2, places=20)
    def testSineWaveContent0Keven(self):
        N = 3
        K = si.fd.DFTUtilities.K(N, Keven = True)
        Fe = 100e9
        Fs = si.fd.DFTUtilities.SampleRate(K, Fe)
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        n0 = 0
        x = [np.cos(2*np.pi*k*f[n0]/Fs) for k in range(K)]
        X = fft.fft(x).tolist()
        XH = si.fd.DFTUtilities.Full_to_Half(X)
        A = si.fd.DFTUtilities.X_to_A(XH, Keven = True)
        rms = si.fd.DFTUtilities.A_to_rms(A, Keven = True)
        self.assertEqual(si.ToSI.ToSI(rms[n0],'V',round=3),'1.0 V')
    def testSineWaveContent1Keven(self):
        N = 3
        K = si.fd.DFTUtilities.K(N, Keven = True)
        Fe = 100e9
        Fs = si.fd.DFTUtilities.SampleRate(K, Fe)
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        n0 = 1
        x = [np.cos(2*np.pi*k*f[n0]/Fs) for k in range(K)]
        X = fft.fft(x).tolist()
        XH = si.fd.DFTUtilities.Full_to_Half(X)
        A = si.fd.DFTUtilities.X_to_A(XH, Keven = True)
        rms = si.fd.DFTUtilities.A_to_rms(A, Keven = True)
        self.assertEqual(si.ToSI.ToSI(rms[n0],'V',round=3),'707.0 mV')
    def testSineWaveContent2Keven(self):
        N = 3
        K = si.fd.DFTUtilities.K(N, Keven = True)
        Fe = 100e9
        Fs = si.fd.DFTUtilities.SampleRate(K, Fe)
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        n0 = 2
        x = [np.cos(2*np.pi*k*f[n0]/Fs) for k in range(K)]
        X = fft.fft(x).tolist()
        XH = si.fd.DFTUtilities.Full_to_Half(X)
        A = si.fd.DFTUtilities.X_to_A(XH, Keven = True)
        rms = si.fd.DFTUtilities.A_to_rms(A, Keven = True)
        self.assertEqual(si.ToSI.ToSI(rms[n0],'V',round=3),'707.0 mV')
    def testSineWaveContent3Keven(self):
        N = 3
        K = si.fd.DFTUtilities.K(N, Keven = True)
        Fe = 100e9
        Fs = si.fd.DFTUtilities.SampleRate(K, Fe)
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        n0 = 3
        x = [np.cos(2*np.pi*k*f[n0]/Fs) for k in range(K)]
        X = fft.fft(x).tolist()
        XH = si.fd.DFTUtilities.Full_to_Half(X)
        A = si.fd.DFTUtilities.X_to_A(XH, Keven = True)
        rms = si.fd.DFTUtilities.A_to_rms(A, Keven = True)
        self.assertEqual(si.ToSI.ToSI(rms[n0],'V',round=3),'1.0 V')
    def testSineWaveContent0Kodd(self):
        N = 3
        K = si.fd.DFTUtilities.K(N, Keven = False)
        Fe = 100e9
        Fs = si.fd.DFTUtilities.SampleRate(K, Fe)
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        n0 = 0
        x = [np.cos(2*np.pi*k*f[n0]/Fs) for k in range(K)]
        X = fft.fft(x).tolist()
        XH = si.fd.DFTUtilities.Full_to_Half(X)
        A = si.fd.DFTUtilities.X_to_A(XH, Keven = False)
        rms = si.fd.DFTUtilities.A_to_rms(A, Keven = False)
        self.assertEqual(si.ToSI.ToSI(rms[n0],'V',round=3),'1.0 V')
    def testSineWaveContent1Kodd(self):
        N = 3
        K = si.fd.DFTUtilities.K(N, Keven = False)
        Fe = 100e9
        Fs = si.fd.DFTUtilities.SampleRate(K, Fe)
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        n0 = 1
        x = [np.cos(2*np.pi*k*f[n0]/Fs) for k in range(K)]
        X = fft.fft(x).tolist()
        XH = si.fd.DFTUtilities.Full_to_Half(X)
        A = si.fd.DFTUtilities.X_to_A(XH, Keven = False)
        rms = si.fd.DFTUtilities.A_to_rms(A, Keven = False)
        self.assertEqual(si.ToSI.ToSI(rms[n0],'V',round=3),'707.0 mV')
    def testSineWaveContent2Kodd(self):
        N = 3
        K = si.fd.DFTUtilities.K(N, Keven = False)
        Fe = 100e9
        Fs = si.fd.DFTUtilities.SampleRate(K, Fe)
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        n0 = 2
        x = [np.cos(2*np.pi*k*f[n0]/Fs) for k in range(K)]
        X = fft.fft(x).tolist()
        XH = si.fd.DFTUtilities.Full_to_Half(X)
        A = si.fd.DFTUtilities.X_to_A(XH, Keven = False)
        rms = si.fd.DFTUtilities.A_to_rms(A, Keven = False)
        self.assertEqual(si.ToSI.ToSI(rms[n0],'V',round=3),'707.0 mV')
    def testSineWaveContent3Kodd(self):
        N = 3
        K = si.fd.DFTUtilities.K(N, Keven = False)
        Fe = 100e9
        Fs = si.fd.DFTUtilities.SampleRate(K, Fe)
        f = [si.fd.DFTUtilities.Frequency(n,K,Fs) for n in range(N+1)]
        n0 = 3
        x = [np.cos(2*np.pi*k*f[n0]/Fs) for k in range(K)]
        X = fft.fft(x).tolist()
        XH = si.fd.DFTUtilities.Full_to_Half(X)
        A = si.fd.DFTUtilities.X_to_A(XH, Keven = False)
        rms = si.fd.DFTUtilities.A_to_rms(A, Keven = False)
        self.assertEqual(si.ToSI.ToSI(rms[n0],'V',round=3),'707.0 mV')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()