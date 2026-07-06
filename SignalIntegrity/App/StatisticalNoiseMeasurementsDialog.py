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

        self.tableFrame = tk.Frame(self, relief=tk.RIDGE, borderwidth=5)
        self.tableFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)

        self.treeStyle = ttk.Style(self)
        self.headerFont = tkfont.nametofont('TkHeadingFont').copy()
        self.headerFont.configure(weight='bold')
        self.treeStyle.configure('StatisticalNoise.Treeview.Heading', font=self.headerFont)

        self.measurementTree = ttk.Treeview(self.tableFrame, show='headings', style='StatisticalNoise.Treeview')
        self.measurementTree.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)

        self.yScroll = ttk.Scrollbar(self.tableFrame, orient=tk.VERTICAL, command=self.measurementTree.yview)
        self.yScroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.measurementTree.configure(yscrollcommand=self.yScroll.set)

        self.xScroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.measurementTree.xview)
        self.xScroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.measurementTree.configure(xscrollcommand=self.xScroll.set)

        self.groupFont = tkfont.nametofont('TkDefaultFont').copy()
        self.groupFont.configure(weight='bold')
        self.measurementTree.tag_configure('group', background='#e8e8e8', font=self.groupFont)

        self._hasAutoSized = False
        self.resizable(True, True)
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

    def _contributorValue(self, measurements, output_name, contributor_name):
        contributions = measurements.get('contributions', {})
        output_contrib = contributions.get(output_name, {})
        contributor = output_contrib.get(contributor_name, {})
        vrms = self._formatValue(contributor.get('Vrms', None), 'Vrms')
        dbm = self._formatValue(contributor.get('dBm', None), 'dBm')

        signal_dbm = self._dictValue(measurements, output_name, 'signal_noise_spectral_density', 'dBm')
        contributor_dbm = contributor.get('dBm', None)
        snr_db = None if signal_dbm is None or contributor_dbm is None else signal_dbm - contributor_dbm
        snr = self._formatValue(snr_db, 'dB')

        return f'{vrms}, {dbm}, {snr}'

    def _contributorNames(self, measurements):
        input_names = measurements.get('input_names', [])
        if len(input_names) > 0:
            return list(input_names)
        contributions = measurements.get('contributions', {})
        ordered = []
        for output_name in measurements.get('output_names', []):
            for contributor_name, contributor_value in contributions.get(output_name, {}).items():
                if not isinstance(contributor_value, dict):
                    continue
                if contributor_name not in ordered:
                    ordered.append(contributor_name)
        return ordered

    def _insertGroupRow(self, title, column_count):
        values = [title] + ['' for _ in range(column_count - 1)]
        self.measurementTree.insert('', tk.END, values=values, tags=('group',))

    def _insertMeasurementRow(self, label, output_names, extractor, units):
        row = [label]
        for output_name in output_names:
            row.append(self._formatValue(extractor(output_name), units))
        self.measurementTree.insert('', tk.END, values=row)

    def _autoSizeOutputColumns(self, output_names, min_width=170, max_width=700, pad=24):
        cell_font = tkfont.nametofont('TkDefaultFont')
        for output_index, output_name in enumerate(output_names, start=1):
            max_pixels = self.headerFont.measure(str(output_name))
            for item in self.measurementTree.get_children(''):
                values = self.measurementTree.item(item, 'values')
                if output_index < len(values):
                    max_pixels = max(max_pixels, cell_font.measure(str(values[output_index])))
            width = max(min_width, min(max_width, max_pixels + pad))
            self.measurementTree.column(output_name, width=width, anchor='center', stretch=tk.NO)

    def _autoSizeWindowToTable(self):
        self.update_idletasks()

        columns = self.measurementTree['columns']
        table_width = sum(int(self.measurementTree.column(column_name, 'width')) for column_name in columns)
        table_width += self.yScroll.winfo_reqwidth()
        table_width += int(2 * self.tableFrame.cget('borderwidth'))

        row_count = len(self.measurementTree.get_children(''))
        try:
            row_height = int(self.treeStyle.lookup('Treeview', 'rowheight'))
        except (TypeError, ValueError):
            row_height = 0
        if row_height <= 0:
            row_height = tkfont.nametofont('TkDefaultFont').metrics('linespace') + 6
        heading_height = self.headerFont.metrics('linespace') + 10
        table_height = heading_height + row_count * row_height
        table_height += int(2 * self.tableFrame.cget('borderwidth'))

        window_width = table_width
        window_height = table_height + self.statusbar.winfo_reqheight() + self.xScroll.winfo_reqheight()

        self.geometry(f'{window_width}x{window_height}')

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

        contributor_names = self._contributorNames(measurements)
        if len(contributor_names) > 0:
            self._insertGroupRow('Noise Contributors (Vrms, dBm, SNR)', column_count)
            for contributor_name in contributor_names:
                row = [contributor_name]
                for output_name in output_names:
                    row.append(self._contributorValue(measurements, output_name, contributor_name))
                self.measurementTree.insert('', tk.END, values=row)

        self._autoSizeOutputColumns(output_names)

        if not self._hasAutoSized:
            self._autoSizeWindowToTable()
            self._hasAutoSized = True

        has_signal = 'signal_noise_spectral_density' in measurements
        signal_note = 'with signal-power metrics' if has_signal else 'signal-power metrics unavailable'
        contributor_note = f', {len(contributor_names)} contributor(s)' if len(contributor_names) > 0 else ''
        self.statusbar.set(f'Showing noise measurements for {len(output_names)} output probe(s), {signal_note}{contributor_note}')

        self.deiconify()
        self.lift()
