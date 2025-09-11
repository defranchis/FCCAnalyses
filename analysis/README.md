# Custom analysis scripts

### Introduction
These scripts are intended to produce training and testing ntuples for a ParticleNet-like jet tagger study from EDM4HEP files (in particular the recently parsed ALEPH data).

This happens in two stages:
- `analysis.py`: Read the input data and calculate all properties of interest.
- `makentuples.cpp`: Store all variables in per-jet ntuples.

For more detailed information about what happens in both stages, see [here](https://github.com/ADV99/ParticleNet_FCCSW/tree/main/FCCAnalyses).
Both stages are combined in `producetrees.py`.

### How to run
First follow the setup instructions in the [main README](https://github.com/LukaLambrecht/FCCAnalyses/blob/particlenet_ntuples/README.md).
Then, run `python producetrees.py` with the appropriate options, for example:
```
python producetrees.py -i samplelists/samples_test.txt -o output_test/output.root -n 100
```

Note: these instructions are preliminary and the code might change extensively in the future.
You can always run `python producetrees.py -h` to see all available options.

### Current status
Runs successfully on some example files for FCC-ee with some minor caveats, see [here](reference/README.md) for more details.

Does not run yet on our ALEPH data files, because the first step in `analysis.py` requires a collection of MC particles.
So we need to either wait for ALEPH simulation, or modify the workflow to make it run on data.
