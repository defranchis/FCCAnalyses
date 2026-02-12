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

    categories = {
      5: ('b-jets', 'darkviolet'),
      4: ('c-jets', 'mediumpurple'),
      3: ('s-jets', 'dodgerblue'),
      2: ('d-jets', 'deepskyblue'),
      1: ('u-jets', 'deepskyblue'),
    }

    variables = [
      'nKs',
      'Ks_pt',
      'Ks_production_dxyz',
      'Ks_production_dxy',
      'Ks_decay_dxyz',
      'Ks_decay_dxy',

      'nPiPi',
      'PiPi_mass',
      'PiPi_deltaR',
      'PiPi_p1',
      'PiPi_p2'
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

    # make category masks
    category_masks = {}
    for category in categories.keys():
        category_masks[category] = (events['genEventType']==category).to_numpy().astype(bool)
    print(f'Found following number of entries per category:')
    for category in categories.keys(): print(f'  - {category}: {np.sum(category_masks[category])}')
    print(f'  -> total: {sum([np.sum(v) for v in category_masks.values()])}')

    # loop over variables to plot
    for variable in variables:
        print(f'Running on variable {variable}...')

        # get data
        data = {}
        for category in categories.keys():
            this_data = events[variable][category_masks[category]]
            
            # flattening
            if variable.startswith('Ks_'): this_data = ak.flatten(this_data)
            if variable.startswith('PiPi_'): this_data = ak.flatten(this_data)

            # parsing
            this_data = this_data.to_numpy()
            if np.isnan(this_data).any():
                msg = 'WARNING: replacing NaN by 0...'
                print(msg)
                np.nan_to_num(this_data, copy=False, nan=0)
            data[category] = this_data

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

        # determine whether variable is integer
        is_integer = False
        if np.all(data_array - data_array.astype(int) < 1e-6): is_integer = True

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
        if is_integer:
            maxv = max(maxv, 5)
            minv = int(minv) - 0.5
            maxv = int(maxv) + 0.5
        num_edges = 51
        if is_integer: num_edges = int(maxv - minv) + 1
        bins = np.linspace(minv, maxv, num=num_edges)

        # make figure
        fig, ax = plt.subplots()
        for category, settings in categories.items():
            hist = np.histogram(data[category], bins=bins)[0]
            errors = np.sqrt(hist)
            binwidths = bins[1:] - bins[:-1]
            integral = np.sum(np.multiply(hist, binwidths))
            if integral > 0:
                hist = hist / integral
                errors = errors / integral
            ax.stairs(hist, edges=bins, linewidth=2, label=settings[0], color=settings[1])
            ax.stairs(hist+errors, baseline=hist-errors, edges=bins, fill=True, color=settings[1], alpha=0.2)

        # plot aesthetics
        ax.set_ylabel('Events (normalized)')
        ax.set_xlabel(variable)
        ax.legend()
        ax.grid(which='both', axis='both')

        # save figure
        fig.tight_layout()
        outputfile = os.path.join(outputdir, variable+'.png')
        fig.savefig(outputfile)

        # same with log scale
        ax.set_yscale('log')
        fig.tight_layout()
        outputfile = os.path.join(outputdir, variable+'_log.png')
        fig.savefig(outputfile)

        # close figures to save memory
        plt.close()
