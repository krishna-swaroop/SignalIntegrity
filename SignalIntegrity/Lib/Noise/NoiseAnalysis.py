"""
NoiseAnalysis.py
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

class NoiseAnalysis(dict):
    def __init__(self, output_names, output_waveforms, input_names, transfer_matrices, input_noise_spectral_density):
        dict.__init__(self)

        if len(input_names) == 0:
            return

        self['output_names'] = output_names
        self['input_names'] = input_names
        self['transfer_matrices'] = transfer_matrices
        self['input_noise_spectral_density_list'] = input_noise_spectral_density
        self['input_noise_spectral_density'] = {key: {'spectrum': sd, 'dBm': sd.TotaldBm(), 'Vrms': sd.TotalRMS() } for key, sd in zip(input_names, input_noise_spectral_density)}

        from SignalIntegrity.Lib.Noise.NoiseTransferMatricesProcessor import NoiseTransferMatricesProcessor

        noiseTransferMatricesProcessor = NoiseTransferMatricesProcessor(transfer_matrices)
        outputNoiseSpectralDensityList = noiseTransferMatricesProcessor.ProcessNoise(input_noise_spectral_density)

        self['output_noise_spectral_density_list'] = outputNoiseSpectralDensityList
        self['output_noise_spectral_density'] = {key: {'spectrum': sd, 'dBm': sd.TotaldBm(), 'Vrms': sd.TotalRMS() } for key, sd in zip(output_names, outputNoiseSpectralDensityList)}


        self['signal_noise_spectral_density_list'] = [signal.SpectralDensity() for signal in output_waveforms]
        self['signal_noise_spectral_density'] = {key: {'spectrum': sd, 'dBm': sd.TotaldBm(), 'Vrms': sd.TotalRMS() } for key,sd in zip(output_names,self['signal_noise_spectral_density_list'])}

        self['signal_to_noise_ratio'] = {key: {'SNR': self['output_noise_spectral_density'][key]['spectrum'].SNRdB(self['signal_noise_spectral_density'][key]['spectrum'],other_is_signal_or_noise='signal'),
                                               'SalzSNR': self['output_noise_spectral_density'][key]['spectrum'].SalzSNRdB(self['signal_noise_spectral_density'][key]['spectrum'],other_is_signal_or_noise='signal')
                                               } for key in output_names}
        
        endFrequencyList = [sd.Frequencies('GHz')[-1] for sd in outputNoiseSpectralDensityList]
        for key,fe in zip(self['output_noise_spectral_density'].keys(),endFrequencyList):
            sdv = self['output_noise_spectral_density'][key]
            sdv['Vrms/sqrt(Hz)'] = sdv['Vrms']/math.sqrt(fe*1e9)
            sdv['Vrms/sqrt(GHz)'] = sdv['Vrms']/math.sqrt(fe)
            sdv['dBm/Hz'] = sdv['dBm'] - 10.*math.log10(fe*1e9)
            sdv['dBm/GHz'] = sdv['dBm'] - 10.*math.log10(fe)

        contributions = noiseTransferMatricesProcessor.Contributions
        self['contributions'] = {key: {input_names[i]:
                                       {'spectrum': contributions[o][i],
                                        'dBm': contributions[o][i].TotaldBm(),
                                        'Vrms': contributions[o][i].TotalRMS()
                                        } for i in range(len(input_names))} for o, key in enumerate(output_names)}

        for o in self['contributions'].keys():
            for i in self['contributions'][o].keys():
                self['contributions'][o][i]['SNR'] = self['signal_noise_spectral_density'][o]['dBm'] - self['contributions'][o][i]['dBm']
                self['contributions'][o][i]['SalzSNR'] = self['contributions'][o][i]['spectrum'].SalzSNRdB(self['signal_noise_spectral_density'][o]['spectrum'],other_is_signal_or_noise='signal')
        pass