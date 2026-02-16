"""
IXT.py
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
import numpy as np
import SignalIntegrity.Lib as si
import math
import os
from SignalIntegrity.Lib.ToSI import ToSI,FromSI

class IXT_Calculator(dict):
    prog='IXT'

    @staticmethod
    def ParseKeywordPairs(args_list=[]):
        import argparse
        from argparse import RawTextHelpFormatter
        parser = argparse.ArgumentParser(
                        prog='IXT',
                        description="""Integrated Crosstalk Calculator

                        Calculates integrated crosstalk

                        """,
                        epilog='',
                        formatter_class=RawTextHelpFormatter)
        parser.add_argument('filename',nargs='?',default=None, help='s-parameter file name')
        parser.add_argument('-pr','--port_reorder',type=str,default=None,help='optional comma seperated list of ports to use')
        parser.add_argument('-se','--single_ended_ports',type=str,default=None,help='optional comma seperated list of single-ended ports for conversion to mixed-mode')
        parser.add_argument('-z0','--reference_impedance',type=str,default=None,help='optional comma seperated list of reference impedances\n\
1 number means a reference impedance to apply to all ports.\n\
2 numbers means a reference impedance to apply to the first half and the second half of ports (like differential/common-mode.\n\
otherwise one number per port.')
        parser.add_argument('-vt','--voltage_transfer_function',action='store_true',help='(optional, applies to s-parameters) fit to the voltage transfer function\n\
the default is to fit s21, which is the ratio of output\n\
wave to incident wave. this is not the voltage transfer function, which is s21/(1+s11).')
        parser.add_argument('-vp','--victim_ports',type=str,help='comma seperated list of the two victim ports: input,output')
        parser.add_argument('-ap','--aggressor_ports',type=str,help='comma seperated list of aggessor ports: input1,output1,input2,output2,... etc.')
        parser.add_argument('-mult','--multiply',type=str,help='comma seperated list of numbers to multiply by each aggressor port crosstalk')
        parser.add_argument('-debug','--debug',action='store_true', help='shows debug information and plots as the computation proceeds')
        parser.add_argument('-p','--profile',action='store_true', help='profiles the software')
        parser.add_argument('-v','--verbose',action='store_true', help='prints information as calculation proceeds.\n\
this should not be set if you are relying on stdout for the return value.')
        parser.add_argument('-fe','--end_frequency',type=float,help='(optional) end frequency to resample to\n\
if this is specified, then the number of frequency points must also be specified\n\
(see --frequency_points).')
        parser.add_argument('-n','--frequency_points',type=int,help='(optional) number of frequency points to resample to\n\
if this is specified, then the end frequency must also be specified (see --end_frequency).\n\
it\'s a good idea to use as few frequency points as needed to improve speed.')
        parser.add_argument('-cli','--command_line',type=bool,default=False,help=argparse.SUPPRESS)
        args, unknown = parser.parse_known_args(args_list)
        return vars(args),unknown

    @staticmethod
    def IXT(victim,aggressors,end_frequency):
        """Integrated crosstalk (in dB)
        @param victim instance of class FrequencyDomain containing the frequency response of the victim channel.
        @param aggressors instance of class FrequencyDomain containing the frequency response of the aggressor channel.
        @param end_frequency float frequency to integrate the crosstalk to.
        @return integrated crosstalk in dB.
        @remark
        aggressors can be provided as a list of aggressor frequency responses, in which case the integrated crosstalk
        will be for the aggregate of all of the aggressor channels.
        @remark
        The frequencies and lengths of the victim and aggressors are assumed to match.
        """
        import SignalIntegrity.Lib as si
        if isinstance(aggressors,si.fd.FrequencyDomain):
            aggressors=[aggressors]
        frequencies = victim.Frequencies()
        victim_mag = victim.Values('mag')
        aggressors_mag = [aggressor.Values('mag') for aggressor in aggressors]
        ixt = 0
        num = 0
        for n in range(len(frequencies)):
            if frequencies[n] > end_frequency:
                break
            ixt += (np.sqrt(sum([aggressor_mag[n]**2 for aggressor_mag in aggressors_mag]))/victim_mag[n])**2
            num += 1
        return 10.*np.log10(ixt/num)

    def Message(self,message,error=False):
        if self.args['verbose'] or self.args['debug']:
            print(message)
        if error:
            raise Exception(message)

    def Error(self,message):
        self.Message(message,error=True)

    def __init__(self,**kwargs):
        dict.__init__(self,{'ixt':None})

        defaults,_ = self.ParseKeywordPairs()

        self.args=kwargs

        for key in kwargs:
            if not key in defaults:
                self.Error(f'unknown key: {key}')

        # default any argument not supplied in kwargs
        for key in defaults.keys():
            if not key in kwargs:
                kwargs[key]=defaults[key]

        self.args=kwargs

        filename=self.args['filename']
        if filename is None:
            self.Error('file name must be supplied')

        ext=os.path.splitext(filename)[-1]
        try:
            sp=si.sp.SParameterFile(filename)
            self.Message(os.path.split(filename)[-1] +' read')
        except:
            self.Error('file: '+filename+' could not be opened')

        if not self.args['port_reorder'] is None:
            try:
                sp=sp.PortReorder(eval('['+self.args['port_reorder']+']'))
                self.Message('ports reordered')
            except:
                self.Error('port reordering failed')
                                  
        if self.args['end_frequency'] != None or self.args['frequency_points'] != None:
            if self.args['end_frequency'] == None:
                self.Error('if number of frequency points specified, then end frequency must be specified')
            if self.args['frequency_points'] == None:
                self.Error('if end frequency is specified, then number of frequency points must be specified')
            fe=self.args['end_frequency']; n = self.args['frequency_points']
            sp=sp.Resample(si.fd.EvenlySpacedFrequencyList(fe,n))
            self.Message(f"resampled to end frequency: {ToSI(fe,'Hz')} with: {n} points")
        else:
            evenly_spaced = si.fd.FrequencyList(sp.m_f).CheckEvenlySpaced()
            if not evenly_spaced:
                self.Error('s-parameters are unevenly spaced.\n end frequency (-fe) and number of frequency points (-n) must be specified')

        if not self.args['single_ended_ports'] is None:
            try:
                # conversion from single ended to mixed mode
                single_ended_ports = eval('['+self.args['single_ended_ports']+']')
                if len(single_ended_ports)//2*2 != len(single_ended_ports):
                    self.Error('number of single-ended ports must be even')
                netlist=[f'device S {sp.m_P}']
                for p,n,d,c in zip(single_ended_ports[::2], # se p
                               single_ended_ports[1::2], # se n
                               [p+1 for p in range(len(single_ended_ports)//2)], # mm d
                               [p+1+len(single_ended_ports)//2 for p in range(len(single_ended_ports)//2)] # mm c
                               ):
                    netlist.append(f'device MM{d} 4 mixedmode')
                    netlist.append(f'connect S {p} MM{d} 1')
                    netlist.append(f'connect S {n} MM{d} 2')
                    netlist.append(f'port {d} MM{d} 3')
                    netlist.append(f'port {c} MM{d} 4')
    
                sdp=si.p.SystemDescriptionParser().AddLines(netlist)
                sspn=si.sd.SystemSParametersNumeric(sdp.SystemDescription())
    
                mmd=[]
                for d in range(len(sp.m_d)):
                    sspn.AssignSParameters('S',sp[d])
                    mmd.append(sspn.SParameters())
    
                sp = si.sp.SParameters(sp.m_f,mmd,sp.m_Z0)
                # s-parameters are now mixed-mode
                self.Message('s-parameters converted to mixed-mode')
            except:
                self.Error('error converting parameters to mixed mode')

        try:
            if self.args['reference_impedance'] is None:
                Z0_list = [sp.m_Z0 for _ in range(sp.m_P)]
            else:
                Z0_raw_list = eval('['+self.args['reference_impedance']+']')
                if len(Z0_raw_list) == 1:
                    Z0_list = [Z0_raw_list[0] for _ in range(sp.m_P)]
                elif len(Z0_raw_list) == 2:
                    Z0_list = [Z0_raw_list[0] for _ in range(sp.m_P//2)]\
                            + [Z0_raw_list[1] for _ in range(sp.m_P//2)]
                elif len(Z0_raw_list) == sp.m_P:
                    Z0_list=Z0_raw_list
                else:
                    self.Error(f'wrong number of reference impedances.  Should be 0, 1, 2, or {sp.m_P}.')
            self.Message('reference impedances determined')
        except:
            self.Error('error determining reference impedances')

        port_list = eval('['+self.args['victim_ports']+']') + eval('['+self.args['aggressor_ports']+']')
        tm_list = []

        if self.args['voltage_transfer_function']:
            try:
                # use voltage transfer functions
                netlist=[f'device S {sp.m_P}',
                         'voltagesource VS 1',
                         'device G 1 ground']
                for R_i in range(len(Z0_list)):
                    R=Z0_list[R_i]
                    netlist.append(f'device R{R_i+1} 2 R {R}')
                    netlist.append(f'connect S {R_i+1} R{R_i+1} 1')
                # now have a partially filled out nestlist with all source and load resistances in place
                # and connected to the DUT, along with a voltage source and ground declared.
                # All that is needed is connect the voltage source to the driven port resistance, tie all
                # the other ports to ground, and install the output probe.

                for input_port,output_port in zip(port_list[::2], # input port
                                                  port_list[1::2], # output port
                                                  ):
                    import copy
                    this_netlist = copy.deepcopy(netlist)
                    this_netlist.append(f'connect VS 1 R{input_port} 2')
                    this_netlist.append(f'voltageoutput VO S {output_port}')
                    ground_netlist_line = 'connect G 1'
                    for other_port in [p+1 for p in range(sp.m_P)]:
                        if other_port != input_port:
                            ground_netlist_line += f' R{other_port} 2'
                    this_netlist.append(ground_netlist_line)
                    snp=si.p.SimulatorNumericParser().AddLines(this_netlist)
                    sd=snp.SystemDescription()
                    sn=si.sd.SimulatorNumeric(sd)

                    mmd=[]
                    for d in range(len(sp.m_d)):
                        sn.AssignSParameters('S',sp[d])
                        mmd.append(sn.TransferMatrix())
                    
                    tm_list.append(si.sp.SParameters(sp.m_f,mmd,sp.m_Z0).FrequencyResponse(1,1))

                self.Message('voltage transfer functions generated')
            except:
                self.Error('error producing voltage transfer functions')
        else:
            try:
                # extract responses directly out of the (presumed) differential-mode s-parameters
                for input_port,output_port in zip(port_list[::2], # input port
                                                  port_list[1::2], # output port
                                                  ):
                    tm_list.append(sp.FrequencyResponse(output_port,input_port))

                self.Message('transfer functions extracted')
            except:
                self.Error('error extracting transfer functions')

        try:
            ixt=self.IXT(tm_list[0],tm_list[1:],tm_list[0].Frequencies()[-1])
        except:
            self.Error('integrated crosstalk could not be calculated')

        self['ixt'] = ixt

def IXT_Main():
    import sys
    args_list=sys.argv[1:]
    args,unknown = IXT_Calculator.ParseKeywordPairs(args_list)
    args['command_line']=True
    if args['profile']:
        import cProfile
        profiler=cProfile.Profile()
        profiler.enable()
        try:
            ixt_dict = IXT_Calculator(**args)
        except:
            ixt_dict = {'ixt':None}
        profiler.disable()
        import pstats
        p = pstats.Stats(profiler)
        p.strip_dirs().sort_stats('cumulative').print_stats(100)
    else:
        try:
            ixt_dict = IXT_Calculator(**args)
        except:
            ixt_dict = {'ixt':None}

    ixt = ixt_dict['ixt']
    if ixt is None:
        ixt = 'error'

    print(ixt)
    exit(1 if ixt == 'error' else 0)

if __name__ == '__main__': # pragma: no cover
    IXT_Main()