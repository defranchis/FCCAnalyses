import ROOT
import os

# Load custom analyzers for ParticleID-based classification
analyzer_path = os.path.join(os.path.dirname(__file__), 'analyzers_particleid.cxx')
ROOT.gInterpreter.Declare(f'#include "{analyzer_path}"')

# define helper function to assign dummy particle IDs to reco particles
# (only to be used if the actual MC particle IDs are not available).
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<ROOT::VecOps::RVec<float>> makeDummyPIDs(
        const ROOT::VecOps::RVec<float>& charges,
        const std::vector<std::vector<int>>& constituents) {
        ROOT::VecOps::RVec<ROOT::VecOps::RVec<float>> pids;
        for (const auto& group : constituents) {
            ROOT::VecOps::RVec<float> tmp;
            for (auto idx : group) {
                int q = charges[idx];
                if (q > 0)      tmp.push_back(211);
                else if (q < 0) tmp.push_back(-211);
                else            tmp.push_back(111);
            }
            pids.push_back(tmp);
        }
        return pids;
    }""")

# helper function for deriving the event type.
# note: for now, only valid with qqbar simulations,
#       where the event type is between 1 (d dbar) and 5 (b bbar) (see PDG numbering scheme).
# note: the event type is derived simply from the first quark in the list of MCParticles;
#       there is in principle no guarantee for any kind of ordering;
#       we just assume the first quark PDG ID in the MCParticle collection
#       is the one corresponding to the type of quarks produced in the hard scattering.
#       to be checked and refined later.
# note: in the original analyzer that served as source for this one,
#       the event type needed not to be derived, as the simulation was split per quark flavour,
#       so instead the event type was just derived from the file name.
ROOT.gInterpreter.Declare("""
    int getGenEventType(
        const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles) {
        for (const auto& genParticle : genParticles) {
            int pdgid = std::abs(genParticle.PDG);
            if( (pdgid >= 1) && (pdgid <= 6) ){ return pdgid; }
        }
        return -1;
    }""")


# main analyzer class
class RDFanalysis():

    def analysers(df):
        
        df2 = (
            df

            # get MC primary vertex
            # type 1: TVector3
            #.Define("MC_PrimaryVertex", "FCCAnalyses::MCParticle::get_EventPrimaryVertex(21)( Particle )" )
            # type 2: TLorentzVector
            #.Define("MC_PrimaryVertexP4", "FCCAnalyses::MCParticle::get_EventPrimaryVertexP4()( Particle )" )

            # alternative for running on (Aleph) data: just use a dummy.
            # note: maybe later try to switch to actual reco primary vertex.
            .Define("MC_PrimaryVertexP4", "TLorentzVector(0.,0.,0.,0.)")

            # get event type (at generator level)
            .Define("genEventType", "getGenEventType(MCParticles)")

            # define the momentum, energy, mass and charge of all reconstructed particles.
            # note: in FCC simulation, the particle collection is called "RecoParticles",
            #       while in Aleph data the collection seems to be called "RecoParticles".
            .Define("RP_px",          "ReconstructedParticle::get_px(RecoParticles)")
            .Define("RP_py",          "ReconstructedParticle::get_py(RecoParticles)")
            .Define("RP_pz",          "ReconstructedParticle::get_pz(RecoParticles)")
            .Define("RP_e",           "ReconstructedParticle::get_e(RecoParticles)")
            .Define("RP_m",           "ReconstructedParticle::get_mass(RecoParticles)")
            .Define("RP_q",           "ReconstructedParticle::get_charge(RecoParticles)")
            
            # build "pseudo-jets", meaning each particle is converted to a jet
            # consisting of only that one particle (which can then be clustered in the next step)
            .Define("pseudo_jets",    "JetClusteringUtils::set_pseudoJets(RP_px, RP_py, RP_pz, RP_e)")
            # run jet clustering with the following parameters:
            # - use all reconstructed particles (in the form of the pseudo-jets defined earlier)
            # - algorithm ee_genkt
            # - R=1.5
            # - inclusive clustering
            # - E-scheme
            .Define("FCCAnalysesJets_ee_genkt", "JetClustering::clustering_ee_genkt(1.5, 0, 0, 0, 0, -1)(pseudo_jets)")
            # get the jets out of the struct
            .Define("jets_ee_genkt",           "JetClusteringUtils::get_pseudoJets(FCCAnalysesJets_ee_genkt)")
            # get the jets constituents out of the struct
            .Define("jetconstituents_ee_genkt","JetClusteringUtils::get_constituents(FCCAnalysesJets_ee_genkt)")

            # define jet-level observables
            .Define("Jets_pt", "JetClusteringUtils::get_pt(jets_ee_genkt)")
            .Define("Jets_e", "JetClusteringUtils::get_e(jets_ee_genkt)")
            .Define("Jets_mass", "JetClusteringUtils::get_m(jets_ee_genkt)")
            .Define("Jets_phi", "JetClusteringUtils::get_phi(jets_ee_genkt)")
            .Define("Jets_eta", "JetClusteringUtils::get_eta(jets_ee_genkt)")
            .Define("Jets_theta", "JetClusteringUtils::get_theta(jets_ee_genkt)")

            # define constituent-level observables
            .Define("JetsConstituents", "JetConstituentsUtils::build_constituents_cluster(RecoParticles, jetconstituents_ee_genkt)")
        
            # Extract ParticleID types for all jet constituents
            # ParticleID.type legend: 0:Track, 1:Electron, 2:Muon, 3:Track from V0, 
            #                         4:EM, 5:Ecal hadron/residual, 6:Hcal element, 7:Lcal element
            .Define("JetsConstituents_Types", "getParticleIDTypes(ParticleID, jetconstituents_ee_genkt)")
            
            # Convert the ParticleID types to binary flags for particle classification
            # Muon: type 2
            # Electron: type 1
            # Gamma: type 4 (EM)
            # Charged hadron: types 0 (Track), 3 (Track from V0)
            # Neutral hadron: types 5 (Ecal hadron/residual), 6 (Hcal element), 7 (Lcal element)
            .Define("JetsConstituents_isMu", "get_isMu_from_type(JetsConstituents_Types)")
            .Define("JetsConstituents_isEl", "get_isEl_from_type(JetsConstituents_Types)")
            .Define("JetsConstituents_isChargedHad", "get_isChargedHad_from_type(JetsConstituents_Types)")
            .Define("JetsConstituents_isGamma", "get_isGamma_from_type(JetsConstituents_Types)")
            .Define("JetsConstituents_isNeutralHad", "get_isNeutralHad_from_type(JetsConstituents_Types)")

            # kinematics, displacement, PID
            .Define("JetsConstituents_e", "JetConstituentsUtils::get_e(JetsConstituents)")
            .Define("JetsConstituents_pt", "JetConstituentsUtils::get_pt(JetsConstituents)")
            .Define("JetsConstituents_theta", "JetConstituentsUtils::get_theta(JetsConstituents)")
            .Define("JetsConstituents_phi", "JetConstituentsUtils::get_phi(JetsConstituents)")
            .Define("JetsConstituents_charge", "JetConstituentsUtils::get_charge(JetsConstituents)")

            .Define("JetsConstituents_erel", "JetConstituentsUtils::get_erel_cluster(jets_ee_genkt, JetsConstituents)")
            .Define("JetsConstituents_erel_log", "JetConstituentsUtils::get_erel_log_cluster(jets_ee_genkt, JetsConstituents)")
            .Define("JetsConstituents_thetarel", "JetConstituentsUtils::get_thetarel_cluster(jets_ee_genkt, JetsConstituents)")
            .Define("JetsConstituents_phirel", "JetConstituentsUtils::get_phirel_cluster(jets_ee_genkt, JetsConstituents)") 
            
            # note: in (Aleph) data, the collections EFlowTrack, EFlowTrack_1 and EFlowTrack_2 do not seem to exist.
            #       instead, we just use aliases and dummys and hope they are more or less equivalent...
            .Alias("EFlowTrack", "Tracks") # must be an object of type rv::RVec<edm4hep::TrackData>
            .Alias("EFlowTrack_1", "_Tracks_trackStates") # must be an object of type ROOT::VecOps::RVec<edm4hep::TrackState>
            .Define("EFlowTrack_2", "1.0 / ReconstructedParticle::get_p(RecoParticles)") # must be an object of type rv::RVec<edm4hep::Quantity>

            # continue defining kinematics
            .Define("JetsConstituents_dndx", "JetConstituentsUtils::get_dndx(JetsConstituents, EFlowTrack_2, EFlowTrack, JetsConstituents_isChargedHad)")
            #temp .Define("JetsConstituents_mtof", "JetConstituentsUtils::get_mtof(JetsConstituents, EFlowTrack_L, EFlowTrack, TrackerHits, JetsConstituents_Pids)")
            
            .Define("JetsConstituents_d0_wrt0", "JetConstituentsUtils::get_d0(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_z0_wrt0", "JetConstituentsUtils::get_z0(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_phi0_wrt0", "JetConstituentsUtils::get_phi0(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_omega_wrt0", "JetConstituentsUtils::get_omega(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_tanlambda_wrt0", "JetConstituentsUtils::get_tanLambda(JetsConstituents, EFlowTrack_1)")

            .Define("JetsConstituents_Bz", "JetConstituentsUtils::get_Bz(JetsConstituents, EFlowTrack_1)")
            .Define("Bz", "ReconstructedParticle2Track::Bz(RecoParticles, EFlowTrack_1)")
            
            .Define("JetsConstituents_dxy", "JetConstituentsUtils::XPtoPar_dxy(JetsConstituents, EFlowTrack_1, MC_PrimaryVertexP4, Bz)")
            .Define("JetsConstituents_dz", "JetConstituentsUtils::XPtoPar_dz(JetsConstituents, EFlowTrack_1, MC_PrimaryVertexP4, Bz)")
            .Define("JetsConstituents_phi0", "JetConstituentsUtils::XPtoPar_phi(JetsConstituents, EFlowTrack_1, MC_PrimaryVertexP4, Bz)")
            .Define("JetsConstituents_C", "JetConstituentsUtils::XPtoPar_C(JetsConstituents, EFlowTrack_1, Bz)")
            .Define("JetsConstituents_ct", "JetConstituentsUtils::XPtoPar_ct(JetsConstituents, EFlowTrack_1, Bz)")

            .Define("JetsConstituents_omega_cov", "JetConstituentsUtils::get_omega_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_d0_cov", "JetConstituentsUtils::get_d0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_z0_cov", "JetConstituentsUtils::get_z0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_phi0_cov", "JetConstituentsUtils::get_phi0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_tanlambda_cov", "JetConstituentsUtils::get_tanlambda_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_d0_z0_cov", "JetConstituentsUtils::get_d0_z0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_phi0_d0_cov", "JetConstituentsUtils::get_phi0_d0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_phi0_z0_cov", "JetConstituentsUtils::get_phi0_z0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_tanlambda_phi0_cov", "JetConstituentsUtils::get_tanlambda_phi0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_tanlambda_d0_cov", "JetConstituentsUtils::get_tanlambda_d0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_tanlambda_z0_cov", "JetConstituentsUtils::get_tanlambda_z0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_omega_tanlambda_cov", "JetConstituentsUtils::get_omega_tanlambda_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_omega_phi0_cov", "JetConstituentsUtils::get_omega_phi0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_omega_d0_cov", "JetConstituentsUtils::get_omega_d0_cov(JetsConstituents, EFlowTrack_1)")
            .Define("JetsConstituents_omega_z0_cov", "JetConstituentsUtils::get_omega_z0_cov(JetsConstituents, EFlowTrack_1)")
            
            .Define("JetsConstituents_Sip2dVal", "JetConstituentsUtils::get_Sip2dVal_clusterV(jets_ee_genkt, JetsConstituents_dxy, JetsConstituents_phi0, Bz)")
            .Define("JetsConstituents_Sip2dSig", "JetConstituentsUtils::get_Sip2dSig(JetsConstituents_Sip2dVal, JetsConstituents_d0_cov)")
            .Define("JetsConstituents_Sip3dVal", "JetConstituentsUtils::get_Sip3dVal_clusterV(jets_ee_genkt, JetsConstituents_dxy, JetsConstituents_dz, JetsConstituents_phi0, Bz)")
            .Define("JetsConstituents_Sip3dSig", "JetConstituentsUtils::get_Sip3dSig(JetsConstituents_Sip3dVal, JetsConstituents_d0_cov, JetsConstituents_z0_cov)")
            .Define("JetsConstituents_JetDistVal", "JetConstituentsUtils::get_JetDistVal_clusterV(jets_ee_genkt, JetsConstituents, JetsConstituents_dxy, JetsConstituents_dz, JetsConstituents_phi0, Bz)")
            .Define("JetsConstituents_JetDistSig", "JetConstituentsUtils::get_JetDistSig(JetsConstituents_JetDistVal, JetsConstituents_d0_cov, JetsConstituents_z0_cov)")

            # counting the types of particles per jet
            .Define("njet", "JetConstituentsUtils::count_jets(JetsConstituents)")
            .Define("nconst", "JetConstituentsUtils::count_consts(JetsConstituents)")
            .Define("nmu", "JetConstituentsUtils::count_type(JetsConstituents_isMu)")
            .Define("nel", "JetConstituentsUtils::count_type(JetsConstituents_isEl)")
            .Define("nchargedhad", "JetConstituentsUtils::count_type(JetsConstituents_isChargedHad)")
            .Define("nphoton", "JetConstituentsUtils::count_type(JetsConstituents_isGamma)")
            .Define("nneutralhad", "JetConstituentsUtils::count_type(JetsConstituents_isNeutralHad)")
        
            # compute the residues jet-constituents on significant kinematic variables as a check
            # notes:
            # - "tlv_jets" seems to mean: "the lorentz vectors of the jets, calculated directly from the jets"
            # - "sum_tlv_jcs" seems to mean: "the lorentz vectors of the jets, but calculated by summing all constituents"
            .Define("tlv_jets", "JetConstituentsUtils::compute_tlv_jets(jets_ee_genkt)")
            .Define("sum_tlv_jcs", "JetConstituentsUtils::sum_tlv_constituents(JetsConstituents)")
            .Define("de", "JetConstituentsUtils::compute_residue_energy(tlv_jets, sum_tlv_jcs)")
            .Define("dpt", "JetConstituentsUtils::compute_residue_pt(tlv_jets, sum_tlv_jcs)")
            .Define("dphi", "JetConstituentsUtils::compute_residue_phi(tlv_jets, sum_tlv_jcs)")
            .Define("dtheta", "JetConstituentsUtils::compute_residue_theta(tlv_jets, sum_tlv_jcs)")
            
            .Define("invariant_mass", "JetConstituentsUtils::InvariantMass(tlv_jets[0], tlv_jets[1])")
        )
        return df2

    def output():
        branchList = [
            # event-level variables
            'genEventType',
            'njet',
            'nconst',
            'nmu', 'nel', 'nchargedhad', 'nphoton', 'nneutralhad',
            'de', 'dpt', 'dphi', 'dtheta',
            'invariant_mass',
            
            # jet-level variables
            'Jets_e', 'Jets_mass', 'Jets_pt', 'Jets_phi', 'Jets_eta', 'Jets_theta',
            
            # jet-constituent-level variables
            'JetsConstituents_e', 'JetsConstituents_pt',
            'JetsConstituents_theta', 'JetsConstituents_phi',
            'JetsConstituents_charge',
            'JetsConstituents_erel', 'JetsConstituents_erel_log',
            'JetsConstituents_thetarel', 'JetsConstituents_phirel', 
            'JetsConstituents_dndx',
            #temp 'JetsConstituents_mtof',
            
            'JetsConstituents_d0_wrt0', 'JetsConstituents_z0_wrt0', 'JetsConstituents_phi0_wrt0', 'JetsConstituents_omega_wrt0', 'JetsConstituents_tanlambda_wrt0',
            'Bz', 'JetsConstituents_Bz',
            'JetsConstituents_dxy', 'JetsConstituents_dz', 'JetsConstituents_phi0',
            'JetsConstituents_C', 'JetsConstituents_ct',

            'JetsConstituents_omega_cov', 'JetsConstituents_d0_cov', 'JetsConstituents_z0_cov', 'JetsConstituents_phi0_cov', 'JetsConstituents_tanlambda_cov',
            'JetsConstituents_d0_z0_cov', 'JetsConstituents_phi0_d0_cov', 'JetsConstituents_phi0_z0_cov', 
            'JetsConstituents_tanlambda_phi0_cov', 'JetsConstituents_tanlambda_d0_cov', 'JetsConstituents_tanlambda_z0_cov', 
            'JetsConstituents_omega_tanlambda_cov', 'JetsConstituents_omega_phi0_cov', 'JetsConstituents_omega_d0_cov', 'JetsConstituents_omega_z0_cov', 
            'JetsConstituents_Sip2dVal',
            'JetsConstituents_Sip2dSig', 
            'JetsConstituents_Sip3dVal',
            'JetsConstituents_Sip3dSig', 
            'JetsConstituents_JetDistVal',
            'JetsConstituents_JetDistSig',
            'JetsConstituents_isMu', 
            'JetsConstituents_isEl', 
            'JetsConstituents_isChargedHad',
            'JetsConstituents_isGamma', 
            'JetsConstituents_isNeutralHad',
        ]
        return branchList    
