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
    treename = 'tree'
    outputdir = 'output_plots'

    variables = [
      'pfcand_pt',
      'pfcand_pz',
      'pfcand_charge',

      'pfcand_dEdx_pads_type',
      'pfcand_dEdx_pads_value',
      'pfcand_dEdx_pads_error',
      'pfcand_dEdx_wires_type',
      'pfcand_dEdx_wires_value',
      'pfcand_dEdx_wires_error',      
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
    #kinematic_mask = (
    #    (events['recojet_pt'].to_numpy()>10)
    #    & (np.abs(events['recojet_eta'].to_numpy())<0.9)
    #    & (events['nconst'].to_numpy()>5)
    #).astype(bool)
    print(f'Made kinematic mask with {np.sum(kinematic_mask)} / {len(kinematic_mask)} entries passing.')

    # make charge mask (optional)
    #charge_mask = np.ones_like(events['pfcand_charge'])
    charge_mask = (events['pfcand_charge'] != 0)

    # loop over pads and wires
    for system in ['pads', 'wires']:
        print(f'Running on system {system}...')

        # make good measurement mask
        measurement_mask = (events[f'pfcand_dEdx_{system}_type'] == 0)
        total_mask = ((kinematic_mask) & (charge_mask) & (measurement_mask))

        # get data
        values = events[f'pfcand_dEdx_{system}_value'][total_mask]
        p = np.sqrt( np.square(events['pfcand_pt'][total_mask]) + np.square(events['pfcand_pz'][total_mask]) )
            
        # strategies for flattening per-constituent data
        strategy = 'flatten' # choose from "flatten" or "leading"

        # approach 1: take all constituents
        if strategy=='flatten':
            values = ak.flatten(values)
            p = ak.flatten(p)

        # approach 2: take leading constituent
        # note: constituents do not seem to be pt-ordered by default!
        elif strategy=='leading':
            if len(values)==0: values = ak.Array([])
            else:
                len_mask = np.nonzero(ak.num(values))[0].to_numpy().astype(bool)
                values = values[len_mask]
                p = p[len_mask]
                ids = ak.argmax(p, axis=1).to_numpy()
                ids = np.array(list(ids))
                values = values[np.arange(len(values)), ids]
                p = p[np.arange(len(p)), ids]

        else: raise Exception(f'Strategy {strategy} not recognized.')

        # parsing
        values = values.to_numpy()
        p = p.to_numpy()
        if np.isnan(values).any():
            msg = 'WARNING: replacing NaN by 0...'
            print(msg)
            np.nan_to_num(values, copy=False, nan=0)

        # optional: ignore dummy values
        mask = (values > 0.1).astype(bool)
        values = values[mask]
        p = p[mask]

        # make figure
        fig, ax = plt.subplots()
        ax.scatter(p, values, s=1, color='blue', alpha=0.1)

        # plot aesthetics
        ax.set_ylabel('$dE/dx$', fontsize=12)
        ax.set_xlabel('$p_{T}$', fontsize=12)
        ax.grid(which='both', axis='both')
        ax.set_xscale('log')
        ax.set_ylim((0, 10))
        ax.set_xlim((0.1, 10))

        # save figure
        fig.tight_layout()
        outputfile = os.path.join(outputdir, f'dedx_{system}_scatter.png')
        fig.savefig(outputfile)

        # close figures to save memory
        plt.close()

        # make alternative figure (density histogram)
        fig, ax = plt.subplots()
        xbins = np.logspace(-1, 1, num=50, base=10)
        ybins = np.linspace(0, 10, num=50)
        ax.hist2d(p, values, bins=(xbins, ybins), density=True, norm=mpl.colors.LogNorm())

        # plot aesthetics
        ax.set_ylabel('$dE/dx$', fontsize=12)
        ax.set_xlabel('$p$', fontsize=12)
        ax.set_xscale('log')
        ax.set_ylim((0, 10))
        ax.set_xlim((0.1, 10))

        # save figure
        fig.tight_layout()
        outputfile = os.path.join(outputdir, f'dedx_{system}_density.png')
        fig.savefig(outputfile)

        # close figures to save memory
        plt.close()
