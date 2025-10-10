# Simple utility script to print the number of events in a root file


import os
import sys
import ROOT


if __name__=='__main__':

    # read input files
    inputfiles = sys.argv[1:]

    # get number of events per file
    nevents= {}
    for inputfile in inputfiles:
        f = ROOT.TFile.Open(inputfile)
        try:
            # for raw input files in EDM4HEP format
            tree = f.Get("events")
            tree.GetEntries()
        except:
            # for ntuples
            tree = f.Get("tree")
        nevents[inputfile] = tree.GetEntries()

    # print results
    print('Found following number of events:')
    for key, val in nevents.items():
        print(f'  - {key}: {val}')
    print(f'  --> total: {sum(list(nevents.values()))}')
