import ROOT

L = 30
energy = 84
# global parameters
intLumi = 1.0
intLumiLabel = f"L = {L} ab^{{-1}}"
ana_tex = ""
delphesVersion = "3.4.2"
collider = "FCC-hh"
formats = ["pdf"]

# outdir         = './outputs/plots/recoil/'
outdir = "/eos/user/s/selvaggi/www/analysis/tttt_v3/"
inputDir = "/eos/user/s/selvaggi/analysis/tttt_v3/"

plotStatUnc = True

# Define custom colors using RGB values
custom = [
    (213, 62, 79),  # red 0
    (253, 174, 97),  # orange 1
    (254, 224, 144),  # yellow 2
    (230, 245, 152),  # yg 3
    (26, 152, 80),  # green 4
    (50, 136, 189),  # blue 5
    (208, 28, 139),  # pink 6
    (241, 182, 218),  # light pink 7
    (128, 205, 193),  # light blue 8
    (1, 133, 113),  # blue green 9
]

# Create custom ROOT colors and store their indices
custom_color_indices = []
for i, (r, g, b) in enumerate(custom):
    color_index = 2000 + i  # Use indices starting from 2000 to avoid conflicts with ROOT's default colors
    ROOT.gROOT.ProcessLine(f"new TColor({color_index}, {r/255.0}, {g/255.0}, {b/255.0})")
    custom_color_indices.append(color_index)

colors = {}
colors["tttt"] = ROOT.kBlack
colors["VVV"] = custom_color_indices[1]
colors["VVVV"] = custom_color_indices[2]
colors["ttV"] = custom_color_indices[3]
colors["ttVV"] = custom_color_indices[4]
colors["ttH"] = custom_color_indices[5]
colors["tt"] = custom_color_indices[6]

procs = {}

# 'mgp8_pp_tth_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_wwz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_wzz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_zzz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_wwwz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_wwww_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_wwzz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_wzzz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_zzzz_5f_84TeV': {"fraction": fraction},    
# 'mgp8_pp_ttw_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_ttz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_ttwz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_ttww_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_ttzz_5f_84TeV': {"fraction": fraction},
# 'mgp8_pp_tttt_5f_84TeV': {"fraction": fraction},

procs["signal"] = {
    "tttt": ["mgp8_pp_tttt_5f_84TeV_4tlep"],
    }
procs["backgrounds"] = {
    "VVV": ["mgp8_pp_wwz_5f_84TeV", "mgp8_pp_wzz_5f_84TeV", "mgp8_pp_zzz_5f_84TeV"],
    "VVVV": ["mgp8_pp_wwwz_5f_84TeV", "mgp8_pp_wwww_5f_84TeV", "mgp8_pp_wwzz_5f_84TeV", "mgp8_pp_wzzz_5f_84TeV", "mgp8_pp_zzzz_5f_84TeV"],
    "ttV": ["mgp8_pp_ttw_5f_84TeV", "mgp8_pp_ttz_5f_84TeV_ttzlep"],
    "ttVV": ["mgp8_pp_ttwz_5f_84TeV", "mgp8_pp_ttww_5f_84TeV", "mgp8_pp_ttzz_5f_84TeV_zzbbee", "mgp8_pp_ttzz_5f_84TeV_zzbbmumu", "mgp8_pp_ttzz_5f_84TeV_zzllll"],
    "ttH": ["mgp8_pp_tth_5f_84TeV"],
    "tt": ["mgp8_pp_tt_HT_2000_100000_5f_84TeV_blvblv", "mgp8_pp_tt_HT_200_2000_5f_84TeV_blvblv"],
    }

legend = {}
legend["tttt"] = "tttt"
legend["VVV"] = "VVV"
legend["VVVV"] = "VVVV"
legend["ttV"] = "ttV"
legend["ttVV"] = "ttVV"
legend["ttH"] = "ttH"
legend["tt"] = "tt"

hists = {}
hists2D = {}


hists["cutFlow"] = {
    "input": "cutFlow",
    "output": "cutFlow",
    "logy": True,
    "stack": False,
    # "xmin": -0.5,
    # "xmax": 2.5,
    # "xtitle": selections,
    "ytitle": "Events",
    "processes": ["tttt", "VVV", "VVVV", "ttV", "ttVV", "ttH", "tt"],
}


hists["n_bjets_pre_stack"] = {
    "input": "n_bjets_pre",
    "output": "n_bjets_pre_stack",
    "logy": True,
    "stack": False,
    "xtitle": "N_{bjets}",
    "xmin": -0.5,
    "xmax": 10.5,
    "ytitle": "Events",
    "processes": ["tttt", "VVV", "VVVV", "ttV", "ttVV", "ttH", "tt"],
    "density": False,
}

