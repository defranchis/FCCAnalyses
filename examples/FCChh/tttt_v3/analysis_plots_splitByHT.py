import ROOT

# plot the mumu bkg sample in the separate HT slices

# global parameters
intLumi = 30e06  # in pb-1
ana_tex = "pp #rightarrow ttbar analysis "
delphesVersion = "3.4.2"
energy = 84
collider = "FCC-hh"
inputDir = "/eos/user/m/mdefranc/FCC-hh/4t_dilept/"
formats = ["png"]
# formats        = ['png','pdf']
# yaxis          = ['log']
yaxis = ["lin", "log"]
# stacksig       = ['stack']
stacksig = ["stack", "nostack"]
outdir = "/eos/user/m/mdefranc/www/FCC-hh/4t_dilept/"
plotStatUnc = True


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

variables = [
    "HT",
    # "pT_bjets",
    # "MET",
    # "genHT",
    # "tt_m",
    # "tt_pt",
    # "tt_eta",
    # "t1_pt",
    # "t1_eta",
    # "t2_pt",
    # "t2_eta",
]


# rebin = [1, 1, 1, 1, 2] # uniform rebin per variable (optional)

### Dictionary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection
selections = {}
selections["4t_diff_analysis"] = ["N_{bjets} #geq 3"]

extralabel = {}
extralabel["N_{bjets} #geq 3"] = "N_{bjets} #geq 3"

colors = {}

colors["4t_slice1"] = ROOT.kRed
colors["4t_slice2"] = ROOT.kBlue
colors["4t_slice3"] = ROOT.kGreen + 2
colors["4t_slice4"] = ROOT.kOrange + 7



procs = {}
procs["signal"] = {
        "4t_slice1": ["mgp8_pp_tttt_wmlep_Q_0_1000_5f_84TeV", 
                      "mgp8_pp_tttt_wplep_Q_0_1000_5f_84TeV"],
    }
procs["backgrounds"] = {        
        "4t_slice2": ["mgp8_pp_tttt_wmlep_Q_1000_3000_5f_84TeV",
                      "mgp8_pp_tttt_wplep_Q_1000_3000_5f_84TeV"],   
        "4t_slice3": ["mgp8_pp_tttt_wmlep_Q_3000_10000_5f_84TeV",
                      "mgp8_pp_tttt_wplep_Q_3000_10000_5f_84TeV"],
        "4t_slice4": ["mgp8_pp_tttt_wmlep_Q_10000_84000_5f_84TeV",
                      "mgp8_pp_tttt_wplep_Q_10000_84000_5f_84TeV"],
    }

legend = {}
legend["4t_slice1"] = "4t Q 0 1000"
legend["4t_slice2"] = "4t Q 1000 3000"
legend["4t_slice3"] = "4t Q 3000 10000"
legend["4t_slice4"] = "4t Q 10000 84000"




# procs["signal"] = {
#         "4t_slice1_wm": ["mgp8_pp_tttt_wmlep_Q_0_1000_5f_84TeV"],
#     }
# procs["backgrounds"] = {        
#         "4t_slice2_wm": ["mgp8_pp_tttt_wmlep_Q_1000_3000_5f_84TeV"],
#         "4t_slice3_wm": ["mgp8_pp_tttt_wmlep_Q_3000_10000_5f_84TeV"],
#         "4t_slice4_wm": ["mgp8_pp_tttt_wmlep_Q_10000_84000_5f_84TeV"],
#         "4t_slice1_wp": ["mgp8_pp_tttt_wplep_Q_0_1000_5f_84TeV"],
#         "4t_slice2_wp": ["mgp8_pp_tttt_wplep_Q_1000_3000_5f_84TeV"],
#         "4t_slice3_wp": ["mgp8_pp_tttt_wplep_Q_3000_10000_5f_84TeV"],
#         "4t_slice4_wp": ["mgp8_pp_tttt_wplep_Q_10000_84000_5f_84TeV"],
#     }

# legend = {}
# legend["4t_slice1_wm"] = "4t Q 0 1000 (wm)"
# legend["4t_slice2_wm"] = "4t Q 1000 3000 (wm)"
# legend["4t_slice3_wm"] = "4t Q 3000 10000 (wm)"
# legend["4t_slice4_wm"] = "4t Q 10000 84000 (wm)"
# legend["4t_slice1_wp"] = "4t Q 0 1000 (wp)"
# legend["4t_slice2_wp"] = "4t Q 1000 3000 (wp)"
# legend["4t_slice3_wp"] = "4t Q 3000 10000 (wp)"
# legend["4t_slice4_wp"] = "4t Q 10000 84000 (wp)"


hists = {}
hists["HT_log"] = {
    "input": "HT",
    "output": "HT_log",
    "logy": True,
    "stack": True,
    "xtitle": "H_{T} [TeV]",
    "xmin": 0.5,
    "xmax": 10,
    "ymin": 1,
    #"ymax": 1e10,
    "rebin_last": True,
    "store_csv": True,
    #"yrange_syst": (-0.5,0.5),
    "ytitle": "Events / TeV",
    "processes": [
        "4t_slice1",
        "4t_slice2",
        "4t_slice3",
        "4t_slice4",
    ],
    "density": False,
    "divideByBinWidth": True,
}

hists["HT_lin"] = {
    "input": "HT",
    "output": "HT_lin",
    "logy": False,
    "stack": True,
    "xtitle": "H_{T} [TeV]",
    "xmin": 0.5,
    "xmax": 2.5,
    #"ymin": 1,
    #"ymax": 1e10,
    "rebin_last": True,
    "store_csv": True,
    "yrange_syst": (-0.5,0.5),
    "ytitle": "Events / TeV",
    "processes": [
        "4t_slice1",
        "4t_slice2",
        "4t_slice3",
        "4t_slice4",
    ],
    "density": False,
    "divideByBinWidth": True,
}

hists["HT_density"] = {
    "input": "HT",
    "output": "HT_density",
    "logy": True,
    "stack": False,
    "xtitle": "H_{T} [TeV]",
    "xmin": 0.5,
    "xmax": 10,
    "ymin": 1e-5,
    "ymax": 1,
    "rebin_last": True,
    "store_csv": True,
    "yrange_syst": (-0.5,0.5),
    "ytitle": "Events / TeV",
    "processes": [
        "4t_slice1",
        "4t_slice2",
        "4t_slice3",
        "4t_slice4",
    ],
    "density": True,
    "divideByBinWidth": True,
}

hists2D = {}
