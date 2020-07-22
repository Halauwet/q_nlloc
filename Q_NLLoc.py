import sys
# import os
from datetime import datetime as dt

sys.path.append('/mnt/d/q_repo/q_modul')
sys.path.append('D:/q_repo/q_modul')
from check_outliers import *

sys.path.append('/mnt/d/q_repo/q_convert')
sys.path.append('D:/q_repo/q_convert')
from nlloc_rw import ReadNLLoc
from velest_rw import WriteVelest

"""
===========================================
NLLoc processing routine by @eqhalauwet
==========================================

Python module for reading velest output, ploting and exporting to GMT input.

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:
# 
# 1. Read velest mainprint to see adjustmet hypocenter, velocity model, and RMS every iteration
# 2. Read cnv file modified to python 3 from pyvelest code (https://github.com/saeedsltm/PyVelest)  
# 
# Logs:
# 
# 2017-Sep: Added _check_header line to automatic check data format from few Seiscomp3 version (see Notes).
# 2019-Oct: Major change: store readed data in dictionary format.
# 2020-May: Correction: select phase only without 'X' residual (unused phase on routine processing).
# 2020-Jul: Major change added Run_Velest() and Run_VelestSet() to run Velest recursively
# 2020-Jul: RunVelestSet() added recursive routine to adjust input velocity layer if velest is hang 
(solution not stable)

"""


def write_ctrl(base, x_len, y_len, z_len, mod, out_dir, out_cf, hdr_cf, sta_cor=False):
    # tambah opsi P_flag = True, S_flag = False,

    # hdr = f'{x_len + 1} {y_len + 1} {z_len * 2 + 1} -{x_len / 2:.1f} -{y_len / 2:.1f} 0.0 1.0 1.0 0.5   PROB_DENSITY'
    hdr = f'{x_len + 1} {y_len + 1} {z_len * 2 + 1} -{x_len / 2:.1f} -{y_len / 2:.1f} 0.0 1.0 1.0 0.5   MISFIT'

    hdrout = open(hdr_cf, 'w')
    hdrout.write(f'{hdr}\n')
    hdrout.close()

    ctrlout = open(out_cf, 'w')

    with open(base) as f:

        hint_model = '###model'
        hint_phase = '###phase'
        hint_vgrid = '###velgrid'
        hint_lgrid = '###locgrid'
        hint_corr = '###corrections'

        flag_model = False
        flag_phase = False
        flag_vgrid = False
        flag_lgrid = False
        flag_corr = False

        for l in f:

            if hint_vgrid in l:
                flag_vgrid = True
            if flag_vgrid and hint_vgrid not in l:
                l = f'VGGRID  2 {int((max(x_len, y_len) + max(x_len, y_len) / 5) * 10 + 1)} {(z_len + 10) * 10 + 1}' \
                    f'  0.0 0.0 -2.0  0.1 0.1 0.1  SLOW_LEN\n'
                flag_vgrid = False

            if hint_model in l:
                flag_model = True
            if flag_model and hint_model not in l:
                l = f'INCLUDE {mod}\n'
                flag_model = False

            if hint_phase in l:
                flag_phase = True
            if flag_phase and hint_phase not in l:
                l = f'LOCFILES ./input/phase.obs HYPOELLIPSE ./time/layer ./{out_dir}/q_loc\n'
                flag_phase = False

            if hint_lgrid in l:
                flag_lgrid = True
            if flag_lgrid and hint_lgrid not in l:
                l = f'LOCGRID  {hdr}  SAVE\n'
                flag_lgrid = False

            if hint_corr in l:
                flag_corr = True
            if flag_corr and hint_corr not in l:
                if sta_cor:
                    l = f"INCLUDE {os.path.join(out_dir, 'last.stat_totcorr')}\n"
                else:
                    l = f"#INCLUDE {os.path.join(out_dir, 'last.stat_totcorr')}\n"
                flag_corr = False

            ctrlout.write(l)

    ctrlout.close()