hists["n_leptons_pre_stack"] = {
    "input": "n_leptons_pre",
    "output": "n_leptons_pre_stack",
    "logy": True,
    "stack": False,
    "xtitle": "N_{leptons}",
    "xmin": -0.5,
    "xmax": 10.5,
    "ytitle": "Events",
    "processes": ["tttt", "VVV", "VVVV", "ttV", "ttVV", "ttH", "tt"],
    "density": False,
}

hists["n_bjets_pre_norm"] = {
    "input": "n_bjets_pre",
    "output": "n_bjets_pre_norm",
    "logy": False,
    "stack": False,
    "xtitle": "N_{bjets}",
    "xmin": -0.5,
    "xmax": 10.5,
    "ytitle": "Events",
    "processes": ["tttt", "VVV", "VVVV", "ttV", "ttVV", "ttH", "tt"],
    "density": True,
}

hists["n_leptons_pre_norm"] = {
    "input": "n_leptons_pre",
    "output": "n_leptons_pre_norm",
    "logy": False,
    "stack": False,
    "xtitle": "N_{leptons}",
    "xmin": -0.5,
    "xmax": 10.5,
    "ytitle": "Events",
    "processes": ["tttt", "VVV", "VVVV", "ttV", "ttVV", "ttH", "tt"],
    "density": True,
}


hists["MET_stack"] = {
    "input": "MET_sel",
    "output": "MET_stack",
    "logy": True,
    "stack": False,
    "xtitle": "E_{T}^{miss} [GeV]",
    "xmin": 0,
    "xmax": 1000,
    "ytitle": "Events",
    "processes": ["tttt", "VVV", "VVVV", "ttV", "ttVV", "ttH", "tt"],
    "density": False,
}

hists["MET_norm"] = {
    "input": "MET_sel",
    "output": "MET_norm",
    "logy": False,
    "stack": False,
    "xtitle": "E_{T}^{miss} [GeV]",
    "xmin": 0,
    "xmax": 1000,
    "ytitle": "Events",
    "processes": ["tttt", "ttV", "ttVV", "ttH"],
    "density": True,
}

hists["HT_sel_stack"] = {
    "input": "HT_sel",
    "output": "HT_sel_stack",
    "logy": True,
    "stack": False,
    "xtitle": "H_{T} [TeV]",
    "xmin": 0.5,
    "xmax": 2.5,
    "ymin": 1,
    "ymax": 1e6,
    "rebin_last": True,
    "store_csv": True,
    "yrange_syst": (-0.5,0.5),
    "ytitle": "Events / TeV",
    "processes": ["tttt", "VVV", "VVVV", "ttV", "ttVV", "ttH", "tt"],
    "density": False,
    "divideByBinWidth": True,
}

hists["HT_stack"] = {
    "input": "HT",
    "output": "HT_stack",
    "logy": True,
    "stack": False,
    "xtitle": "H_{T} [TeV]",
    "xmin": 0.5,
    "xmax": 2.5,
    "ymin": 1,
    "ymax": 1e7,
    "ytitle": "Events / TeV",
    "processes": ["tttt", "VVV", "VVVV", "ttV", "ttVV", "ttH", "tt"],
    "density": False,
    "divideByBinWidth": True,
    "rebin_last": True,
    "store_csv": True,
    "yrange_syst": (-0.5,0.5),
    "systematics": [
    {
        "signal": True,
        "process": "tttt",
        "label": "muon id",
        "type": "shape",
        "hname": "muId",
        "color": custom_color_indices[7],            
    },
    {
        "signal": True,
        "process": "tttt",
        "label": "electron id",
        "type": "shape",
        "hname": "eleId",
        "color": custom_color_indices[8],            
    },
    {
        "signal": True,
        "process": "tttt",
        "label": "bjet id",
        "type": "shape",
        "hname": "bjetId",
        "color": custom_color_indices[9],            
    },    
    {
        "signal": True,
        "process": "tttt",
        "label": "luminosity",
        "type": "const",
        "value": 0.01,
        "color": custom_color_indices[1],            
    },

    ]       
}


hists["HT_norm"] = {
    "input": "HT_sel",
    "output": "HT_norm",
    "logy": False,
    "stack": False,
    "xtitle": "H_{T} [TeV]",
    "xmin": 0,
    "xmax": 5,
    "ytitle": "Events",
    "processes": ["tttt", "ttV", "ttVV", "ttH"],
    "density": True,
}


