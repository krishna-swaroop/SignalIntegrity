"""
StatisticalNoisePropertiesDialog.py
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

import tkinter as tk
import os

from SignalIntegrity.App.CalculationPropertiesProject import PropertiesDialog,CalculationPropertyTrueFalseButton,CalculationPropertyChoices,CalculationPropertySI,CalculationProperty,CalculationPropertyFileName
import SignalIntegrity.App.Project
from SignalIntegrity.App.Files import FileParts

class StatisticalNoisePropertiesDialog(PropertiesDialog):
    NoiseTypeChoices=[('White Noise','WhiteNoise'),('Spectral Density File','SpectralDensityFile'),('Waveform File','WaveformFile')]
    SpecificationTypeChoices=[('dBm/Hz','dBm/Hz'),('V/sqrt(Hz)','V/sqrt(Hz)'),('Vrms','Vrms')]
    def __init__(self,project,parent):
        PropertiesDialog.__init__(self,parent,project,parent.parent,'Statistical Noise Properties')
        self.transient(parent)
        fp=FileParts(os.getcwd())
        self.GeneralFrame=tk.Frame(self.propertyListFrame, relief=tk.RIDGE, borderwidth=5)
        self.GeneralFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
        self.WhiteNoiseFrame=tk.Frame(self.propertyListFrame, relief=tk.RIDGE, borderwidth=5)
        self.WhiteNoiseFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
        self.SpectralDensityFileFrame=tk.Frame(self.propertyListFrame, relief=tk.RIDGE, borderwidth=5)
        self.SpectralDensityFileFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
        self.WaveformFileFrame=tk.Frame(self.propertyListFrame, relief=tk.RIDGE, borderwidth=5)
        self.WaveformFileFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
        self.Enable=CalculationPropertyTrueFalseButton(self.GeneralFrame,'Enable Noise',self.onUpdateFromChanges,None,self.project,'Enable',tooltip='Enable noise generation for this device')
        self.NoiseType=CalculationPropertyChoices(self.GeneralFrame,'Noise Type',self.onUpdateFromChanges,None,self.NoiseTypeChoices,self.project,'Type',tooltip='The source/method used to generate the noise')
        self.SpecificationType=CalculationPropertyChoices(self.WhiteNoiseFrame,'Specification Type',self.onUpdateFromChanges,None,self.SpecificationTypeChoices,self.project,'WhiteNoise.SpecificationType',tooltip='Units in which the white noise level is specified')
        self.NoisedBmPerHz=CalculationPropertySI(self.WhiteNoiseFrame,'Noise (dBm/Hz)',self.onNoisedBmPerHzChanged,None,self.project,'WhiteNoise.NoisedBmPerHz','dBm/Hz',round=3)
        self.VPerRootHz=CalculationPropertySI(self.WhiteNoiseFrame,'Noise (V/sqrt(Hz))',self.onVPerRootHzChanged,None,self.project,'WhiteNoise.VPerRootHz','V/sqrt(Hz)',round=3)
        self.VRms=CalculationPropertySI(self.WhiteNoiseFrame,'Noise (Vrms)',self.onVRmsChanged,None,self.project,'WhiteNoise.VRms','Vrms',round=3)
        self.NoiseBandwidth=CalculationPropertySI(self.WhiteNoiseFrame,'Noise Bandwidth',self.onNoiseBandwidthChanged,None,self.project,'WhiteNoise.NoiseBandwidth','Hz')
        self.SpectralDensityFileName=CalculationPropertyFileName(self.SpectralDensityFileFrame,'Spectral Density File',self.onUpdateFromChanges,None,fp,self.project,'SpectralDensityFile.FileName',tooltip='Path to the spectral density file describing the noise')
        self.WaveformFileName=CalculationPropertyFileName(self.WaveformFileFrame,'Waveform File',self.onUpdateFromChanges,None,fp,self.project,'WaveformFile.FileName',tooltip='Path to the waveform file describing the noise')
        self.SaveToPreferencesFrame=tk.Frame(self.propertyListFrame,relief=tk.RIDGE, borderwidth=5)
        self.SaveToPreferencesFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
        self.SaveToPreferencesButton = tk.Button(self.SaveToPreferencesFrame,text='Save Properties to Global Preferences',command=self.onSaveToPreferences,width=CalculationProperty.labelWidth)
        self.SaveToPreferencesButton.pack(side=tk.TOP,expand=tk.YES)
        self.Finish()
    def Finish(self):
        self.UpdateStrings()
        PropertiesDialog.Finish(self)
    def onUpdateFromChanges(self,_):
        self.UpdateStrings()
    def UpdateStrings(self):
        enable=self.project['Enable']
        noiseType=self.project['Type']
        specType=self.project['WhiteNoise.SpecificationType']
        self.WhiteNoiseFrame.pack_forget()
        self.SpectralDensityFileFrame.pack_forget()
        self.WaveformFileFrame.pack_forget()
        self.SaveToPreferencesFrame.pack_forget()
        self.NoiseType.Show(enable)
        if enable:
            if noiseType=='WhiteNoise':
                self.WhiteNoiseFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
            elif noiseType=='SpectralDensityFile':
                self.SpectralDensityFileFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
            elif noiseType=='WaveformFile':
                self.WaveformFileFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
        self.SaveToPreferencesFrame.pack(side=tk.TOP,fill=tk.X,expand=tk.NO)
        self.SpecificationType.Show(True)
        self.NoisedBmPerHz.Show(specType=='dBm/Hz')
        self.VPerRootHz.Show(specType=='V/sqrt(Hz)')
        self.VRms.Show(specType=='Vrms')
        self.NoiseBandwidth.Show(specType in ['dBm/Hz','V/sqrt(Hz)','Vrms'])
    def onSaveToPreferences(self):
        self.parent.device.configuration.SaveToPreferences()
    def _propagateFrom(self, source_units):
        """Recompute the two non-source noise-level fields from the source field
        using DFTUtilities.ConvertSpectralDensity. Conversions involving 'Vrms'
        are skipped if NoiseBandwidth is not a positive number."""
        from SignalIntegrity.Lib.FrequencyDomain.DFTUtilities import DFTUtilities
        fields = {
            'dBm/Hz':     ('WhiteNoise.NoisedBmPerHz', self.NoisedBmPerHz),
            'V/sqrt(Hz)': ('WhiteNoise.VPerRootHz',    self.VPerRootHz),
            'Vrms':       ('WhiteNoise.VRms',          self.VRms),
        }
        src_key, _ = fields[source_units]
        value = self.project[src_key]
        bw = self.project['WhiteNoise.NoiseBandwidth']
        for to_units, (key, widget) in fields.items():
            if to_units == source_units:
                continue
            needs_bw = (source_units == 'Vrms' or to_units == 'Vrms')
            if needs_bw and (bw is None or bw <= 0):
                continue  # cannot convert without a valid bandwidth
            try:
                converted = DFTUtilities.ConvertSpectralDensity(
                    value, source_units, to_units, bw=bw)
            except (ValueError, ZeroDivisionError):
                continue  # leave stale value rather than crash the UI
            self.project[key] = converted
            widget.UpdateStrings()

    def onNoisedBmPerHzChanged(self, _):
        self._propagateFrom('dBm/Hz')
        self.UpdateStrings()

    def onVPerRootHzChanged(self, _):
        self._propagateFrom('V/sqrt(Hz)')
        self.UpdateStrings()

    def onVRmsChanged(self, _):
        self._propagateFrom('Vrms')
        self.UpdateStrings()

    def onNoiseBandwidthChanged(self, _):
        # Treat NoiseBandwidth as an input; rebuild the other two level fields
        # from whichever level is currently selected as the specification.
        spec_type = self.project['WhiteNoise.SpecificationType']
        if spec_type in ('dBm/Hz', 'V/sqrt(Hz)', 'Vrms'):
            self._propagateFrom(spec_type)
        self.UpdateStrings()