def Run_NLLocSet(x_len=500, y_len=300, z_len=100):

    my_dir = os.getcwd()
    mod_dir = os.path.join('input', 'mod')

    if not os.path.exists(os.path.join('input')):
        os.makedirs('input')
    if not os.path.exists(mod_dir):
        os.makedirs(mod_dir)

    inpmod = []
    mod_nm = []
    for m in os.listdir(os.path.join(my_dir, mod_dir)):
        if os.path.isfile(os.path.join(my_dir, mod_dir, m)):
            inpmod.append(os.path.join(mod_dir, m))
            mod_nm.append(m[13:-4])

    logfile = open('NLLocSet_log.txt', 'w')

    if len(inpmod) > 0:
        log = f'\n__NLLoc Set Runner by eQ Halauwet__\n' \
              f'\nNLLoc will run several iteration set for {len(inpmod)} input model:\n'
    else:
        log = f'\n__NLLoc Set Runner by eQ Halauwet__\n' \
              f'\nPlease place your input model in folder "input/mod/" . . .\n'
        print(log)
        sys.exit(0)

    print(log)
    logfile.write(log)

    for m in mod_nm:
        log = ' * ' + m
        print(log)
        logfile.write(log)

    # Make NLLoc output folder
    if not os.path.exists(os.path.join('loc')):
        os.makedirs('loc')
    if not os.path.exists(os.path.join('model')):
            os.makedirs('model')
    if not os.path.exists(os.path.join('time')):
        os.makedirs('time')

    for mod, num, md_nm in zip(inpmod, range(len(inpmod)), mod_nm):
        if not os.path.exists(os.path.join('loc', md_nm)):
            os.makedirs(os.path.join('loc', md_nm))
        out_dir = os.path.join('loc', md_nm)

        max_rms = []
        min_pha = 5
        max_gap = 360

        log = f'\n\n\n>>> {num + 1}. Input model {md_nm}:\n'
        print(log)
        logfile.write(log)

        ctrl = 'q_nlloc'
        hdr_cf = f'{ctrl}.hdr'
        out_cf = f'{ctrl}.in'
        write_ctrl(os.path.join('input', 'base.in'), x_len, y_len, z_len, mod, out_dir, out_cf, hdr_cf, sta_cor=False)

        print('Run Vel2Grid . . .\n')
        os.system('Vel2Grid ' + out_cf + ' > /dev/null')
        # os.system('Vel2Grid ' + out_cf)
        # cmd = 'Vel2Grid ' + out_cf
        # proc = sp.Popen(cmd, stdout=sp.PIPE)
        # output = proc.communicate()[0]

        print('Run Grid2Time . . .\n')
        os.system('Grid2Time ' + out_cf + ' > /dev/null')
        # cmd = 'Grid2Time ' + out_cf

        for i in range(2):

            if i == 0:
                print('Run 1st step NLLoc . . .\n')
                print(' station correction = no')
                os.system('NLLoc ' + out_cf + ' > /dev/null')
            else:
                print('Run NLLoc . . .\n')
                print(' station correction = yes\n')
                write_ctrl(os.path.join('input', 'base.in'), x_len, y_len, z_len,
                           mod, out_dir, out_cf, hdr_cf, sta_cor=True)
                os.system('NLLoc ' + out_cf)
                log = ('\n\n finished ' + str(dt.now().strftime("%d-%b-%Y %H:%M:%S")) +
                       '\n_____________________________________\n')
                print(log)
                logfile.write(log)

            # sp.Popen('NLLoc' + out_cf, stdout=sp.PIPE)
            # cmd = 'NLLoc ' + out_cf
            # proc = sp.Popen(cmd, stdout=sp.PIPE)
            # output = proc.communicate()[0]
            # print(output)

        LocSum = f'./{ctrl} 1 {out_dir}/q_loc "{out_dir}/q_loc.*.*.grid0.loc" [] [] {max_rms} {min_pha} {max_gap}'
        os.system(f'LocSum {LocSum}')
        # cmd = f'LocSum {LocSum}'
        # proc = sp.Popen(cmd, cwd=my_dir, stdout=sp.PIPE)
        # output = proc.communicate()[0]
        # print(output)

        fileinput = [f'{out_dir}/q_loc.hyp']
        mag_cat = 'input/nlloc_mag.dat'  # output from bmkg2nlloc
        nllocdata, ids, elim_event = ReadNLLoc(fileinput, mag_cat)

        pha_dir = os.path.join('output', md_nm)

        if not os.path.exists('output'):
            os.makedirs('output')
        if not os.path.exists(pha_dir):
            os.makedirs(pha_dir)

        output_p = os.path.join(pha_dir, 'phase_P.cnv')
        output_s = os.path.join(pha_dir, 'phase_S.cnv')
        output_arr = os.path.join(pha_dir, 'arrival.dat')
        output_cat = os.path.join(pha_dir, 'catalog.dat')
        out_log = os.path.join(pha_dir, 'log.txt')
        out_geo = os.path.join(pha_dir, 'sts_geometry.txt')

        # FILTER PARAMETER

        # Filter phase
        lst_phase = ['AAI', 'AAII', 'KRAI', 'MSAI', 'BNDI',
                     'BANI', 'NLAI', 'BSMI', 'OBMI']

        # Filter area
        ulat = -1.5
        blat = -5.5
        llon = 126
        rlon = 131.5
        max_depth = 80

        # Filter kualitas data
        mode = 'OCTREE'
        max_rms = 3
        max_gap = 200
        min_P = 5
        min_S = 0
        max_spatial_err = 10
        rem_fixd = True
        min_time = dt(1970, 1, 3)  # (year, month, day)
        max_time = dt(2019, 12, 31)  # (year, month, day)

        filt_dic = {'lst_pha': lst_phase,
                    'area': {'top': ulat,
                             'bot': blat,
                             'left': llon,
                             'right': rlon
                             },
                    'max_dep': max_depth,
                    'rem_fixd': rem_fixd,
                    'max_gap': max_gap,
                    'max_rms': max_rms,
                    'min_P': min_P,
                    'min_S': min_S,
                    'max_err': max_spatial_err,
                    'mode': mode,
                    'min_tim': min_time,
                    'max_tim': max_time
                    }

        WriteVelest(inp=nllocdata, filt=filt_dic, out_P=output_p, out_S=output_s, out_arr=output_arr,
                    out_cat=output_cat, out_log=out_log, out_geom=out_geo ,inptype='nlloc',
                    filt_flag=True, prob_flag=False)

        if os.stat(output_arr).st_size == 0:
            continue

        check_outliers(arrival_file=output_arr, out_dir=pha_dir, std_error=4)
