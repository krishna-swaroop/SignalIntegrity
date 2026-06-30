"""
StatisticalNoiseAnalysis.py
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

class StatisticalNoiseAnalysis(dict):
    def __init__(self, schematic, transferMatrices):

        netlist = schematic.NetList()

        outputWaveformLabels,sourceNames,transferMatrices = transferMatrices.Keep(
            netlist.OutputNames(),         # outputs
            netlist.SourceNames(),         # sources
            netlist.OutputNames(),         # outputs to keep
            netlist.NoiseSourceNames()     # sources to keep
            )

        inputNoiseSpectralDensityList = []
        for noise_source_ref in netlist.NoiseSourceNames():
            sd = None
            for device in schematic.deviceList:
                if device['partname'].GetValue() in ['VoltageStatisticaLNoiseSource']:
                    if device['ref'].GetValue() == noise_source_ref:
                        sd = device.SpectralDensity()
                        inputNoiseSpectralDensityList.append(sd)
                        break

        from SignalIntegrity.Lib.Noise.NoiseAnalysis import NoiseAnalysis

        dict.__init__(self,
                      NoiseAnalysis(
                          output_names = outputWaveformLabels,
                          input_names = sourceNames,
                          transfer_matrices = transferMatrices,
                          input_noise_spectral_density = inputNoiseSpectralDensityList
                          )
                      )
