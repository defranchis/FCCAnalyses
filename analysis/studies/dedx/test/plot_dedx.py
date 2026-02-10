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
      'JetsConstituents_pt',
      'JetsConstituents_charge',
      'JetsConstituents_pdgId',

      'JetsConstituents_dEdx_pads_type',
      'JetsConstituents_dEdx_pads_value',
      'JetsConstituents_dEdx_pads_error',
      'JetsConstituents_dEdx_wires_type',
      'JetsConstituents_dEdx_wires_value',
      'JetsConstituents_dEdx_wires_error',      
    ]

    # make output dir if needed
    if not os.path.exists(outputdir): os.makedirs(outputdir)

    # read input files
    batches = []
    branches_to_read = variables
    for idx, inputfile in enumerate(inputfiles):
        print(f'Reading file {idx+1} / {len(inputfiles)}', end='\r')
        readstr = ':'.join([inputfile, treename])
        with uproot.open(readstr) as f:
            batches.append(f.arrays(branches_to_read))
    events = ak.concatenate(batches)
    print(f'Read {len(events)} entries.')

    # make kinematic mask (optional)
    kinematic_mask = np.ones(len(events)).astype(bool)
    print(f'Made kinematic mask with {np.sum(kinematic_mask)} / {len(kinematic_mask)} entries passing.')

    # make charge mask (optional)
    charge_mask = (events['JetsConstituents_charge'] != 0)

    # make categories
    categories = {
        'pion': np.abs(events['JetsConstituents_pdgId'])==211,
        'kaon': np.abs(events['JetsConstituents_pdgId'])==321,
        'proton': np.abs(events['JetsConstituents_pdgId'])==2212
    }

    # loop over pads and wires
    for system in ['pads', 'wires']:
        print(f'Running on system {system}...')

        # make good measurement mask
        measurement_mask = (events[f'JetsConstituents_dEdx_{system}_type'] == 0)
        total_mask = ((kinematic_mask) & (charge_mask) & (measurement_mask))

        # loop over categories
        category_data = {}
        for category_label, category_mask in categories.items():
        
            # get data
            values = events[f'JetsConstituents_dEdx_{system}_value'][((total_mask) & (category_mask))]
            pt = events['JetsConstituents_pt'][((total_mask) & (category_mask))]
            
            # strategies for flattening per-constituent data
            strategy = 'flatten' # choose from "flatten" or "leading"

            # approach 1: take all constituents
            if strategy=='flatten':
                values = ak.flatten(values, axis=None)
                pt = ak.flatten(pt, axis=None)

            else: raise Exception(f'Strategy {strategy} not recognized.')

            # parsing
            values = values.to_numpy()
            pt = pt.to_numpy()
            if np.isnan(values).any():
                msg = 'WARNING: replacing NaN by 0...'
                print(msg)
                np.nan_to_num(values, copy=False, nan=0)

            # optional: ignore dummy values
            mask = (values > 0.1).astype(bool)
            values = values[mask]
            pt = pt[mask]

            # add to struct
            category_data[category_label] = (pt, values)

        # make figure
        fig, ax = plt.subplots()
        for category_label, data in category_data.items():
            ax.scatter(data[0], data[1], s=1, label=category_label, alpha=0.1)

        # plot aesthetics
        ax.set_ylabel('$dE/dx$', fontsize=12)
        ax.set_xlabel('$p_{T}$', fontsize=12)
        ax.grid(which='both', axis='both')
        leg = ax.legend()
        for lh in leg.legend_handles:
            lh.set_alpha(1)
            lh.set_sizes([5])
        ax.set_xscale('log')
        ax.set_ylim((0, 10))
        ax.set_xlim((0.1, 10))

        # save figure
        fig.tight_layout()
        outputfile = os.path.join(outputdir, f'dedx_{system}_scatter.png')
        fig.savefig(outputfile)
