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


class NoiseAnalysis(dict):
    def __init__(self, output_names, input_names, transfer_matrices, input_noise_spectral_density):
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
        contributions = noiseTransferMatricesProcessor.Contributions
        self['contributions'] = {key: {input_names[i]: {'spectrum': contributions[o][i], 'dBm': contributions[o][i].TotaldBm(), 'Vrms': contributions[o][i].TotalRMS() } for i in range(len(input_names))} for o, key in enumerate(output_names)}
