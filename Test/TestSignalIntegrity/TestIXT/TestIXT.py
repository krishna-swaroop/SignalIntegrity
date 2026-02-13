"""
TestIXT.py
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
import unittest
import math

import SignalIntegrity.Lib as si
import SignalIntegrity.App.SignalIntegrityAppHeadless as siapp
import numpy as np
import os

from SignalIntegrity.Lib.ToSI import ToSI,FromSI

class TestIXTTest(unittest.TestCase,
        si.test.SParameterCompareHelper,si.test.SignalIntegrityAppTestHelper):
    relearn=True
    plot=False
    debug=False
    checkPictures=True
    epsilon=50e-12
    def setUp(self):
        unittest.TestCase.setUp(self)
        si.test.SignalIntegrityAppTestHelper.__init__(self,os.path.dirname(os.path.realpath(__file__)))
        self.cwd=os.getcwd()
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        #si.test.SignalIntegrityAppTestHelper.forceWritePictures=True
        from SignalIntegrity.App.SignalIntegrityAppHeadless import SignalIntegrityAppHeadless
        import SignalIntegrity.App.Project
        pysi=SignalIntegrityAppHeadless()
        self.UseSinX=SignalIntegrity.App.Preferences['Calculation.UseSinX']
        SignalIntegrity.App.Preferences['Calculation.UseSinX']=True
        self.TextLimit=SignalIntegrity.App.Preferences['Appearance.LimitText']
        SignalIntegrity.App.Preferences['Appearance.LimitText']=60
        self.RoundDisplayedValues=SignalIntegrity.App.Preferences['Appearance.RoundDisplayedValues']
        SignalIntegrity.App.Preferences['Appearance.RoundDisplayedValues']=4
        SignalIntegrity.App.Preferences.SaveToFile()
        pysi=SignalIntegrityAppHeadless()
        SignalIntegrity.App.Preferences['Calculation'].ApplyPreferences()
        import platform
        thisOS=platform.system()
        if thisOS == 'Linux':
            self.python = 'python3'
        else:
            self.python = 'python.exe'
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        os.chdir(self.cwd)
        from SignalIntegrity.App.SignalIntegrityAppHeadless import SignalIntegrityAppHeadless
        import SignalIntegrity.App.Project
        pysi=SignalIntegrityAppHeadless()
        SignalIntegrity.App.Preferences['Calculation.UseSinX']=self.UseSinX
        SignalIntegrity.App.Preferences['Appearance.LimitText']=self.TextLimit
        SignalIntegrity.App.Preferences['Appearance.RoundDisplayedValues']=self.RoundDisplayedValues
        SignalIntegrity.App.Preferences.SaveToFile()
        pysi=SignalIntegrityAppHeadless()
        SignalIntegrity.App.Preferences['Calculation'].ApplyPreferences()
    def __init__(self, methodName='runTest'):
        si.test.SParameterCompareHelper.__init__(self)
        unittest.TestCase.__init__(self,methodName)
        si.test.SignalIntegrityAppTestHelper.__init__(self,os.path.dirname(os.path.realpath(__file__)))

    @staticmethod
    def IXT_args():
        return {'port_reorder':'1,2,3,4,16,15,14,13','single_ended_ports':'1,2,5,6,3,4,7,8',
                'reference_impedance':'46.25,50','voltage_transfer_function':'True','victim_ports':'1,2','aggressor_ports':'3,2',
                'end_frequency':'55e9','frequency_points':'40','multiply':'8'}

    def testIXTSubprocess(self):
        import subprocess
        script_file = os.path.abspath(os.path.relpath('../../../SignalIntegrity/Utilities/IXT/IXT.py', os.path.dirname(__file__)))
        file_name='nitro_9-13-24b-tx1_4_HFSS-sig1p0_res.s16p'
        file_name=os.path.join(os.path.dirname(__file__),file_name)
        cmd_str=self.python+' -u '+script_file+' '+file_name
        ixt_args=self.IXT_args()
        for key in ixt_args:
            cmd_str += ' --'+key+' '+str(ixt_args[key])
        result = subprocess.getoutput(cmd_str)
        result_dB = ToSI(float(result),'dB',round=5)
        # print('result: ',result_dB)
        target = '-50.249 dB'
        self.assertEqual(result_dB, target, 'IXT produced incorrect value')
    def testIXTSubprocessMissingSp(self):
        import subprocess
        script_file = os.path.abspath(os.path.relpath('../../../SignalIntegrity/Utilities/IXT/IXT.py', os.path.dirname(__file__)))
        file_name='missing.s4p'
        file_name=os.path.join(os.path.dirname(__file__),file_name)
        cmd_str=self.python+' -u '+script_file+' '+file_name
        ixt_args=self.IXT_args()
        for key in ixt_args:
            cmd_str += ' --'+key+' '+ixt_args[key]
        result = subprocess.getoutput(cmd_str)
        self.assertTrue(result=='error','result should be error')
    def formIXTMain_argv(self,missing=[],replace={}):
        import sys
        script_file = os.path.abspath(os.path.relpath('../../../SignalIntegrity/Utilities/IXT/IXT.py', os.path.dirname(__file__)))
        file_name='nitro_9-13-24b-tx1_4_HFSS-sig1p0_res.s16p'
        file_name=os.path.join(os.path.dirname(__file__),file_name)
        ixt_args=self.IXT_args()
        sys.argv=[script_file,file_name]
        for key in ixt_args:
            value=ixt_args[key]
            if key in replace:
                value=replace[key]
            if key not in missing:
                sys.argv.append('--'+key)
                sys.argv.append(value)
            # sys.argv.append('-d')
    def testIXTMain(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv()
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,0,'IXT_Main did not exit properly') # exited correctly
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def testIXTMainNoFile(self):
        import sys
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv()
        sys.argv[1]='none.s4p'
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    # @unittest.skip('skip for now')
    # def testIXTMainNoArgs(self):
    #     import sys
    #     from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
    #     self.formIXTMain_argv()
    #     sys.argv=[sys.argv[0]]
    #     try:
    #         IXT_Main()
    #     except SystemExit as e:
    #         self.assertEqual(e.code,1,'IXT_Main did not exit properly') # failed
    #         return
    #     self.fail('IXT should have exited with SystemExit exception raised')
    def testIXTMainUnknownKeyword(self):
        import sys
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv()
        sys.argv=[sys.argv[0],'-unknown']
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # failed
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def testIXTMainBadPortReorder(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['port_reorder'])
        import sys
        sys.argv.append('--port_reorder')
        sys.argv.append(self.IXT_args()['port_reorder']+',100')
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def testIXTMainUnevenSingleEndedPorts(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['single_ended_ports'])
        import sys
        sys.argv.append('--single_ended_ports')
        sys.argv.append(self.IXT_args()['single_ended_ports']+',100')
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def testIXTMainBadSingleEndedPorts(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['single_ended_ports'])
        import sys
        sys.argv.append('--single_ended_ports')
        sys.argv.append(self.IXT_args()['single_ended_ports']+',100,200')
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainMissingTr(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['T_r'])
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainTrUI(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'T_r':'1.0625UI'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,0,'IXT_Main did not exit properly') # should succeed
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainBadTr(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'T_r':'10Hz'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should succeed
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainMissingBetaX(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['beta_x'])
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainBadBetaX(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'beta_x':'50lbs'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainMissingRhoX(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['rho_x'])
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainBadRhoX(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'rho_x':'1UI'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def testIXTMainMissingN(self):
        import sys
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['frequency_points'])
        sys.argv.append('-v')
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def testIXTMainBadN(self):
        import sys
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'frequency_points':'50kHz'})
        #sys.argv.append('-v')
        #sys.argv.append('-p')
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,2,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainMissingNBx(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['N_bx'])
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainBadNBx(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'N_bx':'20GBaud'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainMissingZ0(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['Z0'])
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,0,'IXT_Main did not exit properly') # should succeed
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainBadZ0(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'Z0':'20ps'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainMissingTFx(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['T_fx'])
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,0,'IXT_Main did not exit properly') # should succeed
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainBadTFx(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'T_fx':'30kcycle'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainMissingFb(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['f_b'])
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainBadFb(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'f_b':'200kbps'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainMissingDER0(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(['DER_0'])
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTMainBadDER0(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT_Main
        self.formIXTMain_argv(replace={'DER_0':'50UI'})
        try:
            IXT_Main()
        except SystemExit as e:
            self.assertEqual(e.code,1,'IXT_Main did not exit properly') # should fail
            return
        self.fail('IXT should have exited with SystemExit exception raised')
    def atestIXTPythonScript(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT
        file_name='sparam_res.s4p'
        file_name=os.path.join(os.path.dirname(__file__),file_name)
        ixt_args=self.IXT_args()
        ixt_args['T_r'] = FromSI(ixt_args['T_r'],'s')
        ixt_args['beta_x'] = FromSI(ixt_args['beta_x'],'Hz')
        ixt_args['rho_x'] = FromSI(ixt_args['rho_x'],None)
        ixt_args['N'] = FromSI(ixt_args['N'],'UI')
        ixt_args['N_bx'] = FromSI(ixt_args['N_bx'],'UI')
        ixt_args['Z0'] = FromSI(ixt_args['Z0'],'ohm')
        ixt_args['T_fx'] = FromSI(ixt_args['T_fx'],'s')
        ixt_args['f_b'] = FromSI(ixt_args['f_b'],'Baud')
        ixt_args['DER_0'] = FromSI(ixt_args['DER_0'],None)
        ixt_args['phi'] = FromSI(ixt_args['phi'],None)
        result = IXT(file_name,ixt_args,verbose=True)
        result_dB = ToSI(float(result),'dB',round=5)
        # print('result: ',result_dB)
        target = '9.3858 dB'
        self.assertEqual(result_dB, target, 'IXT produced incorrect value')
    def atestIXTPythonScriptMissingSp(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT
        file_name='missing.s4p'
        file_name=os.path.join(os.path.dirname(__file__),file_name)
        ixt_args=self.IXT_args()
        ixt_args['T_r'] = FromSI(ixt_args['T_r'],'s')
        ixt_args['beta_x'] = FromSI(ixt_args['beta_x'],'Hz')
        ixt_args['rho_x'] = FromSI(ixt_args['rho_x'],None)
        ixt_args['N'] = FromSI(ixt_args['N'],'UI')
        ixt_args['N_bx'] = FromSI(ixt_args['N_bx'],'UI')
        ixt_args['Z0'] = FromSI(ixt_args['Z0'],'ohm')
        ixt_args['T_fx'] = FromSI(ixt_args['T_fx'],'s')
        ixt_args['f_b'] = FromSI(ixt_args['f_b'],'Baud')
        ixt_args['DER_0'] = FromSI(ixt_args['DER_0'],None)
        ixt_args['phi'] = FromSI(ixt_args['phi'],None)
        with self.assertRaises(si.SignalIntegrityException) as cme:
            IXT(file_name,ixt_args,verbose=True)
    def atestIXTPythonScriptMissingKeyword(self):
        from SignalIntegrity.Utilities.IXT.IXT import IXT
        file_name='sparam_res.s4p'
        file_name=os.path.join(os.path.dirname(__file__),file_name)
        ixt_args=self.IXT_args()
        ixt_args['T_r'] = FromSI(ixt_args['T_r'],'s')
        ixt_args['beta_x'] = FromSI(ixt_args['beta_x'],'Hz')
        ixt_args['rho_x'] = FromSI(ixt_args['rho_x'],None)
        ixt_args['N'] = FromSI(ixt_args['N'],'UI')
        ixt_args['N_bx'] = FromSI(ixt_args['N_bx'],'UI')
        ixt_args['Z0'] = FromSI(ixt_args['Z0'],'ohm')
        ixt_args['T_fx'] = FromSI(ixt_args['T_fx'],'s')
        ixt_args['f_b'] = FromSI(ixt_args['f_b'],'Baud')
        ixt_args['DER_0'] = FromSI(ixt_args['DER_0'],None)
        ixt_args['phi'] = FromSI(ixt_args['phi'],None)
        del ixt_args['T_r']
        with self.assertRaises(si.SignalIntegrityException) as cme:
            IXT(file_name,ixt_args,verbose=True)


if __name__ == '__main__': # pragma: no cover
    unittest.main()
