import os
import sys
import uproot
import numpy as np


if __name__=='__main__':

    input_files = sys.argv[1:]

    lumidict = {}
    
    lumi = 0.
    for idx, input_file in enumerate(input_files):
        print(f'Reading file {idx+1} / {len(input_files)}', end='\r')
        with uproot.open(input_file+':events') as f:
            runinfo = f['RunInformation'].array()
            this_lumi = runinfo[:,5].to_numpy()
            mask = (np.roll(this_lumi,1)!=this_lumi)
            this_lumi = this_lumi[mask]
            this_lumi = np.sum(this_lumi)
            lumi += this_lumi
        print()
    print(f'Total luminosity: {lumi}')
