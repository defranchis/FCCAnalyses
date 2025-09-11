# Reference analysis scripts

### Introduction
These scripts were copied from here: [ADV99/ParticleNet_FCCSW](https://github.com/ADV99/ParticleNet_FCCSW/tree/main/FCCAnalyses), and minimally modified to make them work with the current central version of FCCAnalyses.
They can be used as a reference for testing and debugging.

### Issues
- It is hard to disentangle harmless syntax changes in central FCCAnalyses since the time when these scripts were developed, and deliberate changes to FCCAnalyses made by the developers as extensions to FCCAnalyses. To look in more detail, and maybe shift the changes in these scripts to corresponding changes in FCCAnalyses (in particular JetConstituentsUtils). But at least technically the scripts are running now (with central FCCAnalyses).
- The function to calculate the `mtof` variable seems to have undergone a more significant change in its signature than most of the other ones, and fixing it ad-hoc in these scripts does not seem trivial. To look in more detail later. But for now, this variable has just been disabled (i.e. commented out) everywhere.
