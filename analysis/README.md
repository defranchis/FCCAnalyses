# Custom analysis scripts

### Introduction
These scripts are intended to produce training and testing ntuples for a ParticleNet-like jet tagger study from EDM4HEP files (in particular the recently parsed ALEPH data).

This happens in two stages:
- `analysis.py`: Read the input data and calculate all properties of interest.
- `makentuples.cpp`: Store all variables in per-jet ntuples.
For more detailed information about what happens in both stages, see [here](https://github.com/ADV99/ParticleNet_FCCSW/tree/main/FCCAnalyses).
Both stages are combined in `producetrees.py`.

### How to run
Open `producetrees.py` and modify the settings as preferred.
Then run:
```
python producetrees.py
```

To do: update with more detailed instructions.
