#!/usr/bin/env python3

"""split_sample.py

Split input sample into equi-populated bins.

:Author: Martin Kilbinger <martin.kilbinger@cea.fr>

:Date: 2022

"""

import sys
import os

import numpy as np

from optparse import OptionParser
import matplotlib.pylab as plt

from statsmodels.distributions.empirical_distribution import ECDF

from astropy.io import ascii
from astropy.table import Table 

from unions_wl import sample

from sp_validation import util
from sp_validation import plots


def params_default():

    params = {
        'input_path': 'SDSS_SMBH_202206.txt',
        'key_ra': 'ra',
        'key_dec': 'dec',
        'key_z': 'z',
        'key_logM': 'logM',
        'n_split': 2,
        'n_bin_z_hist': 100,
        'output_dir': 'data_mass_sub',
        'output_fname_base': 'SDSS_SMBH_202206',
    }

    short_options = {
        'input_path': '-i',
        'n_split': '-n',
        'output_dir': '-o',
    }

    types = {
        'n_split': 'int',
        'n_bin_z_hist': 'int',
    }

    help_strings = {
        'input_path': 'catalogue input path, default={}',
        'n_split': 'number of equi-populated bins on output, default={}',
        'n_bin_z_hist': 'number of bins for redshift histogram, default={}',
        'output_dir': 'output directory, default={}',
    }


    return params, short_options, types, help_strings


def parse_options(p_def, short_options, types, help_strings):
    """Parse command line options.

    Parameters
    ----------
    p_def : dict
        default parameter values
    help_strings : dict
        help strings for options

    Returns
    -------
    options: tuple
        Command line options
    """

    usage  = "%prog [OPTIONS]"
    parser = OptionParser(usage=usage)

    for key in p_def:
        if key in help_strings:

            if key in short_options:
                short = short_options[key]
            else:
                short = ''

            if key in types:
                typ = types[key]
            else:
                typ = 'string'

            parser.add_option(
                short,
                f'--{key}',
                dest=key,
                type=typ,
                default=p_def[key],
                help=help_strings[key].format(p_def[key]),
            )

    parser.add_option(
        '-v',
        '--verbose',
        dest='verbose',
        action='store_true',
        help=f'verbose output'
    )

    options, args = parser.parse_args()

    return options


def main(argv=None):

    params, short_options, types, help_strings  = params_default()

    options = parse_options(params, short_options, types, help_strings)

    # Update parameter values
    for key in vars(options):
        params[key] = getattr(options, key)

    # Save calling command
    util.log_command(argv)

    # Open input catalogue
    if params['verbose']:
        print(f'Reading catalogue {params["input_path"]}...')
    names = [
        params['key_ra'],
        params['key_dec'],
        params['key_z'],
        params['key_logM'],
    ]
    dat = ascii.read(f'{params["input_path"]}', names=names)

    # To split into more equi-populated bins, compute cumulative distribution function
    if params['verbose']:
        print(f'Computing cdf({params["key_logM"]})...')
    cdf = ECDF(dat[params['key_logM']])

    # Split into two (check whether we get median from before)
    logM_bounds = sample.y_equi(cdf, params['n_split'])

    # Add min and max to boundaries
    logM_bounds.insert(0, min(dat[params['key_logM']]))
    logM_bounds.append(max(dat[params['key_logM']]))

    # Create masks to select mass bins
    mask_list = []
    labels = []
    for idx in range(len(logM_bounds) - 1):
        label = f'{logM_bounds[idx]} <= logM < {logM_bounds[idx + 1]}'
        labels.append(label)
        if params['verbose']:
            print(
                f'Creating sample #{idx+1}/{params["n_split"]} with {label}'
            )
        mask = (
            (dat[params['key_logM']] >= logM_bounds[idx])
            & (dat[params['key_logM']] < logM_bounds[idx + 1])
        )
        mask_list.append(mask)

    if not os.path.exists(params['output_dir']):
        os.mkdir(params['output_dir'])

    # Plot mass histograms
    xs = []
    n_bin = 100
    for mask in mask_list:
        xs.append(dat[params['key_logM']][mask])
    plots.plot_histograms(
        xs,
        labels,
        'AGN SMBH mass distribution',
        r'$\log ( M_\ast / M_\odot )$',
        'frequency',
        [min(dat[params['key_logM']]), max(dat[params['key_logM']])],
        int(n_bin / params['n_split']),
        f'{params["output_dir"]}/hist_{params["key_logM"]}.pdf',
    )

    # Add columns for weight for each sample
    for idx in range(len(mask_list)):
            dat[f'w_{idx}'] = np.ones_like(dat[params['key_z']])

    # Assign weights according to local density in redshift histogram.

    fac = 1.0001
    z_min = min(dat['z']) / fac
    z_max = max(dat['z']) * fac

    z_centres_arr = []
    z_hist_arr = []
    for idx, mask in enumerate(mask_list):
        
        z_hist, z_edges = np.histogram(
            dat['z'][mask],
            bins=int(params['n_bin_z_hist'] / params['n_split']),
            density=True,
            range=(z_min, z_max),
        )
        z_centres = [(z_edges[i] + z_edges[i+1]) / 2 for i in range(len(z_edges) - 1)]

        z_hist_arr.append(z_hist)
        z_centres_arr.append(z_centres)
    
        # Plot histogram
        plt.step(z_centres, z_hist, where='mid', label=idx)
    
        weights = np.ones_like(dat['z'][mask])

        for idz, z in enumerate(dat['z'][mask]):
            w = np.where(z > z_edges)[0]
            if len(w) == 0:
                print('Error:', z)
            else:
                idh = w[-1]
            weights[idz] = 1 / z_hist[idh]

        dat[f'w_{idx}'][mask] = weights
    
    # Plot original redshift histograms
    plots.plot_data_1d(
        z_centres_arr,
        z_hist_arr,
        [],
        'AGN SMBH redshift distribution',
        '$z$',
        'frequency',
        f'{params["output_dir"]}/hist_{params["key_z"]}.pdf',
    )

    # Plot reweighted redshift histograms, which should be flat
    xs = []
    ws = []
    for idx, mask in enumerate(mask_list):
        dat_mask = dat[mask]
        xs.append(dat_mask[params['key_z']])
        ws.append(dat_mask[f'w_{idx}'])

    plots.plot_histograms(
        xs,
        labels,
        'AGN SMBH reweighted redshift distribution',
        '$z$',                                                                  
        'frequency',                                                            
        [z_min, z_max],
        int(params['n_bin_z_hist'] / params['n_split']),
        f'{params["output_dir"]}/hist_reweighted_{params["key_z"]}.pdf',
        weights=ws,
        density=True,
    )

    # Plot reweighted redshift histograms, which should be flat
    xs = []
    for idx, mask in enumerate(mask_list):
        dat_mask = dat[mask]
        xs.append(dat_mask[params['key_logM']])
        ws.append(dat_mask[f'w_{idx}'])

    plots.plot_histograms(
        xs,
        labels,
        'AGN SMBH reweighted mass distribution',
        r'$\log ( M_\ast / M_\odot )$',
        'frequency',                                                            
        [z_min, z_max],
        int(params['n_bin_z_hist'] / params['n_split']),
        f'{params["output_dir"]}/hist_reweighted_{params["key_z"]}.pdf',
        weights=ws,
        density=True,
    )

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
