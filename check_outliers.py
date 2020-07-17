import numpy as np
import pandas as pd
import os
import sys
from math import sqrt
from scipy import stats
from matplotlib import pyplot as plt

"""
=============================================================
outliers checker and remover from arrival data by @eqhalauwet
=============================================================

Python script for read arrival data then locate outliers sts and event_id

Written By, eQ Halauwet BMKG-PGR IX Ambon.
yehezkiel.halauwet@bmkg.go.id


Notes:

1. It is read arrival data output bmkg2velest

Logs:

"""

def calc_std_dev(x, y, slope, intercept):
    N = len(x)
    dev = np.zeros(N)
    var = 0
    for i in range(N):
        mean = (intercept + x[i] * slope)
        dev[i] = y[i] - mean
        var += dev[i]**2
    sigma = sqrt(var/(N-1))
    regress_line = [[min(x), intercept + min(x) * slope], [max(x), intercept + max(x) * slope]]
    sigma_line = [[min(x) + 1,
                   (intercept + (min(x) + 1) * slope) + (4 * sigma), (intercept + (min(x) + 1) * slope) - (4 * sigma),
                   (intercept + (min(x) + 1) * slope) + (6 * sigma), (intercept + (min(x) + 1) * slope) - (6 * sigma),
                   (intercept + (min(x) + 1) * slope) + (8 * sigma), (intercept + (min(x) + 1) * slope) - (8 * sigma)],
                  [max(x) - 1,
                   (intercept + (max(x) - 1) * slope) + (4 * sigma), (intercept + (max(x) - 1) * slope) - (4 * sigma),
                   (intercept + (max(x) - 1) * slope) + (6 * sigma), (intercept + (max(x) - 1) * slope) - (6 * sigma),
                   (intercept + (max(x) - 1) * slope) + (8 * sigma), (intercept + (max(x) - 1) * slope) - (8 * sigma)]]
    return sigma, regress_line, sigma_line, dev


def check_outliers(arrival_file='arrival.dat', out_dir='output', std_error=4):

    ids = '__check outliers from arrival data . . .\n\n'
    if os.stat(arrival_file).st_size == 0:
        sys.exit("Arrival data is empty\n")
    data = pd.read_csv(arrival_file, header=None, delim_whitespace=True)
    # data = pd.read_csv(regress_file, delim_whitespace=True)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if not os.path.exists(os.path.join(out_dir, 'inc')):
        os.makedirs(os.path.join(out_dir, 'inc'))

    Tp = data.iloc[:, 2]
    Ts = data.iloc[:, 3]
    Tsp = data.iloc[:, 4]

    x = Tsp
    y = Tp
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    sig, regr_line, sig_line, devs = calc_std_dev(x, y, slope, intercept)
    slp, icep, r_val, p_val, st_err = stats.linregress(Tp, Ts)
    sigPS, regr_linePS, sig_linePS, devsPS = calc_std_dev(Tp, Ts, slp, icep)

    dev = pd.Series(devs)
    threshold = float(std_error * dev.std())

    drop_rows = dev[abs(dev[:]) > threshold]
    filt_rows = dev[abs(dev[:]) <= threshold]
    idx_drop = drop_rows.index.to_list()
    idx_filt = filt_rows.index.to_list()

    plt.ion()
    plt.plot(x, y, 'o', label='data')
    plt.plot(x, x * slope + intercept, label='mean')
    plt.plot(x, ((x * slope + intercept) + (std_error * sig)), label='(+) ' + str(std_error) + ' sigma error')
    plt.plot(x, ((x * slope + intercept) - (std_error * sig)), label='(-) ' + str(std_error) + ' sigma error')
    plt.legend()
    eqs = ('y = {:.4f} + {:.4f}x'.format(intercept, slope))
    plt.text(x.mean(), y.mean(), eqs, horizontalalignment='left', verticalalignment='bottom')
    plt.show()
    plt.pause(0.001)

    filt_data = data.drop(idx_drop)
    drop_data = data.drop(idx_filt)

    np.savetxt(os.path.join(out_dir, 'filtered_arrival.dat'), filt_data.values, fmt='%s')
    np.savetxt(os.path.join(out_dir, 'droped_arrival.dat'), drop_data.values, fmt='%s')
    np.savetxt(os.path.join(out_dir, 'inc', 'regresi_line.dat'), regr_linePS, fmt='%s')
    np.savetxt(os.path.join(out_dir, 'inc', 'sigma_line.dat'), sig_linePS, fmt='%s')
    np.savetxt(os.path.join(out_dir, 'inc', 'regresi_line_Tsp-p.dat'), regr_line, fmt='%s')
    np.savetxt(os.path.join(out_dir, 'inc', 'sigma_line_Tsp-p.dat'), sig_line, fmt='%s')

    if len(idx_drop) > 0:
        log = ('{} phases diremove pada filtered_arrival:\n '.format(len(idx_drop)))
        for i in range(len(idx_drop)):
            log += ('stasiun {} event no {}\n '.format(drop_data.iloc[i, 1], drop_data.iloc[i, 0]))
        log += '\nIt is recommended to reduce the weight of these phases manually ' \
               'from velest, nlloc or hypodd input data'
    else:
        log = 'Tidak ada data dengan error > ' + str(std_error) + ' sigma'
    print('\n' + ids + log)
    file = open(os.path.join(out_dir, 'log_outliers.txt'), 'w')
    file.write(ids + log)
    file.close()
