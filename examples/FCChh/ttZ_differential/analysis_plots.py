import ROOT

# plot the mumu bkg sample in the separate HT slices

# global parameters
intLumi = 30e+06  # in pb-1
ana_tex = "pp #rightarrow ttZ analysis "
delphesVersion = "3.4.2"
energy = 84
collider = "FCC-hh"
inputDir = "/eos/user/l/lberiet/ttZ_diff_results/final"
formats = ["png"]
# formats        = ['png','pdf']
# yaxis          = ['log']
yaxis = ["lin", "log"]
# stacksig       = ['stack']
stacksig = [ "nostack"]
outdir = "/eos/user/l/lberiet/ttZ_diff_results/plots/"
plotStatUnc = True



variables = ['Z_ll_mass', 'dR_ll', 'n_bjets', 'n_leptons', 'HT', 'MET', 'recoHT']


# rebin = [1, 1, 1, 1, 2] # uniform rebin per variable (optional)

### Dictionary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection
selections = {}
selections["ttZ_diff_analysis"] = ["sel1", "sel2_lep", "sel3_jets"]

extralabel = {}
extralabel["sel1"] = "No Selection"
extralabel["sel2_lep"] = "Sel 3 leptons"
extralabel["sel3_jets"] = "Sel 2 b-jets"

colors = {}
colors["tt_Z_signal"] = ROOT.kRed
colors["4t_bkg"] = ROOT.kBlue
colors["ttH_bkg_lep"] = ROOT.kGreen 


procs = {}
procs["signal"] = {
    "tt_Z_signal": ["mgp8_pp_ttz_5f_84TeV_ttzlep_sel1_histo", "mgp8_pp_ttz_5f_84TeV_ttzlep_sel2_lep_histo", "mgp8_pp_ttz_5f_84TeV_ttzlep_sel3_jets_histo"]
}
procs["backgrounds"] = {
    "4t_bkg": ["mgp8_pp_tttt_5f_84TeV_4tlep_sel1_histo", "mgp8_pp_tttt_5f_84TeV_4tlep_sel2_lep_histo", "mgp8_pp_tttt_5f_84TeV_4tlep_sel3_jets_histo"],
    "ttH_bkg_lep": ["mgp8_pp_tth_5f_84TeV_sel1_histo", "mgp8_pp_tth_5f_84TeV_sel2_lep_histo", "mgp8_pp_tth_5f_84TeV_sel3_jets_histo"]
}

legend = {}
legend["tt_Z_signal"] = "ttZ"
legend["4t_bkg"] = "4t"
legend["ttH_bkg_lep"] = "ttH"

hists = {}
for var in variables:
    hists[var] = {
        "input": var,
        "output": var,
        "logy": True,
        "stack": True,
        "xtitle": var,
        "rebin_last": True,
        "store_csv": True,
        "ytitle": "Events",
        "processes": [
            "tt_Z_signal",
            "4t_bkg",
            "ttH_bkg_lep"
        ],
        "density": False,
        "divideByBinWidth": True,
    }

hists2D = {}


