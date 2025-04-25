"""
Ntuple production for FCC-hh analysis of top-quark pair production
"""

from argparse import ArgumentParser


fraction = 0.01

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
            "mgp8_pp_tt_HT_2000_100000_5f_84TeV": {"fraction": fraction},
            "mgp8_pp_tt_HT_200_2000_5f_84TeV": {"fraction": fraction},
        }

        # Mandatory: Input directory where to find the samples, or a production tag when running over the centrally produced
        # samples (this points to the yaml files for getting sample statistics)
        self.input_dir = "/eos/experiment/fcc/hh/generation/DelphesEvents/fcc_v07/II/"

        # Optional: output directory, default is local running directory
        self.output_dir = "/eos/experiment/fcc/hh/analysis_ntuples/fcc_v06/II/ttbar_differential_v2/"
        self.output_dir = "/eos/user/s/selvaggi/analysis/ttbar_differential_v2/"

        # Optional: analysisName, default is ''
        self.analysis_name = "FCC-hh top-quark pair analysis"

        # Optional: number of threads to run on, default is 'all available'
        self.ncpus = 48

        # Optional: running on HTCondor, default is False
        # self.run_batch = False
        self.run_batch = False

        # Optional: Use weighted events
        self.do_weighted = True

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

        dframe2 = (
            dframe
            ########################################### DEFINITION OF VARIABLES ###########################################
            # generator event weight
            .Define("weight", "EventHeader.weight")

            ########################################### JETS ###########################################
            # selected jets above a pT threshold of 500 GeV, eta < 4
            .Define("selpt_jets", "FCCAnalyses::ReconstructedParticle::sel_pt(500.)(Jet)")
            .Define("sel_jets_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_jets)")
            .Define("sel_jets", "AnalysisFCChh::SortParticleCollection(sel_jets_unsort)")
            .Define("n_jets",  "FCCAnalyses::ReconstructedParticle::get_n(sel_jets)")
            .Define("jet1",  "sel_jets[0]")
            .Define("jet2",  "sel_jets[1]")
            .Define("jet1_tlv", "AnalysisFCChh::getTLV_reco(jet1)")
            .Define("jet2_tlv", "AnalysisFCChh::getTLV_reco(jet2)")
            .Define("jet1_pt", "jet1_tlv.Pt()")
            .Define("jet2_pt", "jet2_tlv.Pt()")
            .Define("jet1_eta", "jet1_tlv.Eta()")
            .Define("jet2_eta", "jet2_tlv.Eta()")
            .Define("jet1_phi", "jet1_tlv.Phi()")
            .Define("jet2_phi", "jet2_tlv.Phi()")
            .Define("mjj", "(jet1_tlv + jet2_tlv).M()")
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
            "n_jets",
            "jet1_pt",
            "jet2_pt",
            "jet1_eta",
            "jet2_eta",
            "jet1_phi",
            "jet2_phi",
            "mjj",
        ]
        return branch_list
