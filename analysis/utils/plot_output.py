import os
import sys
import uproot
import awkward as ak
import numpy as np
import matplotlib.pyplot as plt


if __name__=='__main__':

    # settings
    inputfiles = sys.argv[1:]
    treename = 'tree'
    categories = [
      'recojet_isB',
      'recojet_isC',
      'recojet_isUDSG'
    ]
    variables = [
      'recojet_pt',
      'recojet_eta',
      'recojet_theta',
      'recojet_phi',
      'recojet_e',
      'recojet_mass',
      
      'nconst',
      'nphotons',
      'nchargedhad',
      'nneutralhad',
      'nel',
      'nmu',

      'pfcand_pt',
      'pfcand_e',
      'pfcand_ptrel_log',
      'pfcand_erel_log',
      'pfcand_thetarel',
      'pfcand_phirel',
      'pfcand_charge',

      'pfcand_dxy',
      'pfcand_dz',
      'pfcand_btagSip2dVal',
      'pfcand_btagSip2dSig',
      'pfcand_btagSip3dVal',
      'pfcand_btagSip3dSig',
      'pfcand_btagJetDistVal',
      'pfcand_btagJetDistSig',
      
    ]

    # read input files
    batches = []
    branches_to_read = categories + variables
    for idx, inputfile in enumerate(inputfiles):
        print(f'Reading file {idx+1} / {len(inputfiles)}', end='\r')
        readstr = ':'.join([inputfile, treename])
        with uproot.open(readstr) as f:
            batches.append(f.arrays(branches_to_read))
    events = ak.concatenate(batches)

    # make masks
    masks = {}
    for category in categories:
        masks[category] = events[category].to_numpy().astype(bool)

    # loop over variables to plot
    for variable in variables:
        print(f'Running on variable {variable}...')

        # get data
        data = {}
        for category in categories:
            this_data = events[variable][masks[category]]
            if this_data.layout.minmax_depth[1]>=2: this_data = ak.flatten(this_data)
            this_data = this_data.to_numpy()
            if np.isnan(this_data).any():
                msg = 'WARNING: replacing NaN by 0...'
                print(msg)
                np.nan_to_num(this_data, copy=False, nan=0)
            data[category] = this_data

        # determine suitable binning
        data_array = np.concatenate(list(data.values()))
        minv = np.quantile(data_array, 0.01)
        maxv = np.quantile(data_array, 0.99)
        bins = np.linspace(minv, maxv, num=51)

        # make figure
        fig, ax = plt.subplots()
        for category in categories:
            ax.hist(data[category], bins=bins, density=True, histtype='step', linewidth=2, label=category)

        # plot aesthetics
        ax.set_ylabel('Events (flattened, normalized)')
        ax.set_xlabel(variable)
        ax.legend()

        # save figure
        fig.tight_layout()
        fig.savefig(variable+'.png')

        # same with log scale
        ax.set_yscale('log')
        fig.tight_layout()
        fig.savefig(variable+'_log.png')

        # close figures to save memory
        plt.close()
