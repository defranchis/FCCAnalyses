import os
import sys
import uproot
import awkward as ak
import numpy as np
import matplotlib.pyplot as plt


if __name__=='__main__':

    # settings
    inputfiles = sys.argv[1:]
    treename = 'events'
    outputdir = 'output_plots'

    variables = [
      'PiPi_p',
      'PiPi_deltaR',
      'PiPi_angle',
    ]

    # make output dir if needed
    if not os.path.exists(outputdir): os.makedirs(outputdir)

    # read input files
    batches = []
    branches_to_read = ['genEventType'] + variables
    for idx, inputfile in enumerate(inputfiles):
        print(f'Reading file {idx+1} / {len(inputfiles)}', end='\r')
        readstr = ':'.join([inputfile, treename])
        with uproot.open(readstr) as f:
            batches.append(f.arrays(branches_to_read))
    events = ak.concatenate(batches)
    print(f'Read {len(events)} entries.')

    # loop over variables to parse
    data = {}
    for variable in variables:
        
        # get data
        this_data = events[variable]
            
        # flattening
        this_data = ak.flatten(this_data)

        # parsing
        this_data = this_data.to_numpy()
        if np.isnan(this_data).any():
            msg = 'WARNING: replacing NaN by 0...'
            print(msg)
            np.nan_to_num(this_data, copy=False, nan=0)

        # printouts for testing
        print(f'--- test output for variable {variable} ---')
        print(this_data)
        print('min: ', np.amin(this_data))
        print('max: ', np.amax(this_data))
        print('mean: ', np.mean(this_data))
        print('std: ', np.std(this_data))
        print('-----')

        # add to dict
        data[variable] = this_data

    # make figure of momentum vs delta R
    fig, ax = plt.subplots()
    pbins = np.linspace(0, 10, num=51)
    dbins = np.linspace(0, 1, num=51)
    hist = np.histogram2d(data['PiPi_p'], data['PiPi_deltaR'], bins=(pbins, dbins), density=True)[0]
    ax.hist2d(data['PiPi_p'], data['PiPi_deltaR'], bins=(pbins, dbins), density=True)

    # plot aesthetics
    ax.set_ylabel('Delta R', fontsize=12)
    ax.set_xlabel('Momentum (GeV)', fontsize=12)

    # save figure
    fig.tight_layout()
    outputfile = os.path.join(outputdir, 'p_vs_deltar.png')
    fig.savefig(outputfile)

    # make figure of momentum vs angle
    fig, ax = plt.subplots()
    pbins = np.linspace(0, 10, num=51)
    dbins = np.linspace(0, 1, num=51)
    hist = np.histogram2d(data['PiPi_p'], data['PiPi_deltaR'], bins=(pbins, dbins), density=True)[0]
    ax.hist2d(data['PiPi_p'], data['PiPi_angle'], bins=(pbins, dbins), density=True)

    # plot aesthetics
    ax.set_ylabel('Opening angle', fontsize=12)
    ax.set_xlabel('Momentum (GeV)', fontsize=12)

    # save figure
    fig.tight_layout()
    outputfile = os.path.join(outputdir, 'p_vs_angle.png')
    fig.savefig(outputfile)

    # close figures to save memory
    plt.close()
