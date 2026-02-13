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
        parser.add_argument('-pf','--profile',action='store_true', help='profiles the software')
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
            print('error')
            if self.args['command_line']:
                exit(1)
            else:
                raise Exception(message)

    def Error(self,message):
        self.Message(message,error=True)

    def __init__(self,**kwargs):
        dict.__init__(self,{})

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
            ixt='error'
        print(ixt)
        exit(1 if ixt == 'error' else 0)

        # guess_file = self.args['guess_file']
        # if guess_file != None:
        #     if os.path.splitext(guess_file)[-1].lower() == '.json':
        #         import json
        #         try:
        #             with open(guess_file,'r') as f:
        #                 gf=json.load(f)
        #                 guess=gf['raw']
        #                 self.args['zero_pairs'] = gf['zero pair']['number of']
        #                 self.args['pole_pairs'] = gf['pole pair']['number of']
        #
        #                 self.Message('guess file: '+filename+' read')
        #                 self.Message('zeros are '+str(self.args['zero_pairs'])+' and poles are '+str(self.args['pole_pairs'])+' from guess file')
        #         except:
        #             self.Error('guess file: '+filename+' could not be opened')
        #     else:
        #         try:
        #             gf = PoleZeroLevMar.ReadResultsFile(guess_file)
        #             self.Message('guess file: '+os.path.split(filename)[-1]+' read')
        #
        #             self.args['zero_pairs'] = gf[0]
        #             self.args['pole_pairs'] = gf[1]
        #             guess = gf[2:]
        #             self.Message('zeros are '+str(gf[0])+' and poles are '+str(gf[1])+' from guess file')
        #         except:
        #             self.Error('guess file: '+filename+' could not be opened')
        #
        # num_poles = self.args['pole_pairs']
        # num_zeros = self.args['zero_pairs']
        #
        # if num_zeros == None:
        #     self.Error('number of zero pairs must be specified (-zp)')
        #
        # if num_poles == None:
        #     self.Error('number of pole pairs must be specified (-pp)')
        #
        # if guess == None:
        #     self.Message('zeros are '+str(num_zeros)+' and poles are '+str(num_poles))
        #
        #
        # self.Message(f"initial delay: {ToSI(self.args['initial_delay'],'s')}")
        # self.Message(f"minimum delay allowed: {ToSI(self.args['min_delay'],'s')}")
        # if self.args['max_delay'] == None:
        #     self.Message('there is no limit on maximum delay')
        # else:
        #     self.Message(f"maximum delay allowed: {ToSI(self.args['max_delay'],'s')}")
        #
        # if self.args['fix_gain']:
        #     self.Message('gain is fixed')
        # else:
        #     self.Message('gain is a free variable in the fit')
        #
        # if not self.args['fix_delay'] and self.args['fit_type'] == 'magnitude':
        #     self.args['fix_delay'] = True
        #     self.Message('delay is always fixed for magnitude fits')
        # else:
        #     if self.args['fix_delay']:
        #         self.Message('delay is fixed')
        #     else:
        #         self.Message('delay is a free variable in the fit')
        #
        # self.Message("poles are always restricted to LHP")
        # if self.args['lhp_zeros']:
        #     self.Message("zeros are restricted to LHP")
        # else:
        #     self.Message('no restriction on LHP or RHP on zeros')
        #
        # if self.args['real_zeros']:
        #     self.Message('zeros are restricted to be real')
        # else:
        #     self.Message('zeros are allowed to be complex')
        #
        # self.Message(f"maximum Q is {self.args['max_q']}")

        # fit_type=self.args['fit_type']
        # if fit_type == 'magnitude':
        #     self.Message('fit type is: magnitude')
        # elif fit_type == 'complex':
        #     self.Message('fit type is: complex')
        # else:
        #     self.Error('fit type must be either "magnitude" or "complex"')

        # default_initial_lambda = defaults['initial_lambda']
        # initial_lambda=self.args['initial_lambda']
        # if default_initial_lambda != initial_lambda:
        #     self.Message(f'initial λ: {initial_lambda} as opposed to default of: {default_initial_lambda}')
        #

        # default_lambda_multiplier = defaults['lambda_multiplier']
        # lambda_multiplier=self.args['lambda_multiplier']
        # if default_lambda_multiplier != lambda_multiplier:
        #     self.Message(f'λ multiplier: {lambda_multiplier} as opposed to default of: {default_lambda_multiplier}')
        #

        # default_tolerance = defaults['tolerance']
        # tolerance=self.args['tolerance']
        # if default_tolerance != tolerance:
        #     self.Message(f'tolerance is: {tolerance} as opposed to default of: {default_tolerance}')
        #
        # default_max_frequency_multiplier = defaults['max_frequency_multiplier']
        # max_frequency_multiplier=self.args['max_frequency_multiplier']
        # if default_max_frequency_multiplier != max_frequency_multiplier:
        #     self.Message(f'max_frequency_multiplier is: {max_frequency_multiplier} as opposed to default of: {default_max_frequency_multiplier}')
        #
        # import time
        # from datetime import datetime
        # start_time = time.time()
        # self.m_fitter=PoleZeroLevMar(fr,num_zeros,num_poles,
        #                              guess=guess,
        #                              min_delay=self.args['min_delay'],
        #                              max_delay=self.args['max_delay'],
        #                              max_Q=self.args['max_q'],
        #                              initial_delay=self.args['initial_delay'],
        #                              max_iterations=self.args['max_iterations'],
        #                              mse_unchanging_threshold=self.args['mse_unchanging_threshold'],
        #                              LHP_zeros=self.args['lhp_zeros'],
        #                              real_zeros=self.args['real_zeros'],
        #                              fit_type=self.args['fit_type'],
        #                              initial_lambda=self.args['initial_lambda'],
        #                              lambda_multiplier=self.args['lambda_multiplier'],
        #                              tolerance=self.args['tolerance'],
        #                              max_frequency_multiplier=self.args['max_frequency_multiplier'],
        #                              fix_delay=self.args['fix_delay'],
        #                              fix_gain=self.args['fix_gain'],
        #                              callback=self.PlotResult)
        # self.plotInitialized=False
        #
        # if self.args['profile']:
        #     import cProfile
        #     profiler=cProfile.Profile()
        #     profiler.enable()
        #     self.m_fitter.Solve()
        #     profiler.disable()
        #     import pstats
        #     p = pstats.Stats(profiler)
        #     p.strip_dirs().sort_stats('cumulative').print_stats(100)
        # else:
        #     self.m_fitter.Solve()
        #
        # self.Message('convergence: '+str(self.m_fitter.ccm.why))
        # self.Message('iterations: '+str(self.m_fitter.ccm._IterationsTaken)+' mse:'+str(self.m_fitter.ccm._Mse))
        #
        # end_time = time.time()
        # elapsed_time=end_time-start_time
        # if self.args['debug'] or self.args['verbose']:
        #     self.m_fitter.PrintResults()
        # if self.args['debug']:
        #     self.m_fitter.WriteResultsToFile('test_result.txt').WriteGoalToFile('test_goal.txt')
        #
        # if self.args['debug']:
        #     # make an s-parameter file out of this result
        #     try:
        #         from SignalIntegrity.Lib.Fit.PoleZero.QuadraticComplex import TransferFunctionComplexVectorized
        #         sp=si.sp.SParameterFile(filename)
        #         if self.args['reference_impedance'] != None:
        #             sp.SetReferenceImpedance(self.args['reference_impedance'])
        #         f=sp.m_f
        #         new_s21=TransferFunctionComplexVectorized(np.array(f)*2.*np.pi,
        #                                               np.array(self.m_fitter.Results()),
        #                                               num_zeros,
        #                                               num_poles,
        #                                               self.args['fix_gain'],
        #                                               self.args['fix_delay']
        #                                               ).H
        #         if self.args['voltage_transfer_function']:
        #             # convert back to s11
        #             s11=sp.FrequencyResponse(1,1)
        #             for n in range(len(f)):
        #                 sp.m_d[n][1][0] = new_s21[n]*(1+s11[n])
        #         else:
        #             for n in range(len(f)):
        #                 sp.m_d[n][1][0] = new_s21[n]
        #         sp.WriteToFile('debug')
        #     except:
        #         pass
        # self.Message(f'elapsed time: {elapsed_time} s')
        #
        # results={}
        # if self.args['output_file'] or not self.args['command_line']:
        #     num_zero_pairs=self.m_fitter.num_zero_pairs
        #     num_pole_pairs=self.m_fitter.num_pole_pairs
        #     raw_results=self.m_fitter.Results()
        #
        #     results['raw']=raw_results
        #     results['configuration']=self.args
        #     results['convergence']={'iterations':self.m_fitter.ccm._IterationsTaken,
        #                             'mse':self.m_fitter.ccm._Mse,
        #                             'time':elapsed_time,
        #                             'completed':datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        #                             'why stopped':self.m_fitter.ccm.why,
        #                             'frequency multiplier':self.m_fitter.mul}
        #     fit_result=self.m_fitter.fF(self.m_fitter.m_a).reshape(-1).tolist()
        #     results['response']={'frequency':fr.Frequencies(),
        #                          'goal':{'magnitude':fr.Values('mag'),'phase':fr.Values('deg')},
        #                          'result':{'magnitude':[np.abs(v) for v in fit_result],
        #                                    'phase':[np.angle(v)*180/np.pi for v in fit_result]}}
        #     results['gain']={'value':raw_results[0],'dB':20*math.log10(np.abs(raw_results[0]))}
        #     results['delay']={'value':raw_results[1]}
        #     results['pole pair']={'number of':num_pole_pairs,'list':[]}
        #     results['pole']={'number of':num_pole_pairs*2,'list':[]}
        #     results['zero pair']={'number of':num_zero_pairs,'list':[]}
        #     results['zero']={'number of':num_zero_pairs*2,'list':[]}
        #     for s in range(num_zero_pairs):
        #         wz=raw_results[s*2+2+0]
        #         Qz=raw_results[s*2+2+1]
        #         zeta=1/(2.*Qz)
        #         if zeta < 1./np.sqrt(2):
        #             try:
        #                 wr=np.sqrt(1-2*(zeta*zeta))*wz
        #             except (RuntimeWarning,RuntimeError):
        #                 wr=0
        #             if np.isnan(wr):
        #                 wr=0
        #         else:
        #             wr=0
        #         peak_dB = 0 if wr==0 else 20*np.log10(abs(wz*wz/((wz*wz-wr*wr)+1j*wr*wz/Qz)))
        #         zeros = np.roots(np.array([1, wz/Qz, wz*wz]))
        #         zero_mag = [np.abs(z) for z in zeros]
        #         zero_angle = [np.angle(z) for z in zeros]
        #         zero_real = [z.real for z in zeros]
        #         zero_imag = [z.imag for z in zeros]
        #         results['zero pair']['list'].append({'w0':wz,
        #                                              'Q':Qz,
        #                                              'zeta':zeta,
        #                                              'f0':wz/(2.*np.pi),
        #                                              'wr':wr,
        #                                              'fr':wr/(2.*np.pi),
        #                                              'peakdB':peak_dB})
        #         for z in range(2):
        #             results['zero']['list'].append({#'complex':zeros[z],
        #                                'real':zero_real[z],
        #                                'imag':zero_imag[z],
        #                                'mag':zero_mag[z],
        #                                'angle':{'rad':zero_angle[z],
        #                                         'deg':zero_angle[z]*180./np.pi}})
        #     for s in range(num_pole_pairs):
        #         wp=raw_results[(s+num_zero_pairs)*2+2+0]
        #         Qp=raw_results[(s+num_zero_pairs)*2+2+1]
        #         zeta=1/(2.*Qp)
        #         if zeta < 1./np.sqrt(2):
        #             try:
        #                 wr=np.sqrt(1-2*(zeta*zeta))*wp
        #             except (RuntimeWarning,RuntimeError):
        #                 wr=0
        #             if np.isnan(wr):
        #                 wr=0
        #         else:
        #             wr=0
        #         peak_dB = 0 if wr==0 else 20*np.log10(abs(wp*wp/((wp*wp-wr*wr)+1j*wr*wp/Qp)))
        #         poles = np.roots(np.array([1, wp/Qp, wp*wp]))
        #         pole_mag=[np.abs(p) for p in poles]
        #         pole_angle=[np.angle(p) for p in poles]
        #         pole_real=[p.real for p in poles]
        #         pole_imag=[p.imag for p in poles]
        #         results['pole pair']['list'].append({'w0':wp,
        #                                              'Q':Qp,
        #                                              'zeta':zeta,
        #                                              'f0':wp/(2.*np.pi),
        #                                              'wr':wr,
        #                                              'fr':wr/(2.*np.pi),
        #                                              'peakdB':peak_dB})
        #         for p in range(2):
        #             results['pole']['list'].append({#'complex':poles[p],
        #                                'real':pole_real[p],
        #                                'imag':pole_imag[p],
        #                                'mag':pole_mag[p],
        #                                'angle':{'rad':pole_angle[p],
        #                                         'deg':pole_angle[p]*180./np.pi}})
        #
        #     if self.args['output_file']:
        #         self.args['output_file']=os.path.splitext(self.args['output_file'])[0]+'.json'
        #         import json
        #         with open(self.args['output_file'],'w') as f:
        #             json.dump(results,f,indent=4)
        # self.Message('done')
        # if self.args['debug'] and self.args['command_line']:
        #     input("Press Enter to continue...")
        # dict.__init__(self,results)

def IXT_Main():
    import sys
    args_list=sys.argv[1:]
    args,unknown = IXT_Calculator.ParseKeywordPairs(args_list)
    args['command_line']=True
    IXT_Calculator(**args)

if __name__ == '__main__': # pragma: no cover
    IXT_Main()