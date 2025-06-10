import ROOT
import array

intLumi = 3e7

fraction = 1
debug = False

# check Nl in inclusive 4t 
# eemumu same sign 
# check normalizations 
# DR bparton vs lepton reco 
# check analysis without isolation 





processList = {
    'mgp8_pp_tttt_wmlep_Q_0_1000_5f_84TeV': {"fraction": fraction},
    'mgp8_pp_tttt_wmlep_Q_1000_3000_5f_84TeV': {"fraction": fraction},
    'mgp8_pp_tttt_wmlep_Q_3000_10000_5f_84TeV': {"fraction": fraction},
    'mgp8_pp_tttt_wmlep_Q_10000_84000_5f_84TeV': {"fraction": fraction},
    'mgp8_pp_tttt_wplep_Q_0_1000_5f_84TeV': {"fraction": fraction},
    'mgp8_pp_tttt_wplep_Q_1000_3000_5f_84TeV': {"fraction": fraction},
    'mgp8_pp_tttt_wplep_Q_3000_10000_5f_84TeV': {"fraction": fraction},
    'mgp8_pp_tttt_wplep_Q_10000_84000_5f_84TeV': {"fraction": fraction},


    ## 'mgp8_pp_zzzzz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_tth_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_wwz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_wzz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_zzz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_wwwz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_wwww_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_wwzz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_wzzz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_zzzz_5f_84TeV': {"fraction": fraction},    
    #'mgp8_pp_ttw_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_ttz_5f_84TeV_ttzlep': {"fraction": fraction},
    #'mgp8_pp_ttwz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_ttww_5f_84TeV': {"fraction": fraction},
    ##'mgp8_pp_ttzz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_ttzz_5f_84TeV_zzbbee': {"fraction": fraction},
    #'mgp8_pp_ttzz_5f_84TeV_zzbbmumu': {"fraction": fraction},
    #'mgp8_pp_ttzz_5f_84TeV_zzllll': {"fraction": fraction},
    ##'mgp8_pp_ttzz_5f_84TeV': {"fraction": fraction},
    #'mgp8_pp_tttt_5f_84TeV_4tlep': {"fraction": fraction},
#
    ## missing ttbar 
    #"mgp8_pp_tt_HT_2000_100000_5f_84TeV_blvblv": {"fraction": fraction},
    #"mgp8_pp_tt_HT_200_2000_5f_84TeV_blvblv": {"fraction": fraction},
    ##"mgp8_pp_tt012j_5f_84TeV": {"fraction": fraction},
    
}

# Production tag when running over EDM4Hep centrally produced events, this points to the yaml files for getting sample statistics (mandatory)
prodTag = "FCChh/fcc_v07/II/"

# Link to the dictonary that contains all the cross section informations etc... (mandatory)
procDict = "/eos/experiment/fcc/hh/utils/FCCDicts/FCChh_procDict_fcc_v07_II.json"

# Define the input dir (optional)
# inputDir    = "/eos/experiment/fcc/hh/generation/DelphesEvents/fcc_v07/II/"
# inputDir    = "./localSamples/"

# Optional: output directory, default is local running directory
outputDir = "/eos/user/m/mdefranc/FCC-hh/4t/"

# optional: ncpus, default is 4, -1 uses all cores available
nCPUS = -1

# scale the histograms with the cross-section and integrated luminosity
# doScale = True

# define some binning for various histograms
bins_count = (50, -0.5, 49.5)
bins_ht = array.array('d', [0.5, 0.75, 1, 1.5, 2.5])

