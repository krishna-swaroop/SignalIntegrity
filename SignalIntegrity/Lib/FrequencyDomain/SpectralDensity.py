
"""
Spectral Density
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

import math
from numpy import fft

from SignalIntegrity.Lib.FrequencyDomain.FrequencyDomain import FrequencyDomain
from SignalIntegrity.Lib.FrequencyDomain.DFTUtilities import DFTUtilities

class SpectralDensity(FrequencyDomain):
    """SpectralDensity
    Spectral density view of frequency-domain content.

    Stores per-bin amplitude spectral density values (V/sqrt(Hz)) across an
    instance of class FrequencyList.  This class is the spectral-density
    counterpart of FrequencyResponse and FrequencyContent: it represents the
    noise (or signal) spectral density distribution, and provides conversions
    to other common units (dBm/Hz, per-bin rms, per-bin dBm) as well as
    integrated quantities (total rms, total dBm), random time-domain noise
    realization, resampling onto a different FrequencyList, and a WhiteNoise()
    factory.
    @see FrequencyResponse
    @see FrequencyContent
    @see DFTUtilities
    """
    R=50.0
    P=1e-3
    LogRP10=10.*math.log10(R*P)
    def __init__(self,f=None,density=None,Keven=True):
        """Constructor
        @param f (optional) instance of class FrequencyList
        @param density (optional) list of float spectral density values in V/sqrt(Hz)
        @param Keven (optional) bool whether the corresponding time-record length K
        is even (K=2*N) or odd (K=2*N+1).  Defaults to True.
        """
        FrequencyDomain.__init__(self,f,density)
        self.Keven=Keven
    def Density(self,unit=None):
        """Density
        @param unit string defining the desired units for the spectral density.
        @return list of spectral density values in the unit specified.
        @see Values() for valid units.
        """
        return self.Values(unit)
    def Values(self,unit=None):
        """spectral density values
        @param unit (optional) string containing the unit for the values desired.
        @return list of float values in the unit specified.
        @remark
        Valid spectral-density units are:
        - 'V/sqrt(Hz)' - amplitude spectral density (default if no unit).
        - 'dBm/Hz' - power spectral density in dBm/Hz (50 ohm, 1 mW).

        If no unit is specified, the magnitudes of the spectral density values
        (V/sqrt(Hz)) are returned.

        If no spectral-density unit matches, the call defers to the
        FrequencyDomain base class for generic complex-value units such as
        'dB', 'mag', 'rad', 'deg', 'real', and 'imag'.
        @see FrequencyDomain
        """
        if unit is None or unit == 'V/sqrt(Hz)':
            return [abs(v) for v in list(self)]
        elif unit in ['dBm/Hz','dBmPerHz']:
            return [-3000. if r < 1e-15 else 20.*math.log10(r)-self.LogRP10
                    for r in self.Values('V/sqrt(Hz)')]
        else:
            return FrequencyDomain.Values(self,unit)
    def TotalRMS(self):
        """Total RMS across the spectrum
        @return float total rms = sqrt(sum(rms[n]^2)).
        """
        deltaf = DFTUtilities.DeltaFrequency((len(self)-1)*2, self.Frequencies()[-1]*2)
        return DFTUtilities.TotalSpectralContentRMS(
            DFTUtilities.rho_to_rms(
                self.Values(),
                deltaf))
    def TotaldBm(self):
        """Total power across the spectrum
        @return float total power in dBm.
        """
        deltaf = DFTUtilities.DeltaFrequency((len(self)-1)*2, self.Frequencies()[-1]*2)
        return DFTUtilities.TotalSpectralContentdBm(
            DFTUtilities.rms_to_dBm(
                DFTUtilities.rho_to_rms(
                    self.Values(),
                    deltaf)))
    def NoiseWaveform(self,td=None):
        """Generates a random time-domain noise realization from the spectral density.
        @param td (optional) instance of class TimeDescriptor describing the time
        descriptor of the waveform to produce.
        @return instance of class Waveform containing a random noise realization
        whose expected spectrum matches self.
        @remark
        Each interior bin is assigned an independent uniformly distributed phase;
        the DC bin (and the Nyquist bin when Keven) are kept real so that the
        inverse DFT yields a real-valued waveform.
        @note
        If td is None, the time descriptor corresponding to self's FrequencyList
        is used.
        """
        # pragma: silent exclude
        from SignalIntegrity.Lib.TimeDomain.Waveform.Waveform import Waveform
        # pragma: include
        fd=self.FrequencyList()
        delta_f=fd.Fe/fd.N
        rho=self.Values('V/sqrt(Hz)')
        rms=DFTUtilities.rho_to_rms(rho,delta_f,self.Keven)
        A=DFTUtilities.rms_to_A(rms,self.Keven)
        X=DFTUtilities.A_to_X(A,self.Keven,random_phase=True)
        F=DFTUtilities.Half_to_Full(X,self.Keven)
        x=[v.real for v in fft.ifft(F).tolist()]
        wf_td=fd.TimeDescriptor(Keven=self.Keven)
        wf=Waveform(wf_td,x)
        if td is not None:
            wf=wf.Adapt(td)
        return wf
    def Resample(self,fdp):
        """Resamples the spectral density to a different frequency list.
        @param fdp instance of class FrequencyList to resample to.
        @return instance of class SpectralDensity containing self resampled onto
        fdp using linear interpolation of the V/sqrt(Hz) values.
        @remark Resampling is performed on the magnitude in V/sqrt(Hz); points
        beyond self's end frequency are clamped to zero.
        """
        if fdp is None:
            return SpectralDensity(self.FrequencyList(),self.Values(),self.Keven)
        from numpy import interp
        fd=self.FrequencyList()
        old_f=list(fd)
        old_rho=self.Values('V/sqrt(Hz)')
        new_f=list(fdp)
        interpolated=interp(new_f,old_f,old_rho).tolist()
        new_rho=[float(v) if f<=old_f[-1] else 0.0
                 for f,v in zip(new_f,interpolated)]
        return SpectralDensity(fdp,new_rho,self.Keven)
    @staticmethod
    def WhiteNoise(fd,specification_type,value,noise_bandwidth=None,Keven=True):
        """Constructs a flat (white) noise SpectralDensity.
        @param fd instance of class FrequencyList for the frequency descriptor.
        @param specification_type string one of 'dBm/Hz', 'V/sqrt(Hz)', or 'Vrms'.
        @param value float the noise level expressed in the specification_type:
        - 'dBm/Hz'     : power spectral density in dBm/Hz
        - 'V/sqrt(Hz)' : amplitude spectral density in V/sqrt(Hz)
        - 'Vrms'       : total rms voltage over noise_bandwidth
        @param noise_bandwidth (optional) float bandwidth in Hz over which the
        total rms value is specified.  Required only when
        specification_type == 'Vrms'.
        @param Keven (optional) bool whether the corresponding time-record length
        is even.  Defaults to True.
        @return instance of class SpectralDensity containing a flat spectral
        density evaluated at each frequency in fd.
        """
        if specification_type == 'V/sqrt(Hz)':
            rho=value
        elif specification_type == 'dBm/Hz':
            rho=math.sqrt(SpectralDensity.R*SpectralDensity.P*
                          10.**(value/10.))
        elif specification_type == 'Vrms':
            if noise_bandwidth is None or noise_bandwidth <= 0:
                raise ValueError(
                    'noise_bandwidth must be positive for Vrms specification')
            rho=value/math.sqrt(noise_bandwidth)
        else:
            raise ValueError(
                "specification_type must be 'dBm/Hz', 'V/sqrt(Hz)', or 'Vrms'")
        return SpectralDensity(fd,[rho for _ in range(fd.N+1)],Keven)
    def __eq__(self,other):
        """overloads ==
        @param other another instance of class SpectralDensity (or FrequencyDomain).
        @return bool whether self == other.
        """
        if hasattr(other,'Keven') and self.Keven != other.Keven:
            return False
        return FrequencyDomain.__eq__(self,other)
    def __ne__(self,other):
        """overloads !=
        @param other another instance of class SpectralDensity (or FrequencyDomain).
        @return bool whether self != other.
        """
        return not self == other

    def __mul__(self, other):
        """Multiplies a FrequencyResponse by this SpectralDensity (element-wise magnitude).
        @param other instance of class FrequencyResponse.
        @return instance of class SpectralDensity where each bin is |H(f)| * SD(f).
        """
        if isinstance(other,(float,int)):
            return SpectralDensity(self.FrequencyList(),
                        [abs(h) * other for h in self.Values()],
                        self.Keven)

        return SpectralDensity(self.FrequencyList(),
            [abs(h) * s for h, s in zip(list(other), self.Values())],
            self.Keven)

    def __rmul__(self, other):
        """Right-multiply: allows FrequencyResponse * SpectralDensity.
        @param other instance of class FrequencyResponse, int, or float
        @return instance of class SpectralDensity where each bin is |H(f)| * SD(f).
        """
        return self.__mul__(other)

    def __add__(self, other):
        """Adds two SpectralDensity instances as root-sum-square.
        @param other instance of class SpectralDensity.
        @return instance of class SpectralDensity where each bin is sqrt(a^2 + b^2).
        @remark This models the combination of uncorrelated noise sources.
        """
        return SpectralDensity(self.FrequencyList(),
            [math.sqrt(a**2 + b**2) for a, b in zip(self.Values(), other.Values())],
            self.Keven)

    ##
    # @var Keven
    # bool whether the corresponding time-record length K is even (K=2*N) or
    # odd (K=2*N+1); affects Nyquist-bin handling in unit conversions and in
    # NoiseWaveform.
