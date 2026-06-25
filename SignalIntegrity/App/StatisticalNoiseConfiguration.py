"""
StatisticalNoiseConfiguration.py
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
from SignalIntegrity.App.StatisticalNoisePreferencesFile import NoiseConfiguration
from SignalIntegrity.App.DeviceExtendedConfiguration import DeviceExtendedConfiguration
import SignalIntegrity.App.Preferences
import copy

class StatisticalNoiseConfiguration(NoiseConfiguration,DeviceExtendedConfiguration):
    def __init__(self):
        if DeviceExtendedConfiguration.headless:
            dialog=None
        else:
            from SignalIntegrity.App.StatisticalNoisePropertiesDialog import StatisticalNoisePropertiesDialog
            dialog=StatisticalNoisePropertiesDialog
        NoiseConfiguration.__init__(self)
        DeviceExtendedConfiguration.__init__(self,
            label='Statistical Noise Configuration',
            dialog=dialog
            )
    def HandleBackwardsCompatibility(self):
        # for backwards compatibility with old projects with noise sources with global noise configurations,
        # assign the global configuration to the device.  When the file is written, these individual configurations
        # will be retained and the global configuration will be removed.
        import SignalIntegrity.App.Project
        if not SignalIntegrity.App.Project['Noise'] is None:
            self.dict = copy.deepcopy(SignalIntegrity.App.Project['Noise'].dict)
