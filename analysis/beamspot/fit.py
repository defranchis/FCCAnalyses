import os
import sys
import json
import uproot
import awkward as ak
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


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


def fit_beamspot_gaussian(values):
    # estimate mean and width by fitting a gaussian

    # remove outliers
    lower_bound = np.quantile(values, 0.01)
    upper_bound = np.quantile(values, 0.99)
    values = values[((values>lower_bound) & (values<upper_bound))]

    # binning
    bins = np.linspace(np.amin(values), np.amax(values), num=100)
    x = (bins[:-1] + bins[1:])/2
    y = np.histogram(values, bins=bins)[0]

    # do fit
    def gauss(x, a, mu, sigma):
        return a*np.exp(-0.5*np.square(np.divide((x-mu), sigma)))
    a0 = np.amax(y)
    mu0 = np.mean(values)
    sigma0 = np.std(values)
    parameters, cov = curve_fit(gauss, x, y, p0=(a0, mu0, sigma0))
    
    # get parameters
    mean = parameters[1]
    width = parameters[2]
    meanunc = np.sqrt(cov[1,1])

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

    # make mask for events with valid primary vertex
    pv_mask = ( 
      (np.abs(events['PV_x'])>1e-12)
      | (np.abs(events['PV_y'])>1e-12)
      | (np.abs(events['PV_z'])>1e-12)
    ).to_numpy().astype(bool)

    # find runs
    runs = np.unique(events['runNumber'].to_numpy())

    # loop over runs
    data = {}
    for runidx, run in enumerate(runs):
        print(f'Processing run {run}...')

        # make a mask for this run
        run_mask = np.squeeze((events['runNumber']==run).to_numpy()).astype(bool)
        tot_mask = (pv_mask & run_mask)
        if np.sum(tot_mask) < 100:
            msg = f'WARNING: skipping run {run} because too few events.'
            print(msg)
            data[run] = None
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
            #data[run][varname] = fit_beamspot_simple(values)
            data[run][varname] = fit_beamspot_gaussian(values)

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

    # fill runs for which no sensible measurement could be made with sensible values
    for runidx, run in enumerate(runs):
        if data[run] is None:
            if runidx==0:
                nextrunidx = runidx + 1
                nextrun = runs[nextrunidx]
                while data[nextrun] is None:
                    nextrunidx += 1
                    nextrun = runs[nextrunidx]
                data[run] = data[nextrun]
            else:
                previousrunidx = runidx - 1
                previousrun = runs[previousrunidx]
                while data[previousrun] is None:
                    previousrunidx -= 1
                    previousrun = runs[previousrunidx]
                data[run] = data[previousrun]

    # parse data into format for writing
    data_to_write = {}
    for run, val in data.items():
        run = int(run)
        data_to_write[run] = {}
        for varname, values in val.items():
            vartag = varname.split('_')[-1]
            data_to_write[run][vartag]= float(values[0])
    
    # write output data
    with open('beamspot.json', 'w') as f:
        json.dump(data_to_write, f, indent=2)

    # make a summary figure
    fig, axs = plt.subplots(nrows=6, figsize=(12,12))
    colors = {'x': 'darkviolet', 'y': 'mediumpurple', 'z': 'blue'}
    for idx, varname in enumerate(pv_vars):
        ax1 = axs[2*idx]
        ax2 = axs[2*idx+1]
        means = np.array([data[run][varname][0] for run in data.keys()])
        stds = np.array([data[run][varname][1] for run in data.keys()])
        xax = np.arange(len(means))

        coord = varname.split('_')[-1]
        color = colors.get(coord, 'blue')

        # plot means and std
        ax1.fill_between(xax, means+stds, y2=means-stds, color=color, alpha=0.3)
        ax1.plot(xax, means, color=color, linewidth=2)
        mean = np.mean(means)
        ax1.axhline(mean, linestyle='dashed', color='gray')
        
        # plot std only
        ax2.fill_between(xax, stds, color=color, alpha=0.3)

        # plot aesthetics
        varlabel = f'Primary vertex {coord}-coordinate'
        ax1.set_xticklabels([])
        ax1.set_xticks([])
        text = ax1.text(0.98, 0.95, varlabel + ' fitted center + width', ha='right', va='top', transform=ax1.transAxes)
        text.set_bbox(dict(facecolor='white', alpha=0.7, edgecolor='white'))
        ax2.set_xticklabels([])
        ax2.set_xticks([])
        text = ax2.text(0.98, 0.95, varlabel + ' width', ha='right', va='top', transform=ax2.transAxes)
        text.set_bbox(dict(facecolor='white', alpha=0.7, edgecolor='white'))
        ax2.grid(axis='y', which='both', linestyle='dashed', color='grey')
        ax2.set_ylim((0, ax2.get_ylim()[1]*1.2))

    # more plot aesthetics
    axs[5].set_xlabel('Run')
    fig.subplots_adjust(wspace=0, hspace=0)

    # save figure
    fig.tight_layout()
    outputfile = os.path.join(outputdir, f'summary.png')
    fig.savefig(outputfile)

    # make another summary figure
    fig, axs = plt.subplots(nrows=6, figsize=(12,12))
    colors = {'x': 'darkviolet', 'y': 'mediumpurple', 'z': 'blue'}
    for idx, varname in enumerate(pv_vars):
        ax1 = axs[2*idx]
        ax2 = axs[2*idx + 1]
        means = np.array([data[run][varname][0] for run in data.keys()])
        uncs = np.array([data[run][varname][2] for run in data.keys()])
        xax = np.arange(len(means))

        coord = varname.split('_')[-1]
        color = colors.get(coord, 'blue')

        # plot means and uncertainty
        ax1.fill_between(xax, means+uncs, y2=means-uncs, color=color, alpha=0.3)
        ax1.plot(xax, means, color=color)
        mean = np.mean(means)
        ax1.axhline(mean, linestyle='dashed', color='gray')

        # plot uncertainty only
        ax2.fill_between(xax, uncs, color=color, alpha=0.3)

        # plot aesthetics
        varlabel = f'Primary vertex {coord}-coordinate'
        ax1.set_xticklabels([])
        ax1.set_xticks([])
        text = ax1.text(0.98, 0.95, varlabel + ' fitted center + uncertainty', ha='right', va='top', transform=ax1.transAxes)
        text.set_bbox(dict(facecolor='white', alpha=0.7, edgecolor='white'))
        ax2.set_xticklabels([])
        ax2.set_xticks([])
        text = ax2.text(0.98, 0.95, varlabel + ' uncertainty on fitted center', ha='right', va='top', transform=ax2.transAxes)
        text.set_bbox(dict(facecolor='white', alpha=0.7, edgecolor='white'))
        ax2.grid(axis='y', which='both', linestyle='dashed', color='grey')
        ax2.set_ylim((0, ax2.get_ylim()[1]*1.2))

    # more plot aesthetics
    axs[5].set_xlabel('Run')
    fig.subplots_adjust(wspace=0, hspace=0)

    # save figure
    fig.tight_layout()
    outputfile = os.path.join(outputdir, f'summary2.png')
    fig.savefig(outputfile)
