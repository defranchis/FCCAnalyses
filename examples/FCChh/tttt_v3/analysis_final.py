# Input directory where the files produced at the pre-selection level are
inputDir = "/eos/experiment/fcc/hh/analysis_ntuples/fcc_v06/II/ttbar_diff_analysis/"
inputDir = "/eos/user/s/selvaggi/analysis/ttbar_diff"

# Input directory where the files produced at the pre-selection level are
outputDir = f"{inputDir}/final/"

processList = {
    "mgp8_pp_tt012j_5f_HT_0_600": {},
    "mgp8_pp_tt012j_5f_HT_600_1200": {},
    "mgp8_pp_tt012j_5f_HT_1200_2100": {},
    "mgp8_pp_tt012j_5f_HT_2100_3400": {},
    "mgp8_pp_tt012j_5f_HT_3400_5300": {},
    "mgp8_pp_tt012j_5f_HT_5300_8100": {},
    "mgp8_pp_tt012j_5f_HT_8100_15000": {},
    "mgp8_pp_tt012j_5f_HT_15000_25000": {},
    "mgp8_pp_tt012j_5f_HT_25000_35000": {},
    "mgp8_pp_tt012j_5f_HT_35000_100000": {},
}

# Link to the dictonary that contains all the cross section informations etc...
procDict = "/eos/experiment/fcc/hh/utils/FCCDicts/FCChh_procDict_fcc_v06_II.json"
# Note the numbeOfEvents and sumOfWeights are placeholders that get overwritten with the correct values in the samples

# How to add a process that is not in the official dictionary:
# procDictAdd={"pwp8_pp_hh_5f_hhbbyy": {"numberOfEvents": 4980000, "sumOfWeights": 4980000.0, "crossSection": 0.0029844128399999998, "kfactor": 1.075363, "matchingEfficiency": 1.0}}

# Expected integrated luminosity
intLumi = 30e06  # pb-1

# Whether to scale to expected integrated luminosity
doScale = True

# Number of CPUs to use
nCPUS = 48

# produces ROOT TTrees, default is False
doTree = True

saveTabular = True

# Optional: Use weighted events
do_weighted = True

# Dictionary of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = {
    "sel1_bjets": "n_bjets > -1",
}

# Dictionary for the output variable/histograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.

# add these variables
# "tt_m",
# "tt_pt",
# "tt_eta",
# "tt_phi",
# "t1_pt",
# "t1_eta",
# "t1_phi",
# "t1_m",
# "t2_pt",
# "t2_eta",
# "t2_phi",
# "t2_m",


histoList = {
    # "n_jets": {"name": "n_jets", "title": "n_jets", "bin": 10, "xmin": 0, "xmax": 10},
    "n_bjets": {"name": "n_bjets", "title": "n_bjets", "bin": 10, "xmin": 0, "xmax": 10},
    "n_muons": {"name": "n_muons", "title": "n_muons", "bin": 10, "xmin": 0, "xmax": 10},
    "n_electrons": {"name": "n_electrons", "title": "n_electrons", "bin": 10, "xmin": 0, "xmax": 10},
    "MET": {"name": "MET", "title": "MET[GeV]", "bin": 50, "xmin": 0.0, "xmax": 250},
    "pT_bjets": {"name": "pT_bjets", "title": "pT_{bjets} [GeV]", "bin": 50, "xmin": 0.0, "xmax": 250.0},
    "HT": {"name": "HT", "title": "Scalar HT [GeV]", "bin": 50, "xmin": 0.0, "xmax": 100000.0},
    "genHT": {"name": "genHT", "title": "gen Scalar HT[GeV]", "bin": 50, "xmin": 0.0, "xmax": 100000.0},
    "tt_m": {"name": "tt_m", "title": "tt_m [GeV]", "bin": 50, "xmin": 0.0, "xmax": 100000.0},
    "tt_pt": {"name": "tt_pt", "title": "tt_pt [GeV]", "bin": 50, "xmin": 0.0, "xmax": 50000.0},
    "tt_eta": {"name": "tt_eta", "title": "tt_eta", "bin": 50, "xmin": -5.0, "xmax": 5.0},
    "t1_pt": {"name": "t1_pt", "title": "t1_pt [GeV]", "bin": 50, "xmin": 0.0, "xmax": 50000.0},
    "t1_eta": {"name": "t1_eta", "title": "t1_eta", "bin": 50, "xmin": -5.0, "xmax": 5.0},
    "t2_pt": {"name": "t2_pt", "title": "t2_pt [GeV]", "bin": 50, "xmin": 0.0, "xmax": 50000.0},
    "t2_eta": {"name": "t2_eta", "title": "t2_eta", "bin": 50, "xmin": -5.0, "xmax": 5.0},
}
