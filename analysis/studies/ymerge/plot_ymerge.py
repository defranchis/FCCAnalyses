import os
import sys
import uproot
import awkward as ak
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


if __name__=='__main__':

    # settings
    inputfiles = sys.argv[1:]
    treename = 'events'
    outputdir = 'output_plots'

    variables = [
      'Event_dmerge1',
      'Event_dmerge2',
      'Event_dmerge3',
      'Event_dmerge4',
    ]

    selection_variables = [
        'Jets_pt', 'Jets_pz', 'Jets_theta',
        'recoEventType'
    ]

    # make output dir if needed
    if not os.path.exists(outputdir): os.makedirs(outputdir)

    # read input files
    batches = []
    branches_to_read = variables + selection_variables
    for idx, inputfile in enumerate(inputfiles):
        print(f'Reading file {idx+1} / {len(inputfiles)}', end='\r')
        readstr = ':'.join([inputfile, treename])
        with uproot.open(readstr) as f:
            batches.append(f.arrays(branches_to_read))
    events = ak.concatenate(batches)
    print(f'Read {len(events)} entries.')

    # do baseline event selection (optional)
    baseline_mask = np.ones(len(events)).astype(bool)
    jets_mask = (
        (np.sqrt(np.square(events['Jets_pt']) + np.square(events['Jets_pz'])) > 10)
        & (np.abs(np.cos(events['Jets_theta'])) < 0.65)
    )
    events_mask = (
        (ak.any(events['recoEventType']==16, axis=1))
        & (ak.sum(jets_mask, axis=1)==2)
    )
    baseline_mask = events_mask
    print(f'Made baseline mask with {np.sum(baseline_mask)} / {len(baseline_mask)} entries passing.')

    # loop over dmerge variables
    data = {}
    for variable in variables:
    
            # get data
            values = events[variable][baseline_mask]
            
            # parsing
            values = values.to_numpy()
            if np.isnan(values).any():
                msg = 'WARNING: replacing NaN by 0...'
                print(msg)
                np.nan_to_num(values, copy=False, nan=0)

            # add to struct
            data[variable] = values

            # make y_merge from d_merge
            y_merge = values / 91.2**2

            data[variable.replace('dmerge', 'ymerge')] = y_merge

    # determine ymerge cutoff where 3% of events are removed
    variable = 'Event_ymerge2'
    cutoff_amount = 0.03
    values = data[variable]
    cutoff_value = np.quantile(values, 1-cutoff_amount)
    print(f'Cutoff value where {cutoff_amount*100}% of events are removed (for variable {variable}): {cutoff_value}')

    # loop over types
    for vartype in ['dmerge', 'ymerge']:

        # set bins
        bins = np.linspace(0, 0.4, num=51)
        if vartype == 'dmerge': bins = np.linspace(0, 500, num=51)

        # make figure
        fig, ax = plt.subplots()
        for variable, values in data.items():
            if vartype not in variable: continue
            hist = np.histogram(values, bins=bins, density=True)[0]
            label = variable.replace('Event_', '')
            ax.stairs(hist, edges=bins, label=label, linewidth=2)

        # add cutoff
        if vartype=='ymerge':
            ax.axvline(x=cutoff_value, linestyle='--', color='r', label=f'{cutoff_amount*100}% cutoff')

        # plot aesthetics
        ax.set_ylabel('Events (normalized)', fontsize=12)
        ax.set_xlabel(vartype, fontsize=12)
        ax.grid(which='both', axis='both')
        ax.legend(fontsize=12)
        ax.set_yscale('log')

        # save figure
        fig.tight_layout()
        outputfile = os.path.join(outputdir, f'{vartype}.png')
        fig.savefig(outputfile)
        plt.close()
