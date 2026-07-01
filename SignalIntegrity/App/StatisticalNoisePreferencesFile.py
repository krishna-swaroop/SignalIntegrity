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

class WhiteNoiseConfiguration(XMLConfiguration):
    def __init__(self):
        super().__init__('WhiteNoise')
        self.Add(XMLPropertyDefaultString('SpecificationType','V/sqrt(Hz)')) # 'dBm/Hz', 'V/sqrt(Hz)', or 'Vrms'
        self.Add(XMLPropertyDefaultFloat('NoisedBmPerHz',0.0))
        self.Add(XMLPropertyDefaultFloat('VPerRootHz',0.0))
        self.Add(XMLPropertyDefaultFloat('VRms',0.0))
        self.Add(XMLPropertyDefaultFloat('NoiseBandwidth',0.0))
    def NoiseDensity(self):
        from SignalIntegrity.Lib.FrequencyDomain.DFTUtilities import DFTUtilities
        spec_type = self['SpecificationType']
        if spec_type == 'dBm/Hz':
            value = self['NoisedBmPerHz']
        elif spec_type == 'V/sqrt(Hz)':
            value = self['VPerRootHz']
        elif spec_type == 'Vrms':
            value = self['VRms']
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

class NoiseConfiguration(XMLConfiguration):
    def __init__(self):
        super().__init__('Noise')
        self.Add(XMLPropertyDefaultBool('Enable',False))
        self.Add(XMLPropertyDefaultString('Type','WhiteNoise')) # 'WhiteNoise', 'SpectralDensityFile', or 'WaveformFile'
        self.SubDir(WhiteNoiseConfiguration())
        self.SubDir(SpectralDensityFileConfiguration())
        self.SubDir(NoiseWaveformFileConfiguration())
    def SpectralDensity(self, EndFrequency, FrequencyPoints):
        from SignalIntegrity.Lib.FrequencyDomain.SpectralDensity import SpectralDensity
        from SignalIntegrity.Lib.FrequencyDomain.FrequencyList import EvenlySpacedFrequencyList
        fl = EvenlySpacedFrequencyList(EndFrequency, FrequencyPoints)
        if not self['Enable']:
            return SpectralDensity(fl, [0.0 for _ in fl])
        noiseType = self['Type']
        if noiseType == 'WhiteNoise':
            return self['WhiteNoise'].SpectralDensity(EndFrequency, FrequencyPoints)
        if noiseType == 'SpectralDensityFile':
            return self['SpectralDensityFile'].SpectralDensity(EndFrequency, FrequencyPoints)
        if noiseType == 'WaveformFile':
            return self['WaveformFile'].SpectralDensity(EndFrequency, FrequencyPoints)
        raise ValueError(f'Unknown noise type: {noiseType}')
