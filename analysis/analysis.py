import os
import sys
import ROOT

# load custom analyzer for particle ID retrieval
analyzer_path = os.path.join(os.path.dirname(__file__), 'analyzers', 'analyzer_particleid.cxx')
ROOT.gInterpreter.Declare(f'#include "{analyzer_path}"')

# helper function for deriving the gen-level event type.
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
    int get_genEventType(
        const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles) {
        for (const auto& genParticle : genParticles) {
            int pdgid = std::abs(genParticle.PDG);
            if( (pdgid >= 1) && (pdgid <= 6) ){ return pdgid; }
        }
        return -1;
    }""")

# helper function for deriving the reco-level event type.
# for more info on the class bitset encoding this information,
# see here: https://aleph-new.docs.cern.ch/eos/1994-data/
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<unsigned int> get_recoEventType(
        ROOT::VecOps::RVec<unsigned int> classBitsetInt) {
        std::bitset<32> classBitset = std::bitset<32>(classBitsetInt[0]);
        ROOT::VecOps::RVec<unsigned int> res;
        for(unsigned int shift=0; shift<32; shift++){
            if(classBitset[shift]){ res.push_back(shift+1); }
        }
        return res;
    }""")

# helper function for making a dummy RecoParticle-to-Tracks linking collection.
# this is needed for syntax in case the linking collection does not exist,
# and the linking between RecoParticles and Tracks is direct.
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<podio::ObjectID> makeDummyRecoToTracks(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps){
        ROOT::VecOps::RVec<podio::ObjectID> links;
        links.reserve(rps.size());
        for (size_t i = 0; i < rps.size(); ++i) {
            const auto& rp = rps[i];
            podio::ObjectID oid;
            oid.index = rp.tracks_begin;
            oid.collectionID = 0;
            links.push_back(oid);
        }
        return links;
    }""")

# helper function to retrieve a vertex from the collection of vertices
# in the correct TLorentzVector format.
# note: not clear how to distinguish primary from secondary vertices,
#       this code just relies on the fact that >99% of events (in simulation) have exactly one vertex stored.
# note: what to do in case no vertex is stored for an event?
#       for now just use the dummy of (0, 0, 0) in those cases.
ROOT.gInterpreter.Declare("""
    TLorentzVector getRecoPrimaryVertex(
        ROOT::VecOps::RVec<FCCAnalyses::VertexingUtils::FCCAnalysesVertex> vertexCollection){
        edm4hep::VertexData vertex;
        TLorentzVector result = {0., 0., 0., 0.};
        if( vertexCollection.size() == 0 ){ return result; }
        vertex = vertexCollection.at(0).vertex;
        result = {vertex.position.x, vertex.position.y, vertex.position.z, 0.};
        return result;
    }""")

# helper function to re-calculate the primary vertex from the collection of tracks.
# note: experimental; runs but not yet thoroughly tested.
ROOT.gInterpreter.Declare("""
    TLorentzVector fitRecoPrimaryVertex(
        ROOT::VecOps::RVec<edm4hep::TrackState> tracks){
        ROOT::VecOps::RVec<edm4hep::TrackState> tracksToUse;
        for(const auto& track: tracks){
            //if( std::abs(track.omega) < 0.015 ){ continue; }
            tracksToUse.push_back(track);
        }
        TLorentzVector result = {0., 0., 0., 0.};
        if( tracksToUse.size() < 5 ){ return result; }
        FCCAnalyses::VertexingUtils::FCCAnalysesVertex fitresult = FCCAnalyses::VertexFitterSimple::VertexFitter_Tk(0, tracksToUse);
        edm4hep::VertexData vertex = fitresult.vertex;
        result = {vertex.position.x, vertex.position.y, vertex.position.z, 0.};
        return result;
    }""")

# helper function to get the MC truth-level primary vertex from the first gen-particle.
# note: relies on the assumption that the vertex stored for the first gen-particle is the PV.
ROOT.gInterpreter.Declare("""
    TLorentzVector getMCPV(
        const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles) {
        TLorentzVector result = {0, 0, 0, 0};
        if( genParticles.size() < 1 ){ return result; }
        result = {genParticles[0].vertex.x, genParticles[0].vertex.y, genParticles[0].vertex.z, 0.};
        return result;
    }""")

# helper function to make dummy jet constituent variables
# (e.g. for variables that are available for aleph but not for fcc or the other way round)
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<ROOT::VecOps::RVec<float>> makeDummyJetConstituentVariable(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>>& jcs, float dummyValue){
        ROOT::VecOps::RVec<ROOT::VecOps::RVec<float>> out;
        for (const auto &jc : jcs){
            ROOT::VecOps::RVec<float> temp;
            for (const auto &el : jc){
                temp.emplace_back(dummyValue);
            }
            out.emplace_back(temp);
        }
        return out;
    }""")


