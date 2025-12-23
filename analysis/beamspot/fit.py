import os
import sys
import uproot
import awkward as ak
import numpy as np
import matplotlib.pyplot as plt


def fit_beamspot_simple(values):
    # do simple fit of mean and width of beamspot
    
    # remove outliers
    lower_bound = np.quantile(values, 0.01)
    upper_bound = np.quantile(values, 0.99)
    values = values[((values>lower_bound) & (values<upper_bound))]

    # calculate mean and std
    mean = np.mean(values)
    width = np.std(values)
    meanunc = width/np.sqrt(len(values))

    return (mean, width, meanunc)


if __name__=='__main__':

    # settings
    inputfiles = sys.argv[1:]
    outputdir = 'output_plots'
    do_run_plots = False

    # fixed settings
    treename = 'events'
    pv_vars = ['PV_x', 'PV_y', 'PV_z']
    id_vars = ['runNumber']

    # make output directory
    if not os.path.exists(outputdir): os.makedirs(outputdir)

    # read input files
    batches = []
    branches_to_read = pv_vars + id_vars
    for idx, inputfile in enumerate(inputfiles):
        print(f'Reading file {idx+1} / {len(inputfiles)}', end='\r')
        readstr = ':'.join([inputfile, treename])
        with uproot.open(readstr) as f:
            batches.append(f.arrays(branches_to_read))
    events = ak.concatenate(batches)

    # make mask for events with no valid primary vertex
    pv_mask = ( 
      (np.abs(events['PV_x'])>1e-12)
      | (np.abs(events['PV_y'])>1e-12)
      | (np.abs(events['PV_z'])>1e-12)
    ).to_numpy().astype(bool)

    # find runs
    runs = np.unique(events['runNumber'].to_numpy())

    # loop over runs
    data = {}
    for run in runs:
        print(f'Processing run {run}...')

        # make a mask for this run
        run_mask = np.squeeze((events['runNumber']==run).to_numpy()).astype(bool)
        tot_mask = (pv_mask & run_mask)
        if np.sum(tot_mask) < 100:
            msg = f'WARNING: skipping run {run} because too few events.'
            print(msg)
            continue

        # loop over variables
        data[run] = {}
        data_for_plotting = {}
        for varname in pv_vars:
            values = events[varname][tot_mask].to_numpy()
            lower_bound = np.quantile(values, 0.01)
            upper_bound = np.quantile(values, 0.99)
            values_for_plotting = values[((values>lower_bound) & (values<upper_bound))]
            data_for_plotting[varname] = values_for_plotting

            # calculate the central value and width
            # note: preliminary, to replace with more advanced fitting
            data[run][varname] = fit_beamspot_simple(values)

        if not do_run_plots: continue

        # make figure
        fig, axs = plt.subplots(nrows=3)
        for idx, varname in enumerate(pv_vars):
            ax = axs[idx]
            values = data_for_plotting[varname]
            mean = data[run][varname][0]
            width = data[run][varname][1]
            ax.hist(values, bins=50, histtype='step', linewidth=2)
            ax.axvline(x=mean, color='blue', linestyle='dashed')
            ax.axvline(x=mean+width, color='red', linestyle='dashed')
            ax.axvline(x=mean-width, color='red', linestyle='dashed')

            # plot aesthetics
            ax.set_ylabel('Events')
            ax.text(0.98, 0.95, varname, ha='right', va='top', transform=ax.transAxes)
            ax.text(0.98, 0.75, 'Mean: {:.2e} cm'.format(mean), ha='right', va='top', transform=ax.transAxes)
            ax.text(0.98, 0.55, 'Width: {:.2e} cm'.format(width), ha='right', va='top', transform=ax.transAxes)

        # more plot aesthetics
        axs[-1].set_xlabel('[cm]')
        
        axs[0].text(0.99, 1.05, f'Run {run}', ha='right', transform=axs[0].transAxes)

        # save figure
        fig.tight_layout()
        outputfile = os.path.join(outputdir, f'run_{run}.png')
        fig.savefig(outputfile)

        # close figures to save memory
        plt.close()

    # make a summary figure
    fig, axs = plt.subplots(nrows=3, figsize=(12,6))
    for idx, varname in enumerate(pv_vars):
        ax = axs[idx]
        means = np.array([data[run][varname][0] for run in data.keys()])
        stds = np.array([data[run][varname][1] for run in data.keys()])
        xax = np.arange(len(means))
        ax.fill_between(xax, means+stds, y2=means-stds, color='purple', alpha=0.3)
        ax.plot(xax, means, color='blue', linewidth=2)

        mean = np.mean(means)
        ax.axhline(mean, linestyle='dashed', color='gray')
        
        # plot aesthetics
        ax.set_xticklabels([])
        ax.text(0.98, 0.95, varname, ha='right', va='top', transform=ax.transAxes)

    # more plot aesthetics
    axs[2].set_xlabel('Run')
    axs[1].set_ylabel('Estimated beamspot center and width [cm]', labelpad=10)

    # save figure
    fig.tight_layout()
    outputfile = os.path.join(outputdir, f'summary.png')
    fig.savefig(outputfile)

    # make another summary figure
    fig, axs = plt.subplots(nrows=3, figsize=(12,6))
    for idx, varname in enumerate(pv_vars):
        ax = axs[idx]
        means = np.array([data[run][varname][0] for run in data.keys()])
        uncs = np.array([data[run][varname][2] for run in data.keys()])
        xax = np.arange(len(means))
        ax.fill_between(xax, means+uncs, y2=means-uncs, color='blue', alpha=0.3)
        ax.plot(xax, means, color='blue')

        mean = np.mean(means)
        ax.axhline(mean, linestyle='dashed', color='gray')

        # plot aesthetics
        ax.set_xticklabels([])
        ax.text(0.98, 0.95, varname, ha='right', va='top', transform=ax.transAxes)
        ax.text(0.98, 0.8, 'Mean: {:.2e} +- {:.2e}'.format(np.mean(means), np.std(means)),
          ha='right', va='top', transform=ax.transAxes)

    # more plot aesthetics
    axs[2].set_xlabel('Run')
    axs[1].set_ylabel('Estimated beamspot center with uncertainty [cm]', labelpad=10)

    # save figure
    fig.tight_layout()
    outputfile = os.path.join(outputdir, f'summary2.png')
    fig.savefig(outputfile)
