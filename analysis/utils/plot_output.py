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
      'recojet_isS',
      'recojet_isUD',
      #'recojet_isData'
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

      'recojet_sv_xrel',
      'recojet_sv_yrel',
      'recojet_sv_zrel',
      'recojet_sv_thetarel',
      'recojet_sv_phirel',
      'recojet_sv_p',
      'recojet_sv_prel',
      'recojet_sv_chi2',
      'recojet_sv_chi2Normalized',
      'recojet_sv_ndof',
      'recojet_sv_nTracks',
      'recojet_sv_mass',
      'recojet_sv_dxy',
      'recojet_sv_dxyz',
      'recojet_sv_cosPointing',

      'pfcand_pt',
      'pfcand_e',
      'pfcand_ptrel_log',
      'pfcand_erel_log',
      'pfcand_thetarel',
      'pfcand_phirel',
      'pfcand_charge',

      'pfcand_d0_wrt0',
      'pfcand_z0_wrt0',
      'pfcand_dxy',
      'pfcand_dz',

      'pfcand_Sip2dVal',
      'pfcand_Sip2dSig',
      'pfcand_Sip3dVal',
      'pfcand_Sip3dSig',
      'pfcand_JetDistVal',
      'pfcand_JetDistSig',

      'pfcand_linearSignedIP3D',
      'pfcand_linearSignedIP3DSig',
      'pfcand_transverseJetDistance',
      'pfcand_longitudinalJetDistance',
        
      'pfcand_dxydxy',
      'pfcand_dzdz'      
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

    # make kinematic mask (optional)
    #kinematic_mask = np.ones(len(events)).astype(bool)
    kinematic_mask = (
        (events['recojet_pt'].to_numpy()>10)
        & (np.abs(events['recojet_eta'].to_numpy())<0.9)
        & (events['nconst'].to_numpy()>5)
    ).astype(bool)

    # make category masks
    category_masks = {}
    for category in categories:
        category_masks[category] = events[category].to_numpy().astype(bool)

    # loop over variables to plot
    for variable in variables:
        print(f'Running on variable {variable}...')

        # get data
        data = {}
        for category in categories:
            this_data = events[variable][(kinematic_mask) & (category_masks[category])]
            
            # strategies for flattening per-constituent data
            if this_data.layout.minmax_depth[1]>=2:

                # approach 1: take all constituents
                #this_data = ak.flatten(this_data)

                # approach 2: take leading constituent
                # note: constituents do not seem to be pt-ordered by default!
                if len(this_data)==0: this_data = ak.Array([])
                else:
                    len_mask = np.nonzero(ak.num(this_data))[0].to_numpy().astype(bool)
                    this_data = this_data[len_mask]
                    pt = events['pfcand_pt'][(kinematic_mask) & (category_masks[category])]
                    pt = pt[len_mask]
                    ids = ak.argmax(pt, axis=1).to_numpy()
                    ids = np.array(list(ids))
                    this_data = this_data[np.arange(len(this_data)), ids]

            # parsing
            this_data = this_data.to_numpy()
            if np.isnan(this_data).any():
                msg = 'WARNING: replacing NaN by 0...'
                print(msg)
                np.nan_to_num(this_data, copy=False, nan=0)
            data[category] = this_data

        # optional: ignore dummy values
        for category in categories:
            this_data = data[category]
            mask = (np.abs(this_data+9)>1e-3).astype(bool)
            data[category] = this_data[mask]

        # group categories in single array
        data_array = np.concatenate(list(data.values()))

        # printouts for testing
        print(f'--- test output for variable {variable} ---')
        print(data_array)
        print('min: ', np.amin(data_array))
        print('max: ', np.amax(data_array))
        print('mean: ', np.mean(data_array))
        print('std: ', np.std(data_array))
        print('-----')

        # determine suitable binning
        mask = (np.abs(data_array+9)>1e-3).astype(bool)
        npass = np.sum(mask.astype(int))
        if npass==0:
            msg = 'WARNING: no instances pass mask; skipping this variable.'
            print(msg)
            continue
        minv = np.quantile(data_array[mask], 0.05)
        maxv = np.quantile(data_array[mask], 0.95)
        if minv < 0:
            maxv = max(maxv, abs(minv))
            minv = -maxv
        # special cases (hard-coded)
        if variable == 'recojet_sv_chi2Normalized': (minv, maxv) = (-2, 25)
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
