# ParticleNet ntuple branch of FCCAnalyses

This is a special branch of FCCAnalyses, intended to prepare ntuples for ParticleNet training from EDM4HEP files.

### How to set up
Note: these instructions are valid for `lxplus`, not necessarily for other environments.
1. Clone this repository (and make sure to switch to this branch).
2. Run the builtin setup script:
```
source ./setup.sh
```
3. Build and install
```
mkdir build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install
cd ..
```
(Note: this step is not needed if no modifications are made to the FCCAnalyses framework,
in which case the library is taken from some remote location;
use this step if you want to use the local and potentially modified framework.
Probably you will need to re-run this step every time you make a modification,
but this remains to be double-checked).

### How to run
Go into the `analysis` subfolder.
Run `python producetrees.py -h` to see a list of all available options.
See more detailed instructions in the [analysis/README.md](analysis/README.md).

### References
- The main FCCAnalyses repo (from which this is a fork) is here: [HEP-FCC/FCCAnalyses](https://github.com/HEP-FCC/FCCAnalyses).
- This branch is based on [this example](https://github.com/ADV99/ParticleNet_FCCSW/tree/main), but is updated to deal with newer versions of FCCAnalyses and with other samples.
