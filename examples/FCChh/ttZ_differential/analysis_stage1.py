"""
Ntuple production for FCC-hh analysis of top-quark pair production
"""

from argparse import ArgumentParser


fraction = 1

# Mandatory: Analysis class where the user defines the operations on the
# dataframe.
class Analysis:
    """
    differential ttbar analysis
    """

    def __init__(self, cmdline_args):
        parser = ArgumentParser(description="Additional analysis arguments", usage="Provide additional arguments after analysis script path")
        # parser.add_argument('--bjet-pt', default='10.', type=float,
        #                     help='Minimal pT of the selected b-jets.')
        # Parse additional arguments not known to the FCCAnalyses parsers
        # All command line arguments know to fccanalysis are provided in the
        # `cmdline_arg` dictionary.
        self.ana_args, _ = parser.parse_known_args(cmdline_args["unknown"])


        # Mandatory: List of processes to run over
        self.process_list = {
            'mgp8_pp_ttz_5f_84TeV_ttzlep': {"fraction": fraction, "chunks": 100},
            'mgp8_pp_tttt_5f_84TeV_4tlep': {"fraction": fraction, "chunks": 100},
            'mgp8_pp_tth_5f_84TeV': {"fraction": fraction, "chunks": 100},
                }

        # Mandatory: Input directory where to find the samples, or a production tag when running over the centrally produced
        # samples (this points to the yaml files for getting sample statistics)
        self.input_dir = "/eos/experiment/fcc/hh/generation/DelphesEvents/fcc_v07/II/"

        # Optional: output directory, default is local running directory
        self.output_dir = "/eos/user/l/lberiet/ttZ_diff_results/"
        #self.output_dir = "/eos/user/s/selvaggi/analysis/ttbar_differential_v2/"

        # Optional: analysisName, default is ''
        self.analysis_name = "FCC-hh top-quark pair analysis"

        # Optional: number of threads to run on, default is 'all available'
        self.ncpus = 16

        # Optional: running on HTCondor, default is False
        # self.run_batch = False
        self.run_batch = False

        # Optional: Use weighted events
        self.do_weighted = False 

        # Optional: read the input files with podio::DataSource
        self.use_data_source = False  # explicitly use old way in this version

        # Optional: test file that is used if you run with the --test argument
        self.test_file = "root://eospublic.cern.ch//eos/experiment/fcc/hh/" "generation/DelphesEvents/fcc_v06/II/mgp8_pp_tth01j_5f_haa/" "events_000001472.root"

    # Mandatory: analyzers function to define the analysis graph, please make
    # sure you return the dataframe, in this example it is dframe2
    def analyzers(self, dframe):
        """
        Analysis graph.
        """
        dframe2 = dframe.Define("weight", "EventHeader.weight")
        weightsum = dframe2.Sum("weight")
        print(f"Weight sum: {weightsum}")
        
        dframe2 = (
            dframe2
            ########################################### DEFINITION OF VARIABLES ###########################################
            # select muons 
            .Define("muons",  "FCCAnalyses::ReconstructedParticle::get(Muon_objIdx.index, ReconstructedParticles)") 
            .Define("selpt_muons", "FCCAnalyses::ReconstructedParticle::sel_pt(30.)(muons)")
            .Define("sel_muons_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_muons)")
            .Define("sel_muons", "AnalysisFCChh::SortParticleCollection(sel_muons_unsort)") #sort by pT
            .Define("n_muons_sel",  "FCCAnalyses::ReconstructedParticle::get_n(sel_muons)") 
            .Define("pT_muons_sel",  "FCCAnalyses::ReconstructedParticle::get_pt(sel_muons)")

            # select electrons
            .Define("electrons",  "FCCAnalyses::ReconstructedParticle::get(Electron_objIdx.index, ReconstructedParticles)")
            .Define("selpt_electrons", "FCCAnalyses::ReconstructedParticle::sel_pt(30.)(electrons)")
            .Define("sel_electrons_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_electrons)")
            .Define("sel_electrons", "AnalysisFCChh::SortParticleCollection(sel_electrons_unsort)") #sort by pT
            .Define("n_electrons_sel",  "FCCAnalyses::ReconstructedParticle::get_n(sel_electrons)")
            .Define("pT_electrons_sel",  "FCCAnalyses::ReconstructedParticle::get_pt(sel_electrons)")

            # combine leptons
            .Define("OS_ee_pairs", "AnalysisFCChh::getOSPairs(sel_muons)") 
            .Define("OS_mm_pairs", "AnalysisFCChh::getOSPairs(sel_electrons)") 
            .Define("Z_ll_candidate_unmerged", "AnalysisFCChh::getBestOSPair(OS_ee_pairs, OS_mm_pairs)") 
            .Define("Z_ll_flavor", "Z_ll_candidate_unmerged[0].flavour_flag")

            .Define('Z_ll_candidate', 'AnalysisFCChh::merge_pairs(Z_ll_candidate_unmerged)')
            .Define('Z_ll_mass', 'FCCAnalyses::ReconstructedParticle::get_mass(Z_ll_candidate)')
            .Define('Z_ll_pt', 'FCCAnalyses::ReconstructedParticle::get_pt(Z_ll_candidate)')
            .Define('Z_ll_eta', 'FCCAnalyses::ReconstructedParticle::get_eta(Z_ll_candidate)')

            .Define('dR_ll', 'AnalysisFCChh::get_angularDist_pair(Z_ll_candidate_unmerged, TString(\"dR\"))')
            # merge leptons
            .Define("sel_leptons_unsort", "FCCAnalyses::ReconstructedParticle::merge(sel_muons, sel_electrons)")
            .Define("sel_leptons", "AnalysisFCChh::SortParticleCollection(sel_leptons_unsort)") #sort by pT
            .Define("pT_leptons_sel", "FCCAnalyses::ReconstructedParticle::get_pt(sel_leptons)")

            .Define("n_leptons", "FCCAnalyses::ReconstructedParticle::get_n(sel_leptons)")

            # select jets
            .Define(
                "b_tagged_jets_medium", "AnalysisFCChh::get_tagged_jets(Jet, Jet_HF_tags, _Jet_HF_tags_particle, _Jet_HF_tags_parameters, 1)"
            )  # bit 1 = medium WP, see: https://github.com/delphes/delphes/blob/master/cards/FCC/scenarios/FCChh_I.tcl
            # select medium b-jets with pT > 30 GeV, |eta| < 4
            .Define("selpt_bjets", "FCCAnalyses::ReconstructedParticle::sel_pt(30.)(b_tagged_jets_medium)")
            .Define("sel_bjets_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_bjets)")
            .Define("sel_bjets", "AnalysisFCChh::SortParticleCollection(sel_bjets_unsort)")  # sort by pT
            .Define("sel_bjets_pt", "FCCAnalyses::ReconstructedParticle::get_pt(sel_bjets)")
            .Define("n_bjets", "FCCAnalyses::ReconstructedParticle::get_n(sel_bjets)")
            

            # missing ET
            .Define("MET", "FCCAnalyses::ReconstructedParticle::get_pt(MissingET)")

            # ######### cut on number of bjets and leptons
            #.Filter("n_leptons >= 3")
            #.Define(f"cut{len(selections)}", f"{len(selections)}")
           

            #.Filter("n_bjets == 2")
            #.Define(f"cut{len(selections)}", f"{len(selections)}")
        

            # calculate HT
            .Define("HT", "pT_leptons_sel[0] + pT_leptons_sel[1] + sel_bjets_pt[0] + sel_bjets_pt[1] + sel_bjets_pt[2]")
            .Define("ht_tev", "HT/1000.")
            .Define("recoHT", "ScalarHT")
    
        )
        return dframe2

    # Mandatory: output function, please make sure you return the branch list
    # as a python list
    def output(self):
        """
        Output variables which will be saved to output root file.
        """
        branch_list = [
            "weight",
            "n_bjets",
            "n_leptons",
            "HT",
            "ht_tev",
            "MET",
            "Z_ll_flavor",
            "Z_ll_mass",
            "Z_ll_pt",
            "Z_ll_eta",
            "dR_ll",
            "recoHT",
            
        ]
        return branch_list