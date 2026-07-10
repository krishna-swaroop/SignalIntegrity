"""
StatisticalNoisePreferencesFile.py
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
from SignalIntegrity.App.ProjectFileBase import XMLConfiguration,XMLPropertyDefaultString,XMLPropertyDefaultInt,XMLPropertyDefaultBool,XMLPropertyDefaultFloat,XMLPropertyDefaultFile
import math

class WhiteNoiseConfiguration(XMLConfiguration):
    def __init__(self):
        super().__init__('WhiteNoise')
        self.Add(XMLPropertyDefaultString('SpecificationType','V/sqrt(Hz)')) # Allowed values: 'dBm/Hz', 'V/sqrt(Hz)', 'V^2/GHz', 'Vrms', 'ENOB', or 'COM TX'.
        self.Add(XMLPropertyDefaultFloat('NoisedBmPerHz',0.0)) # Noise density in dBm/Hz.
        self.Add(XMLPropertyDefaultFloat('VPerRootHz',0.0)) # Noise density in V/sqrt(Hz).
        self.Add(XMLPropertyDefaultFloat('VSquaredPerGHz',0.0)) # Noise density in V^2/GHz.
        self.Add(XMLPropertyDefaultFloat('VRms',0.0)) # Total noise in Vrms integrated over NoiseBandwidth (i.e., density in V/sqrt(Hz) * sqrt(NoiseBandwidth)).
        self.Add(XMLPropertyDefaultFloat('ENOB',0.0)) # Effective number of bits used for COM RX noise specification.
        self.Add(XMLPropertyDefaultFloat('Vpp',1.0)) # Peak-to-peak voltage used for COM TX/COM RX derived-noise calculations.
        self.Add(XMLPropertyDefaultFloat('h0',1.0)) # COM TX FFE cursor tap height used to scale noise density.
        self.Add(XMLPropertyDefaultFloat('SNRdB',33.0)) # COM TX signal-to-noise ratio in dB used to derive noise.
        self.Add(XMLPropertyDefaultFloat('Risetime',0.0)) # COM TX transmitter 20-80 risetime in seconds used for Gaussian spectral shaping.
        self.Add(XMLPropertyDefaultFloat('NoiseBandwidth',0.0)) # Noise bandwidth in Hz used for Vrms integration and white-noise support.

    def _noiseVrmsFromComTx(self):
        return self['h0'] * self['Vpp'] / 2.0 * (10.0 ** (-self['SNRdB'] / 20.0))

    def NoiseDensity(self):
        from SignalIntegrity.Lib.FrequencyDomain.DFTUtilities import DFTUtilities
        spec_type = self['SpecificationType']
        if spec_type == 'dBm/Hz':
            value = self['NoisedBmPerHz']
        elif spec_type == 'V/sqrt(Hz)':
            value = self['VPerRootHz']
        elif spec_type == 'V^2/GHz':
            value = self['VSquaredPerGHz']
        elif spec_type == 'Vrms':
            value = self['VRms']
        elif spec_type == 'ENOB':
            bw = self['NoiseBandwidth']
            if bw is None or bw <= 0:
                raise ValueError('NoiseBandwidth must be > 0 for ENOB specification')
            vpp = self['Vpp']
            enob = self['ENOB']
            snr_db = 6.02 * enob + 1.76
            signal_vrms = vpp / (2.0 * math.sqrt(2.0))
            value = signal_vrms / (10.0 ** (snr_db / 20.0))
            spec_type = 'Vrms'
        elif spec_type == 'COM TX':
            bw = self['NoiseBandwidth']
            if bw is None or bw <= 0:
                raise ValueError('NoiseBandwidth must be > 0 for COM TX specification')
            value = self._noiseVrmsFromComTx()
            spec_type = 'Vrms'
        else:
            raise ValueError(f'Unknown SpecificationType: {spec_type}')
        return DFTUtilities.ConvertSpectralDensity(
            value, spec_type, 'V/sqrt(Hz)', bw=self['NoiseBandwidth'])

    def SpectralDensity(self, EndFrequency, FrequencyPoints):
        from SignalIntegrity.Lib.FrequencyDomain.SpectralDensity import SpectralDensity
        from SignalIntegrity.Lib.FrequencyDomain.FrequencyList import EvenlySpacedFrequencyList
        fl = EvenlySpacedFrequencyList(EndFrequency, FrequencyPoints)
        noiseDensity = self.NoiseDensity()
        noiseBandwidth = self['NoiseBandwidth']
        spec_type = self['SpecificationType']
        if spec_type == 'COM TX':
            from SignalIntegrity.Lib.TimeDomain.Filters.Risetime.Gaussian import Gaussian
            risetime = self['Risetime']
            density = []
            for f in fl:
                if f == 0.0 or f > noiseBandwidth:
                    density.append(0.0)
                elif risetime is None or risetime <= 0.0:
                    density.append(noiseDensity)
                else:
                    density.append(noiseDensity * math.exp(-2.0 * (math.pi * f * risetime / Gaussian.a2080) ** 2))
            return SpectralDensity(fl, density)
        return SpectralDensity(
            fl,
            [0.0 if (f == 0.0 or f > noiseBandwidth) else noiseDensity for f in fl])

class SpectralDensityFileConfiguration(XMLConfiguration):
    def __init__(self):
        super().__init__('SpectralDensityFile')
        self.Add(XMLPropertyDefaultFile('FileName',''))
    def SpectralDensity(self, EndFrequency, FrequencyPoints):
        from SignalIntegrity.Lib.FrequencyDomain.SpectralDensity import SpectralDensity
        from SignalIntegrity.Lib.FrequencyDomain.FrequencyList import EvenlySpacedFrequencyList
        fl = EvenlySpacedFrequencyList(EndFrequency, FrequencyPoints)
        return SpectralDensity().ReadFromFile(self['FileName']).Resample(fl)

class NoiseWaveformFileConfiguration(XMLConfiguration):
    def __init__(self):
        super().__init__('WaveformFile')
        self.Add(XMLPropertyDefaultFile('FileName',''))
    def SpectralDensity(self, EndFrequency, FrequencyPoints):
        from SignalIntegrity.Lib.FrequencyDomain.FrequencyList import EvenlySpacedFrequencyList
        from SignalIntegrity.Lib.TimeDomain.Waveform import Waveform
        fl  = EvenlySpacedFrequencyList(EndFrequency, FrequencyPoints)
        wf = Waveform().ReadFromFile(self['FileName'])
        return wf.SpectralDensity(fl)

class JohnsonNoiseConfiguration(XMLConfiguration):
    def __init__(self):
        super().__init__('Johnson')
        self.Add(XMLPropertyDefaultFloat('Temperature_Kelvin',298.15)) # Temperature in Kelvin (default: 25 C).
        self.Add(XMLPropertyDefaultFloat('Resistance',50.0)) # Resistance in ohms (default: 50 ohms).
    def SpectralDensity(self, EndFrequency, FrequencyPoints):
        from SignalIntegrity.Lib.FrequencyDomain.SpectralDensity import SpectralDensity
        from SignalIntegrity.Lib.FrequencyDomain.FrequencyList import EvenlySpacedFrequencyList
        fl = EvenlySpacedFrequencyList(EndFrequency, FrequencyPoints)
        import scipy.constants as const
        import math
        # Boltzmann constant in Joules per Kelvin
        k_B = const.k
        noiseDensity = math.sqrt(4.*k_B*self['Temperature_Kelvin']*self['Resistance'])
        noiseBandwidth = self.wn_property['NoiseBandwidth']
        return SpectralDensity(
            fl,
            [0.0 if (f == 0.0 or f > noiseBandwidth) else noiseDensity for f in fl])

class CrosstalkNoiseFromProbeConfiguration(XMLConfiguration):
    def __init__(self):
        super().__init__('Crosstalk')
        self.Add(XMLPropertyDefaultString('ProbeName',''))
    def SpectralDensity(self, EndFrequency, FrequencyPoints, output_waveforms=None, output_waveform_names=None):
        from SignalIntegrity.Lib.FrequencyDomain.SpectralDensity import SpectralDensity
        from SignalIntegrity.Lib.FrequencyDomain.FrequencyList import EvenlySpacedFrequencyList
        fl = EvenlySpacedFrequencyList(EndFrequency, FrequencyPoints)
        if output_waveforms is None or output_waveform_names is None:
            return SpectralDensity(fl, [0.0 for _ in fl])
        probe_name = self['ProbeName']
        if probe_name in output_waveform_names:
            waveform = output_waveforms[output_waveform_names.index(probe_name)]
            return waveform.SpectralDensity(fl)
        return SpectralDensity(fl, [0.0 for _ in fl])

class NoiseConfiguration(XMLConfiguration):
    def __init__(self):
        super().__init__('Noise')
        self.Add(XMLPropertyDefaultBool('Enable',False))
        self.Add(XMLPropertyDefaultString('Type','WhiteNoise')) # 'WhiteNoise', 'SpectralDensityFile', 'WaveformFile', 'Johnson', or 'Crosstalk'
        self.SubDir(WhiteNoiseConfiguration())
        self.SubDir(SpectralDensityFileConfiguration())
        self.SubDir(NoiseWaveformFileConfiguration())
        self.SubDir(JohnsonNoiseConfiguration())
        self.SubDir(CrosstalkNoiseFromProbeConfiguration())
        self['Johnson'].wn_property = self['WhiteNoise']
        self.Add(XMLPropertyDefaultFloat('Lanes',1.0))
    def SpectralDensity(self, EndFrequency, FrequencyPoints, output_waveforms=None, output_waveform_names=None):
        from SignalIntegrity.Lib.FrequencyDomain.SpectralDensity import SpectralDensity
        from SignalIntegrity.Lib.FrequencyDomain.FrequencyList import EvenlySpacedFrequencyList
        import math
        fl = EvenlySpacedFrequencyList(EndFrequency, FrequencyPoints)
        if not self['Enable']:
            return SpectralDensity(fl, [0.0 for _ in fl])
        noiseType = self['Type']
        lanes = self['Lanes']
        if noiseType == 'WhiteNoise':
            return self['WhiteNoise'].SpectralDensity(EndFrequency, FrequencyPoints)*math.sqrt(lanes)
        if noiseType == 'SpectralDensityFile':
            return self['SpectralDensityFile'].SpectralDensity(EndFrequency, FrequencyPoints)*math.sqrt(lanes)
        if noiseType == 'WaveformFile':
            return self['WaveformFile'].SpectralDensity(EndFrequency, FrequencyPoints)*math.sqrt(lanes)
        if noiseType == 'Johnson':
            return self['Johnson'].SpectralDensity(EndFrequency, FrequencyPoints)*math.sqrt(lanes)
        if noiseType == 'Crosstalk':
            return self['Crosstalk'].SpectralDensity(
                EndFrequency,
                FrequencyPoints,
                output_waveforms=output_waveforms,
                output_waveform_names=output_waveform_names)*math.sqrt(lanes)
        raise ValueError(f'Unknown noise type: {noiseType}')