# build_graph function that contains the analysis logic, cuts and histograms (mandatory)
def build_graph(df, dataset):

    results = []
    selections = []

    df = df.Define("weight", "EventHeader.weight")
    weightsum = df.Sum("weight")

    # cut 0 : all events
    df = df.Define(f"cut{len(selections)}", f"{len(selections)}")
    results.append(df.Histo1D(("cutFlow", "", *bins_count), f"cut{len(selections)}"))
    selections.append("All events")

    # select muons 
    df = df.Define("muons",  "FCCAnalyses::ReconstructedParticle::get(Muon_objIdx.index, ReconstructedParticles)") 
    df = df.Define("selpt_muons", "FCCAnalyses::ReconstructedParticle::sel_pt(30.)(muons)")
    df = df.Define("sel_muons_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_muons)")
    df = df.Define("sel_muons", "AnalysisFCChh::SortParticleCollection(sel_muons_unsort)") #sort by pT
    df = df.Define("n_muons_sel",  "FCCAnalyses::ReconstructedParticle::get_n(sel_muons)") 
    df = df.Define("pT_muons_sel",  "FCCAnalyses::ReconstructedParticle::get_pt(sel_muons)")

    # select electrons
    df = df.Define("electrons",  "FCCAnalyses::ReconstructedParticle::get(Electron_objIdx.index, ReconstructedParticles)")
    df = df.Define("selpt_electrons", "FCCAnalyses::ReconstructedParticle::sel_pt(30.)(electrons)")
    df = df.Define("sel_electrons_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_electrons)")
    df = df.Define("sel_electrons", "AnalysisFCChh::SortParticleCollection(sel_electrons_unsort)") #sort by pT
    df = df.Define("n_electrons_sel",  "FCCAnalyses::ReconstructedParticle::get_n(sel_electrons)")
    df = df.Define("pT_electrons_sel",  "FCCAnalyses::ReconstructedParticle::get_pt(sel_electrons)")

    # combine leptons
    df = df.Define("sel_leptons_unsort", "FCCAnalyses::ReconstructedParticle::merge(sel_muons, sel_electrons)")
    df = df.Define("sel_leptons", "AnalysisFCChh::SortParticleCollection(sel_leptons_unsort)") #sort by pT
    df = df.Define("pT_leptons_sel", "FCCAnalyses::ReconstructedParticle::get_pt(sel_leptons)")

    df = df.Define("n_leptons", "FCCAnalyses::ReconstructedParticle::get_n(sel_leptons)")

    # select jets
    df = df.Define(
        "b_tagged_jets_medium", "AnalysisFCChh::get_tagged_jets(Jet, Jet_HF_tags, _Jet_HF_tags_particle, _Jet_HF_tags_parameters, 1)"
    )  # bit 1 = medium WP, see: https://github.com/delphes/delphes/blob/master/cards/FCC/scenarios/FCChh_I.tcl
    # select medium b-jets with pT > 30 GeV, |eta| < 4
    df = df.Define("selpt_bjets", "FCCAnalyses::ReconstructedParticle::sel_pt(30.)(b_tagged_jets_medium)")
    df = df.Define("sel_bjets_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_bjets)")
    df = df.Define("sel_bjets", "AnalysisFCChh::SortParticleCollection(sel_bjets_unsort)")  # sort by pT
    df = df.Define("sel_bjets_pt", "FCCAnalyses::ReconstructedParticle::get_pt(sel_bjets)")
    df = df.Define("n_bjets", "FCCAnalyses::ReconstructedParticle::get_n(sel_bjets)")

    # missing ET
    df = df.Define("MET", "FCCAnalyses::ReconstructedParticle::get_pt(MissingET)")

    results.append(df.Histo1D(("n_bjets_pre", "", *bins_count), "n_bjets"))
    results.append(df.Histo1D(("n_leptons_pre", "", *bins_count), "n_leptons"))

    # ######### cut on number of bjets and leptons
    df = df.Filter("n_leptons == 4")
    df = df.Define(f"cut{len(selections)}", f"{len(selections)}")
    results.append(df.Histo1D(("cutFlow", "", *bins_count), f"cut{len(selections)}"))
    selections.append("N_{lep} == 4")

    df = df.Filter("n_bjets >= 3")
    df = df.Define(f"cut{len(selections)}", f"{len(selections)}")
    results.append(df.Histo1D(("cutFlow", "", *bins_count), f"cut{len(selections)}"))
    selections.append("N_{bjets} #geq 3")

    # calculate HT
    df = df.Define("HT", "pT_leptons_sel[0] + pT_leptons_sel[1] + pT_leptons_sel[2] + pT_leptons_sel[3] + sel_bjets_pt[0] + sel_bjets_pt[1] + sel_bjets_pt[2]")

    df = df.Define("ht_tev", "HT/1000.")

    results.append(df.Histo1D(("HT_sel", "", len(bins_ht) - 1, bins_ht), "ht_tev"))
    results.append(df.Histo1D(("MET_sel", "", 20, 0, 2000), "MET"))

    df = df.Define("find_of_ss_sf",  "AnalysisFCChh::find_of_ss_sf(sel_electrons, sel_muons)")
    df = df.Define("of_ss_sf_leptons",  "AnalysisFCChh::findOppositeFlavorSameSign(sel_electrons, sel_muons)")
    df = df.Define("n_of_ss_sf_leptons",  "FCCAnalyses::ReconstructedParticle::get_n(of_ss_sf_leptons)")
    # df = df.Filter("find_of_ss_sf")
    df = df.Filter("n_of_ss_sf_leptons == 4") 
    df = df.Define(f"cut{len(selections)}", f"{len(selections)}")
    results.append(df.Histo1D(("cutFlow", "", *bins_count), f"cut{len(selections)}"))
    selections.append("2 OF - SS pairs")

    df = df.Define("of_ss_sf_leptons_pt", "FCCAnalyses::ReconstructedParticle::get_pt(of_ss_sf_leptons)")
    df = df.Define("ele1_pt", "of_ss_sf_leptons_pt[0]")
    df = df.Define("ele2_pt", "of_ss_sf_leptons_pt[1]")
    df = df.Define("mu1_pt", "of_ss_sf_leptons_pt[2]")
    df = df.Define("mu2_pt", "of_ss_sf_leptons_pt[3]")
    df = df.Define("bjet1_pt", "sel_bjets_pt[0]")
    df = df.Define("bjet2_pt", "sel_bjets_pt[1]")
    df = df.Define("bjet3_pt", "sel_bjets_pt[2]")


    df = df.Define("wp_eleId", "(1 + AnalysisFCChh::get_weight_emugamma(ele1_pt, 2.0))*(1+AnalysisFCChh::get_weight_emugamma(ele2_pt, 2.0))")
    df = df.Define("wm_eleId", "(1 - AnalysisFCChh::get_weight_emugamma(ele1_pt, 2.0))*(1-AnalysisFCChh::get_weight_emugamma(ele2_pt, 2.0))")
    df = df.Define("wp_muId", "(1 + AnalysisFCChh::get_weight_emugamma(mu1_pt, 1.0))*(1+AnalysisFCChh::get_weight_emugamma(mu2_pt, 1.0))")
    df = df.Define("wm_muId", "(1 - AnalysisFCChh::get_weight_emugamma(mu1_pt, 1.0))*(1-AnalysisFCChh::get_weight_emugamma(mu2_pt, 1.0))")
    df = df.Define("wp_bjetId", "(1 + AnalysisFCChh::get_weight_emugamma(bjet1_pt, 3.0))*(1+AnalysisFCChh::get_weight_emugamma(bjet2_pt, 3.0))*(1+AnalysisFCChh::get_weight_emugamma(bjet3_pt, 3.0))")
    df = df.Define("wm_bjetId", "(1 - AnalysisFCChh::get_weight_emugamma(bjet1_pt, 3.0))*(1-AnalysisFCChh::get_weight_emugamma(bjet2_pt, 3.0))*(1-AnalysisFCChh::get_weight_emugamma(bjet3_pt, 3.0))")

    results.append(df.Histo1D(("HT", "", len(bins_ht) - 1, bins_ht), "ht_tev"))
    results.append(df.Histo1D(("HT_muId_wp", "", len(bins_ht) - 1, bins_ht), "ht_tev", "wp_muId"))
    results.append(df.Histo1D(("HT_muId_wm", "", len(bins_ht) - 1, bins_ht), "ht_tev", "wm_muId"))
    results.append(df.Histo1D(("HT_eleId_wp", "", len(bins_ht) - 1, bins_ht), "ht_tev", "wp_eleId"))
    results.append(df.Histo1D(("HT_eleId_wm", "", len(bins_ht) - 1, bins_ht), "ht_tev", "wm_eleId"))
    results.append(df.Histo1D(("HT_bjetId_wp", "", len(bins_ht) - 1, bins_ht), "ht_tev", "wp_bjetId"))
    results.append(df.Histo1D(("HT_bjetId_wm", "", len(bins_ht) - 1, bins_ht), "ht_tev", "wm_bjetId"))
                              

    results.append(df.Histo1D(("MET", "", 20, 0, 2000), "MET"))    

    # store selection labels dynamically in the ROOT file
    from ROOT import TObjString

    selection_str = "\n".join(selections)
    selection_obj = TObjString(selection_str)

    # Identify the cutFlow histogram and attach the object
    for obj in results:
        h = obj.GetValue()  # returns the TH1
        if h.GetName() == "cutFlow":
            h.GetListOfFunctions().Add(selection_obj)
            break

    return results, weightsum
