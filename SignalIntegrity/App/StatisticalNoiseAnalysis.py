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
    def __init__(self, schematic,
                 transferMatrices,
                 output_waveforms,
                 output_waveform_names):

        dict.__init__(self)

        try:
            netlist = schematic.NetList()

            if netlist is None:
                return

            if netlist.NoiseSourceNames() is None or len(netlist.NoiseSourceNames()) == 0:
                return

            outputWaveformLabels,sourceNames,transferMatrices = transferMatrices.Keep(
                netlist.OutputNames(),         # outputs
                netlist.SourceNames(),         # sources
                netlist.OutputNames(),         # outputs to keep
                netlist.NoiseSourceNames()     # sources to keep
                )

            from SignalIntegrity.Lib.FrequencyDomain.FrequencyList import EvenlySpacedFrequencyList
            fl = EvenlySpacedFrequencyList(transferMatrices.f[-1], len(transferMatrices.f)-1)

            # determine the 'type' (voltage or current) of each output probe.
            # A CurrentOutput probe measures current, so its noise/signal is
            # reported in current units; every other probe reports voltage.
            output_types = {}
            for output_name in outputWaveformLabels:
                output_types[output_name] = 'voltage'
                for device in schematic.deviceList:
                    if device['ref'] is None:
                        continue
                    if device['ref'].GetValue() == output_name:
                        if device['partname'].GetValue() == 'CurrentOutput':
                            output_types[output_name] = 'current'
                        break

            input_types = {}
            inputNoiseSpectralDensityList = []
            for noise_source_ref in netlist.NoiseSourceNames():
                sd = None
                for device in schematic.deviceList:
                    if device['partname'].GetValue() in ['VoltageStatisticalNoiseSource','VoltageStatisticalNoiseSourceProject','CurrentStatisticalNoiseSource','CurrentStatisticalNoiseSourceProject']:
                        if device['ref'].GetValue() == noise_source_ref:
                            input_types[noise_source_ref] = 'current' if device['partname'].GetValue().startswith('Current') else 'voltage'
                            sd = device.SpectralDensity(
                                output_waveforms=output_waveforms,
                                output_waveform_names=output_waveform_names).Resample(fl)
                            inputNoiseSpectralDensityList.append(sd)
                            break

            from SignalIntegrity.Lib.Noise.NoiseAnalysis import NoiseAnalysis

            dict.__init__(self,
                          NoiseAnalysis(
                              output_names = outputWaveformLabels,
                              output_waveforms = output_waveforms,
                              input_names = sourceNames,
                              transfer_matrices = transferMatrices,
                              input_noise_spectral_density = inputNoiseSpectralDensityList,
                              output_types = output_types,
                              input_types = input_types
                              )
                          )
        except Exception as e:
            raise Exception("Error in StatisticalNoiseAnalysis: "+str(e))

    def Noise(self,reference):
        try:
            return self['output_noise_spectral_density'][reference]['rms']
        except Exception as e:
            return 0.0