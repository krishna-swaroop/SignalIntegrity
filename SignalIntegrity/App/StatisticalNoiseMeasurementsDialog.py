"""
StatisticalNoiseMeasurementsDialog.py
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
from tkinter import ttk
import tkinter.font as tkfont

from SignalIntegrity.App.MenuSystemHelpers import StatusBar
from SignalIntegrity.Lib.ToSI import ToSI
import SignalIntegrity.App.Project


class StatisticalNoiseMeasurementsDialog(tk.Toplevel):
    """Dialog that displays statistical noise measurements in a column-oriented table."""

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.withdraw()
        self.title('Statistical Noise Measurements')
        self.img = tk.PhotoImage(file=SignalIntegrity.App.IconsBaseDir + 'AppIcon2.gif')
        self.tk.call('wm', 'iconphoto', self._w, self.img)
        self.protocol('WM_DELETE_WINDOW', self.onClosing)

        self.statusbar = StatusBar(self)
        self.statusbar.pack(side=tk.TOP, fill=tk.X, expand=tk.NO)

        tableFrame = tk.Frame(self, relief=tk.RIDGE, borderwidth=5)
        tableFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)

        self.treeStyle = ttk.Style(self)
        self.headerFont = tkfont.nametofont('TkHeadingFont').copy()
        self.headerFont.configure(weight='bold')
        self.treeStyle.configure('StatisticalNoise.Treeview.Heading', font=self.headerFont)

        self.measurementTree = ttk.Treeview(tableFrame, show='headings', style='StatisticalNoise.Treeview')
        self.measurementTree.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)

        yScroll = ttk.Scrollbar(tableFrame, orient=tk.VERTICAL, command=self.measurementTree.yview)
        yScroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.measurementTree.configure(yscrollcommand=yScroll.set)

        xScroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.measurementTree.xview)
        xScroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.measurementTree.configure(xscrollcommand=xScroll.set)

        self.groupFont = tkfont.nametofont('TkDefaultFont').copy()
        self.groupFont.configure(weight='bold')
        self.measurementTree.tag_configure('group', background='#e8e8e8', font=self.groupFont)

        self.resizable(True, True)
        self.geometry('900x420')
        self.deiconify()
        self.lift()

    def onClosing(self):
        self.withdraw()
        self.destroy()

    def destroy(self):
        tk.Toplevel.withdraw(self)
        tk.Toplevel.destroy(self)

    def _clearTable(self):
        self.measurementTree['columns'] = ()
        for item in self.measurementTree.get_children():
            self.measurementTree.delete(item)

    def _formatValue(self, value, units):
        if value is None:
            return '-'
        try:
            return ToSI(value, units, round=3)
        except Exception:
            return str(value)

    def _dictValue(self, measurements, output_name, section_name, key_name):
        section = measurements.get(section_name, {})
        output_entry = section.get(output_name, {})
        return output_entry.get(key_name, None)

    def _snrDb(self, measurements, output_name):
        signal_dbm = self._dictValue(measurements, output_name, 'signal_noise_spectral_density', 'dBm')
        noise_dbm = self._dictValue(measurements, output_name, 'output_noise_spectral_density', 'dBm')
        if signal_dbm is None or noise_dbm is None:
            return None
        return signal_dbm - noise_dbm

    def _insertGroupRow(self, title, column_count):
        values = [title] + ['' for _ in range(column_count - 1)]
        self.measurementTree.insert('', tk.END, values=values, tags=('group',))

    def _insertMeasurementRow(self, label, output_names, extractor, units):
        row = [label]
        for output_name in output_names:
            row.append(self._formatValue(extractor(output_name), units))
        self.measurementTree.insert('', tk.END, values=row)

    def UpdateMeasurements(self, measurements):
        """
        Update table content.

        Expected keys in measurements include:
          - output_names
          - output_noise_spectral_density
          - signal_noise_spectral_density (optional)
        """
        self.withdraw()
        self._clearTable()

        if measurements is None:
            self.statusbar.set('No statistical noise measurements available')
            self.deiconify()
            return

        output_names = measurements.get('output_names', [])
        if len(output_names) == 0:
            self.statusbar.set('No output probes in statistical noise measurements')
            self.deiconify()
            return

        columns = ['Measurement'] + list(output_names)
        self.measurementTree['columns'] = columns

        self.measurementTree.heading('Measurement', text='Measurement')
        self.measurementTree.column('Measurement', width=260, anchor='w', stretch=tk.NO)

        for output_name in output_names:
            self.measurementTree.heading(output_name, text=output_name)
            self.measurementTree.column(output_name, width=170, anchor='center', stretch=tk.NO)

        column_count = len(columns)

        self._insertGroupRow('Signal Power', column_count)
        self._insertMeasurementRow(
            'Integrated signal power (Vrms)',
            output_names,
            lambda out: self._dictValue(measurements, out, 'signal_noise_spectral_density', 'Vrms'),
            'Vrms')
        self._insertMeasurementRow(
            'Integrated signal power (dBm)',
            output_names,
            lambda out: self._dictValue(measurements, out, 'signal_noise_spectral_density', 'dBm'),
            'dBm')

        self._insertGroupRow('Noise Power', column_count)
        self._insertMeasurementRow(
            'Total noise (Vrms)',
            output_names,
            lambda out: self._dictValue(measurements, out, 'output_noise_spectral_density', 'Vrms'),
            'Vrms')
        self._insertMeasurementRow(
            'Total noise (dBm)',
            output_names,
            lambda out: self._dictValue(measurements, out, 'output_noise_spectral_density', 'dBm'),
            'dBm')

        self._insertGroupRow('Signal-to-Noise Ratio', column_count)
        self._insertMeasurementRow(
            'SNR (dB)',
            output_names,
            lambda out: self._snrDb(measurements, out),
            'dB')

        self._insertGroupRow('Average Noise Density (Hz)', column_count)
        self._insertMeasurementRow(
            'Average noise density (V/sqrt(Hz))',
            output_names,
            lambda out: self._dictValue(measurements, out, 'output_noise_spectral_density', 'Vrms/sqrt(Hz)'),
            'Vrms/sqrt(Hz)')
        self._insertMeasurementRow(
            'Average noise density (dBm/Hz)',
            output_names,
            lambda out: self._dictValue(measurements, out, 'output_noise_spectral_density', 'dBm/Hz'),
            'dBm/Hz')

        self._insertGroupRow('Average Noise Density (GHz)', column_count)
        self._insertMeasurementRow(
            'Average noise density (V/sqrt(GHz))',
            output_names,
            lambda out: self._dictValue(measurements, out, 'output_noise_spectral_density', 'Vrms/sqrt(GHz)'),
            'Vrms/sqrt(GHz)')
        self._insertMeasurementRow(
            'Average noise density (dBm/GHz)',
            output_names,
            lambda out: self._dictValue(measurements, out, 'output_noise_spectral_density', 'dBm/GHz'),
            'dBm/GHz')

        has_signal = 'signal_noise_spectral_density' in measurements
        signal_note = 'with signal-power metrics' if has_signal else 'signal-power metrics unavailable'
        self.statusbar.set(f'Showing noise measurements for {len(output_names)} output probe(s), {signal_note}')

        self.deiconify()
        self.lift()