# main analyzer class
class RDFanalysis():

    def analysers(df):

        # initialization
        dfout = df

        # automatically determine detector type based on the presence of some branches
        # (maybe make more robust later)
        det = None
        try:
            df.Alias("_", "ReconstructedParticles")
            det = 'fcc'
        except: pass
        try:
            df.Alias("_", "RecoParticles")
            det = 'aleph'
        except: pass
        if det is None:
            raise Exception('Could not determine detector type.')

        # automatically determine data type based on the presence of some branches
        # (maybe make more robust later)
        dtype = 'data'
        try:
            if det=='fcc': df.Alias("_", "Particle")
            if det=='aleph': df.Alias("_", "MCParticles")
            dtype = 'sim'
        except: pass

        # for Aleph simulation, the collection of MC particles is called "MCParticles",
        # while for FCC simulation it is called "Particle", so define an alias here.
        # and same for "RecoParticles" vs "ReconstructedParticles".
        # and same for "ParticleID" vs "ParticleIDs" (note: not well defined for FCC).
        if det=='aleph':
            if dtype=='sim': dfout = dfout.Alias("Particle", "MCParticles")
            dfout = dfout.Alias("ReconstructedParticles", "RecoParticles")
            dfout = dfout.Alias("ParticleIDs", "ParticleID")

        # for Aleph simulation, the collections EFlowTrack, EFlowTrack_1 and EFlowTrack_2 do not seem to exist,
        # so we need to alias them with other collections.
        # note: the alias for EFlowTrack_2 has not yet been validated, no guarantee that it is correct.
        if det=='aleph':
            dfout = (
                dfout

                .Alias("EFlowTrack", "Tracks")
                # (must be an object of type rv::RVec<edm4hep::TrackData>)
                .Alias("EFlowTrack_1", "_Tracks_trackStates")
                # (must be an object of type ROOT::VecOps::RVec<edm4hep::TrackState>)
                .Define("EFlowTrack_2", "1.0 / ReconstructedParticle::get_p(ReconstructedParticles)")
                # (must be an object of type rv::RVec<edm4hep::Quantity>)
            )

        # for Aleph simulation, the link between RecoParticles and Tracks is indirect,
        # via an intermediate collection _RecoParticles_tracks;
        # for FCC simulation, we must define it as a transparent mapping for the syntax
        if det=='aleph': dfout = dfout.Alias("Reco2TrackLinks", "_RecoParticles_tracks")
        elif det=='fcc': dfout = dfout.Define("Reco2TrackLinks", "makeDummyRecoToTracks(ReconstructedParticles)")

        # do gen-level stuff
        if dtype=='sim':
            dfout = (
                dfout
                
                # store the pdg ID and generator status for all generator particles
                # (mainly for debugging)
                .Define("GenParticle_pdgId", "MCParticle::get_pdg(Particle)")
                .Define("GenParticle_genStatus", "MCParticle::get_genStatus(Particle)")

                # get event type (at generator level)
                .Define("genEventType", "get_genEventType(Particle)")

                # get true primary vertex position
                .Define("GenPrimaryVertexP4", "getMCPV(Particle)")
                .Define("GenPV_x", "GenPrimaryVertexP4.X()")
                .Define("GenPV_y", "GenPrimaryVertexP4.Y()")
                .Define("GenPV_z", "GenPrimaryVertexP4.Z()")
            )
        else:
            # set dummies (maybe later find out how to avoid the need for this)
            dfout = (
                dfout
                .Define("GenParticle_pdgId", "0")
                .Define("GenParticle_genStatus", "0")
                .Define("genEventType", "-1")
                .Define("GenPV_x", "-1")
                .Define("GenPV_y", "-1")
                .Define("GenPV_z", "-1")
            )

        # do reco-level event type
        # (only well-defined for Aleph, put a dummy for FCC)
        if det=='aleph':
            dfout = dfout.Define("recoEventType", "get_recoEventType(ClassBitset)")
        elif det=='fcc':
            dfout = dfout.Define("recoEventType", "-1")

        # do the actual analysis
        dfout = (
            dfout

            # get MC primary vertex
            #.Define("PrimaryVertexP4", "FCCAnalyses::MCParticle::get_EventPrimaryVertexP4()(Particle)")

            # alternative: get MC primary vertex from first particle in list of gen particles
            #.Define("PrimaryVertexP4", "getMCPV(Particle)")

            # alternative for running on data: just use a dummy.
            # note: maybe later try to switch to actual reco primary vertex.
            #.Define("PrimaryVertexP4", "TLorentzVector(0.,0.,0.,0.)")

            # alternative for running on data or circumventing other issues with the MC primary vertex:
            # use reco primary vertex.
            # note: not sure how to make this work for FCC sim; there doesn't seem to be an equivalent collection.
            .Define("PrimaryVertexP4", "getRecoPrimaryVertex(Vertices)")
            
            # alternative: recalculate reco primary vertex
            #.Define("PrimaryVertexP4", "fitRecoPrimaryVertex(EFlowTrack_1)")

            # store the primary vertex coordinates
            # (mainly for debugging)
            .Define("PV_x", "PrimaryVertexP4.X()")
            .Define("PV_y", "PrimaryVertexP4.Y()")
            .Define("PV_z", "PrimaryVertexP4.Z()")

            # temp for testing
            #.Redefine("PrimaryVertexP4", "TLorentzVector(GenPV_x, GenPV_y, GenPV_z, 0)")

            # define the momentum, energy, mass and charge of all reconstructed particles.
            .Define("RP_px",          "ReconstructedParticle::get_px(ReconstructedParticles)")
            .Define("RP_py",          "ReconstructedParticle::get_py(ReconstructedParticles)")
            .Define("RP_pz",          "ReconstructedParticle::get_pz(ReconstructedParticles)")
            .Define("RP_e",           "ReconstructedParticle::get_e(ReconstructedParticles)")
            .Define("RP_m",           "ReconstructedParticle::get_mass(ReconstructedParticles)")
            .Define("RP_q",           "ReconstructedParticle::get_charge(ReconstructedParticles)")
            
            # build "pseudo-jets", meaning each particle is converted to a jet
            # consisting of only that one particle (which can then be clustered in the next step)
            .Define("pseudo_jets",    "JetClusteringUtils::set_pseudoJets(RP_px, RP_py, RP_pz, RP_e)")
            # run jet clustering
            # note: the JetClustering namespace with its functions is defined here:
            #       FCCAnalyses/addons/FastJet/src/JetClustering.cc.
            # note: the arguments are (in order):
            # - radius: jet radius (typically 1.5)
            # - exclusive: inclusive or exclusive clustering.
            #   "inclusive" = variable number of jets, fixed radius.
            #   "exclusive" = fixed number of jets (typically 2, i.e. hemispheres), variable radius.
            #   in the case of exclusive clustering, the jet radius argument is ignored (?).
            #   use 0 for inclusive clustering, 1 or 2 for exclusive clustering (?)
            #   (see FCCAnalyses/analyzers/dataframe/src/JetClusteringUtils.cc / build_jets)
            # - cut: seems to be a pt threshold for inclusive clustering,
            #   and the number of jets in exclusive clustering (?)
            #   (see FCCAnalyses/analyzers/dataframe/src/JetClusteringUtils.cc / build_jets)
            #   (see https://fastjet.fr/repo/doxygen-3.0.0/classfastjet_1_1ClusterSequence.html)
            # - sorted: sorting method (leave at default 0).
            # - recombination: how jets are summed (leave at default 0).
            # - exponent (of kT algorithm, typically -1, i.e. anti-kT).
            .Define("FCCAnalysesJets_ee_genkt", "JetClustering::clustering_ee_genkt(1.5, 0, 0, 0, 0, -1)(pseudo_jets)") # inclusive
            #.Define("FCCAnalysesJets_ee_genkt", "JetClustering::clustering_ee_genkt(1.5, 3, 2, 0, 0, -1)(pseudo_jets)") # exclusive
            # get the jets out of the struct
            .Define("jets_ee_genkt", "JetClusteringUtils::get_pseudoJets(FCCAnalysesJets_ee_genkt)")
            # get the jets constituents out of the struct
            .Define("jetconstituents_ee_genkt", "JetClusteringUtils::get_constituents(FCCAnalysesJets_ee_genkt)")

            # define jet-level observables
            .Define("Jets_pt", "JetClusteringUtils::get_pt(jets_ee_genkt)")
            .Define("Jets_e", "JetClusteringUtils::get_e(jets_ee_genkt)")
            .Define("Jets_mass", "JetClusteringUtils::get_m(jets_ee_genkt)")
            .Define("Jets_phi", "JetClusteringUtils::get_phi(jets_ee_genkt)")
            .Define("Jets_eta", "JetClusteringUtils::get_eta(jets_ee_genkt)")
            .Define("Jets_theta", "JetClusteringUtils::get_theta(jets_ee_genkt)")
            .Define("Jets_p4", "JetConstituentsUtils::compute_tlv_jets(jets_ee_genkt)")

            # define event-level properties
            .Define("Event_mass", "JetConstituentsUtils::InvariantMass(Jets_p4[0], Jets_p4[1])")
            .Define("Event_njets", "(int)Jets_p4.size()")
            .Define("Event_Bz", "ReconstructedParticle2Track::Bz(ReconstructedParticles, EFlowTrack_1, Reco2TrackLinks)")

            # define constituent-level observables
            .Define("JetsConstituents", "JetConstituentsUtils::build_constituents_cluster(ReconstructedParticles, jetconstituents_ee_genkt)")
 
            # Extract ParticleID types for all jet constituents
            # ParticleID.type legend: 0:Track, 1:Electron, 2:Muon, 3:Track from V0, 
            #                         4:EM, 5:Ecal hadron/residual, 6:Hcal element, 7:Lcal element
            .Define("JetsConstituents_Types", "getParticleIDTypes(ParticleIDs, jetconstituents_ee_genkt)")
            
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

            # basic kinematics
            .Define("JetsConstituents_e", "JetConstituentsUtils::get_e(JetsConstituents)")
            .Define("JetsConstituents_pt", "JetConstituentsUtils::get_pt(JetsConstituents)")
            .Define("JetsConstituents_px", "JetConstituentsUtils::get_px(JetsConstituents)")
            .Define("JetsConstituents_py", "JetConstituentsUtils::get_py(JetsConstituents)")
            .Define("JetsConstituents_pz", "JetConstituentsUtils::get_pz(JetsConstituents)")
            .Define("JetsConstituents_theta", "JetConstituentsUtils::get_theta(JetsConstituents)")
            .Define("JetsConstituents_phi", "JetConstituentsUtils::get_phi(JetsConstituents)")
            .Define("JetsConstituents_charge", "JetConstituentsUtils::get_charge(JetsConstituents)")

            # kinematics relative to jet
            .Define("JetsConstituents_erel", "JetConstituentsUtils::get_erel_cluster(jets_ee_genkt, JetsConstituents)")
            .Define("JetsConstituents_erel_log", "JetConstituentsUtils::get_erel_log_cluster(jets_ee_genkt, JetsConstituents)")
            .Define("JetsConstituents_ptrel", "JetConstituentsUtils::get_ptrel_cluster(jets_ee_genkt, JetsConstituents)")
            .Define("JetsConstituents_ptrel_log", "JetConstituentsUtils::get_ptrel_log_cluster(jets_ee_genkt, JetsConstituents)")
            .Define("JetsConstituents_thetarel", "JetConstituentsUtils::get_thetarel_cluster(jets_ee_genkt, JetsConstituents)")
            .Define("JetsConstituents_phirel", "JetConstituentsUtils::get_phirel_cluster(jets_ee_genkt, JetsConstituents)") 
            
            # PID variables
            .Define("JetsConstituents_dndx", "JetConstituentsUtils::get_dndx(JetsConstituents, EFlowTrack_2, EFlowTrack, JetsConstituents_isChargedHad)")
            #temp .Define("JetsConstituents_mtof", "JetConstituentsUtils::get_mtof(JetsConstituents, EFlowTrack_L, EFlowTrack, TrackerHits, JetsConstituents_Pids)")
           
            # track properties
            .Define("JetsConstituents_trackChi2", "JetConstituentsUtils::get_chi2(JetsConstituents, EFlowTrack, Reco2TrackLinks)")
            .Define("JetsConstituents_trackNdof", "JetConstituentsUtils::get_ndof(JetsConstituents, EFlowTrack, Reco2TrackLinks)")
            .Define("JetsConstituents_trackChi2Normalized", "JetConstituentsUtils::get_chi2Normalized(JetsConstituents, EFlowTrack, Reco2TrackLinks)")
        )

        # number of hits in tracking detectors
        if det=='fcc':
            dfout = (
                dfout
                .Define("JetsConstituents_nTrackHits_VDET", "makeDummyJetConstituentVariable(JetsConstituents, 0)")
                .Define("JetsConstituents_nTrackHits_ITC", "makeDummyJetConstituentVariable(JetsConstituents, 0)")
                .Define("JetsConstituents_nTrackHits_TPC", "makeDummyJetConstituentVariable(JetsConstituents, 0)")
            )

        elif det=='aleph':
            dfout = (
                dfout
                .Define("JetsConstituents_nTrackHits_VDET", "JetConstituentsUtils::get_nTrackHits_VDET(JetsConstituents, EFlowTrack, _Tracks_subdetectorHitNumbers, Reco2TrackLinks)")
                .Define("JetsConstituents_nTrackHits_ITC", "JetConstituentsUtils::get_nTrackHits_ITC(JetsConstituents, EFlowTrack, _Tracks_subdetectorHitNumbers, Reco2TrackLinks)")
                .Define("JetsConstituents_nTrackHits_TPC", "JetConstituentsUtils::get_nTrackHits_TPC(JetsConstituents, EFlowTrack, _Tracks_subdetectorHitNumbers, Reco2TrackLinks)")
            )
            
        dfout = (
            dfout

            # store some track parameters with respect to the nominal origin
            # (mainly for debugging? typically these variables should be re-calculated w.r.t. the primary vertex)
            # note: the parameters have the following meaning:
            #  - d0: transverse impact parameter, i.e. signed transverse distance of closest approach of track to origin
            #  - z0: longitudinal impact parameter, i.e. z-coordinate of the point of closest approach of the track to origin
            #  - phi0: ?
            #  - omega: track curvature (does not depend on reference point?)
            #  - tan(lambda): pz / pT (related to theta) (does not depend on reference point?)
            # note: the functions below don't do any calculations, they are just getters for the values stored.
            .Define("JetsConstituents_d0_wrt0", "JetConstituentsUtils::get_d0(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_z0_wrt0", "JetConstituentsUtils::get_z0(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_phi0_wrt0", "JetConstituentsUtils::get_phi0(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_omega_wrt0", "JetConstituentsUtils::get_omega(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_tanlambda_wrt0", "JetConstituentsUtils::get_tanLambda(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")

            # calculate the magnetic field strength along the z-axis from the curvature of the tracks
            .Define("JetsConstituents_Bz", "JetConstituentsUtils::get_Bz(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
        
            # more jet constituents
            .Define("JetsConstituents_dxy", "JetConstituentsUtils::XPtoPar_dxy(JetsConstituents, EFlowTrack_1, Reco2TrackLinks, PrimaryVertexP4, Event_Bz)")
            .Define("JetsConstituents_dz", "JetConstituentsUtils::XPtoPar_dz(JetsConstituents, EFlowTrack_1, Reco2TrackLinks, PrimaryVertexP4, Event_Bz)")
            .Define("JetsConstituents_phi0", "JetConstituentsUtils::XPtoPar_phi(JetsConstituents, EFlowTrack_1, Reco2TrackLinks, PrimaryVertexP4, Event_Bz)")
            .Define("JetsConstituents_C", "JetConstituentsUtils::XPtoPar_C(JetsConstituents, EFlowTrack_1, Event_Bz)")
            .Define("JetsConstituents_ct", "JetConstituentsUtils::XPtoPar_ct(JetsConstituents, EFlowTrack_1, Event_Bz)")

            .Define("JetsConstituents_omega_cov", "JetConstituentsUtils::get_omega_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_d0_cov", "JetConstituentsUtils::get_d0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_z0_cov", "JetConstituentsUtils::get_z0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_phi0_cov", "JetConstituentsUtils::get_phi0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_tanlambda_cov", "JetConstituentsUtils::get_tanlambda_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_d0_z0_cov", "JetConstituentsUtils::get_d0_z0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_phi0_d0_cov", "JetConstituentsUtils::get_phi0_d0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_phi0_z0_cov", "JetConstituentsUtils::get_phi0_z0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_tanlambda_phi0_cov", "JetConstituentsUtils::get_tanlambda_phi0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_tanlambda_d0_cov", "JetConstituentsUtils::get_tanlambda_d0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_tanlambda_z0_cov", "JetConstituentsUtils::get_tanlambda_z0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_omega_tanlambda_cov", "JetConstituentsUtils::get_omega_tanlambda_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_omega_phi0_cov", "JetConstituentsUtils::get_omega_phi0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_omega_d0_cov", "JetConstituentsUtils::get_omega_d0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            .Define("JetsConstituents_omega_z0_cov", "JetConstituentsUtils::get_omega_z0_cov(JetsConstituents, EFlowTrack_1, Reco2TrackLinks)")
            
            .Define("JetsConstituents_Sip2dVal", "JetConstituentsUtils::get_Sip2dVal_clusterV(jets_ee_genkt, JetsConstituents, JetsConstituents_dxy, JetsConstituents_phi0)")
            .Define("JetsConstituents_Sip2dSig", "JetConstituentsUtils::get_Sip2dSig(JetsConstituents_Sip2dVal, JetsConstituents_d0_cov)")
            .Define("JetsConstituents_Sip3dVal", "JetConstituentsUtils::get_Sip3dVal_clusterV(jets_ee_genkt, JetsConstituents, JetsConstituents_dxy, JetsConstituents_dz, JetsConstituents_phi0)")
            .Define("JetsConstituents_Sip3dSig", "JetConstituentsUtils::get_Sip3dSig(JetsConstituents_Sip3dVal, JetsConstituents_d0_cov, JetsConstituents_z0_cov)")
            .Define("JetsConstituents_JetDistVal", "JetConstituentsUtils::get_JetPlaneDistVal_clusterV(jets_ee_genkt, JetsConstituents, JetsConstituents_dxy, JetsConstituents_dz, JetsConstituents_phi0)")
            .Define("JetsConstituents_JetDistSig", "JetConstituentsUtils::get_JetPlaneDistSig(JetsConstituents_JetDistVal, JetsConstituents_d0_cov, JetsConstituents_z0_cov)")

            # counting the types of particles per jet
            .Define("Jets_nConstituents", "JetConstituentsUtils::count_consts(JetsConstituents)")
            .Define("Jets_nMu", "JetConstituentsUtils::count_type(JetsConstituents_isMu)")
            .Define("Jets_nEl", "JetConstituentsUtils::count_type(JetsConstituents_isEl)")
            .Define("Jets_nChargedHad", "JetConstituentsUtils::count_type(JetsConstituents_isChargedHad)")
            .Define("Jets_nPhoton", "JetConstituentsUtils::count_type(JetsConstituents_isGamma)")
            .Define("Jets_nNeutralHad", "JetConstituentsUtils::count_type(JetsConstituents_isNeutralHad)")
        
            # compute the residues jet-constituents on significant kinematic variables as a check
            # notes:
            # - "tlv_jets" seems to mean: "the lorentz vectors of the jets, calculated directly from the jets"
            # - "sum_tlv_jcs" seems to mean: "the lorentz vectors of the jets, but calculated by summing all constituents"
            .Define("tlv_jets", "JetConstituentsUtils::compute_tlv_jets(jets_ee_genkt)")
            .Define("sum_tlv_jcs", "JetConstituentsUtils::sum_tlv_constituents(JetsConstituents)")
            .Define("Event_de", "JetConstituentsUtils::compute_residue_energy(tlv_jets, sum_tlv_jcs)")
            .Define("Event_dpt", "JetConstituentsUtils::compute_residue_pt(tlv_jets, sum_tlv_jcs)")
            .Define("Event_dphi", "JetConstituentsUtils::compute_residue_phi(tlv_jets, sum_tlv_jcs)")
            .Define("Event_dtheta", "JetConstituentsUtils::compute_residue_theta(tlv_jets, sum_tlv_jcs)")
            
        )
        return dfout

    def output():
        branchList = []

        # gen-level stuff
        branchList += [
            'genEventType',
            'GenParticle_pdgId',
            'GenParticle_genStatus',
            'GenPV_x',
            'GenPV_y',
            'GenPV_z'
        ]

        # event-level variables
        branchList += [
            'recoEventType',
            'Event_njets',
            'Event_mass',
            'Event_Bz',
            'Event_de',
            'Event_dpt',
            'Event_dphi',
            'Event_dtheta',
            'PV_x',
            'PV_y',
            'PV_z',
        ]
        
        # jet-level variables
        branchList += [
            'Jets_e',
            'Jets_mass',
            'Jets_pt',
            'Jets_phi',
            'Jets_eta',
            'Jets_theta',
            'Jets_nConstituents',
            'Jets_nMu',
            'Jets_nEl',
            'Jets_nChargedHad',
            'Jets_nPhoton',
            'Jets_nNeutralHad',
        ]

        # jet-constituent-level variables
        branchList += [
            'JetsConstituents_e', 'JetsConstituents_pt',
            'JetsConstituents_px', 'JetsConstituents_py', 'JetsConstituents_pz',
            'JetsConstituents_theta', 'JetsConstituents_phi',
            'JetsConstituents_charge',
            'JetsConstituents_erel', 'JetsConstituents_erel_log',
            'JetsConstituents_ptrel', 'JetsConstituents_ptrel_log',
            'JetsConstituents_thetarel', 'JetsConstituents_phirel', 
            'JetsConstituents_dndx',
            #temp 'JetsConstituents_mtof',

            'JetsConstituents_trackChi2',
            'JetsConstituents_trackNdof',
            'JetsConstituents_trackChi2Normalized',
            
            'JetsConstituents_nTrackHits_VDET',
            'JetsConstituents_nTrackHits_ITC',
            'JetsConstituents_nTrackHits_TPC',

            'JetsConstituents_d0_wrt0',
            'JetsConstituents_z0_wrt0',
            'JetsConstituents_phi0_wrt0',
            'JetsConstituents_omega_wrt0',
            'JetsConstituents_tanlambda_wrt0',
            'JetsConstituents_Bz',
            'JetsConstituents_dxy',
            'JetsConstituents_dz',
            'JetsConstituents_phi0',
            'JetsConstituents_C',
            'JetsConstituents_ct',

            'JetsConstituents_omega_cov',
            'JetsConstituents_d0_cov',
            'JetsConstituents_z0_cov',
            'JetsConstituents_phi0_cov',
            'JetsConstituents_tanlambda_cov',
            'JetsConstituents_d0_z0_cov',
            'JetsConstituents_phi0_d0_cov',
            'JetsConstituents_phi0_z0_cov', 
            'JetsConstituents_tanlambda_phi0_cov',
            'JetsConstituents_tanlambda_d0_cov',
            'JetsConstituents_tanlambda_z0_cov', 
            'JetsConstituents_omega_tanlambda_cov',
            'JetsConstituents_omega_phi0_cov',
            'JetsConstituents_omega_d0_cov',
            'JetsConstituents_omega_z0_cov', 
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
