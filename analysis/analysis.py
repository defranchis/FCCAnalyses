import os
import sys
import json
import ROOT


### handling of beamspot data (preliminary) ###

# load beamspot json file
beamspotfile = 'data/beamspot.json'
if os.path.exists(beamspotfile):
    print(f'Loading beamspot data from {beamspotfile}...')
    with open(beamspotfile, 'r') as f:
        beamspot_data = json.load(f)
else:
    msg = 'WARNING: trying to load beamspot data, but expected file {beamspotfile} not found.'
    msg += ' Will skip loading beamspot data.'
    print(msg)
    beamspot_data = None

# declare data struct in ROOT and fill it
ROOT.gInterpreter.Declare("""
    #include <map>
    #include <tuple>
    #include <string>

    static std::map<int, std::tuple<double,double,double>> beamspotCoords;
""")
for run, coords in beamspot_data.items():
    ROOT.beamspotCoords.emplace(
        int(run),
        ROOT.std.make_tuple(float(coords['x']), float(coords['y']), float(coords['z']))
    )

# declare retrieval function in ROOT
ROOT.gInterpreter.Declare("""
    TLorentzVector getBeamspotCoords(int run){
        auto it = beamspotCoords.find(run);
        if (it != beamspotCoords.end()){
            std::tuple<double, double, double> coords = it->second;
            return TLorentzVector(std::get<0>(coords), std::get<1>(coords), std::get<2>(coords), 0.0);
        }
        // fallback if run not found
        return TLorentzVector(0.0, 0.0, 0.0, 0.0);
    }
""")

### end of beamspot handling part ###


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
        const ROOT::VecOps::RVec<FCCAnalyses::VertexingUtils::FCCAnalysesVertex>& vertexCollection){
        edm4hep::VertexData vertex;
        TLorentzVector result = {0., 0., 0., 0.};
        if( vertexCollection.size() == 0 ){ return result; }
        vertex = vertexCollection.at(0).vertex;
        result = {vertex.position.x, vertex.position.y, vertex.position.z, 0.};
        return result;
    }""")

# helper function to find tracks passing some baseline selection
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<edm4hep::TrackState> getSelectedTracks(
        const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks){

        // do filtering
        ROOT::VecOps::RVec<edm4hep::TrackState> selectedTracks;
        for (const edm4hep::TrackState& trk : tracks) {
            const auto& c = trk.covMatrix;
            if (c[0] <= 0 || c[2] <= 0 || c[9] <= 0) continue;
            if (c[0] < 1e-6 || c[2] < 1e-6 || c[9] <= 1e-6) continue;
            if (!std::isfinite(c[0]) || !std::isfinite(c[2]) || !std::isfinite(c[9])) continue;
            if (std::abs(trk.D0)>3 || std::abs(trk.Z0)>5) continue;
            selectedTracks.push_back(trk);
        }
        return selectedTracks;
    }""")

# same as above but with tracks per jet
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::TrackState>> getSelectedTracks(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::TrackState>>& tracksPerJet){

        // initialization
        ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::TrackState>> selectedTracks;

        // loop over jets
        for ( const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks : tracksPerJet) {
            selectedTracks.push_back( getSelectedTracks(tracks) );
        }
        return selectedTracks;
    }""")

# helper function to find primary tracks.
# note: need to keep in sync with fitRecoPrimaryVertex (below)...
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<edm4hep::TrackState> getPrimaryTracks(
        const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
        double chi2max = 25.,
        double beamspotX = 0., double beamspotY = 0., double beamspotZ = 0.){

        // convert beamspot position units from centimeter to 10 micrometer
        // note: the FCCAnalyses function expect these values in micrometer,
        //       corresponding to track parameters in mm;
        //       but since our track parameters are in cm instead of mm,
        //       we use beamspot units of 10 micrometers.
        beamspotX = beamspotX * 1e3;
        beamspotY = beamspotY * 1e3;
        beamspotZ = beamspotZ * 1e3;

        // define beamspot width
        double sigma_beamspotX = 20; // unit: 10 micrometer
        double sigma_beamspotY = 10; // unit: 10 micrometer
        double sigma_beamspotZ = 2000; // unit: 10 micrometer
        bool doBeamSpotConstraint = true;

        // intitialize output
        ROOT::VecOps::RVec<edm4hep::TrackState> primaryTracks;

        // do filtering
        // note: the input is assumed to have already passed the baseline selection;
        //       here we just apply an extra cut on D0 and Z0 to focus on primary tracks
        ROOT::VecOps::RVec<edm4hep::TrackState> tracksToUse;
        for (const edm4hep::TrackState& trk : tracks) {
            if (std::abs(trk.D0)>0.75 || std::abs(trk.Z0)>2) continue;
            tracksToUse.push_back(trk);
        }
        if( tracksToUse.size() < 2 ){ return primaryTracks; }

        // call primary track finder from FCCAnalyses
        primaryTracks = FCCAnalyses::VertexFitterSimple::get_PrimaryTracks(
            tracksToUse,
            chi2max,
            doBeamSpotConstraint,
            sigma_beamspotX, sigma_beamspotY, sigma_beamspotZ,
            beamspotX, beamspotY, beamspotZ
        );
        return primaryTracks;
    }""")

# helper function to re-calculate the primary vertex from the collection of tracks.
# note: no track selection is performed, this is assumed to be done beforehand.
# note: need to keep in sync with getPrimaryTracks (above)...
ROOT.gInterpreter.Declare("""
    FCCAnalyses::VertexingUtils::FCCAnalysesVertex fitRecoPrimaryVertex(
        const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
        double beamspotX = 0, double beamspotY = 0, double beamspotZ = 0){

        // convert beamspot position units from centimeter to 10 micrometer
        // note: the FCCAnalyses function expect these values in micrometer,
        //       corresponding to track parameters in mm;
        //       but since our track parameters are in cm instead of mm,
        //       we use beamspot units of 10 micrometers.
        beamspotX = beamspotX * 1e3;
        beamspotY = beamspotY * 1e3;
        beamspotZ = beamspotZ * 1e3;

        // define beamspot width
        double sigma_beamspotX = 20; // unit: 10 micrometer
        double sigma_beamspotY = 10; // unit: 10 micrometer
        double sigma_beamspotZ = 2000; // unit: 10 micrometer
        bool doBeamSpotConstraint = true;

        // define dummy vertex in case the fit cannot be performed
        edm4hep::VertexData dummyVertex;
        dummyVertex.chi2 = -1;
        dummyVertex.ndf = 0;
        dummyVertex.position = edm4hep::Vector3f(beamspotX, beamspotY, beamspotZ);
        FCCAnalyses::VertexingUtils::FCCAnalysesVertex dummyVertexObject;
        dummyVertexObject.vertex = dummyVertex;
        dummyVertexObject.ntracks = 0;
        dummyVertexObject.mc_ind = -1;
        if( tracks.size() < 2 ){ return dummyVertexObject; }

        // call primary vertex finder from FCCAnalyses
        FCCAnalyses::VertexingUtils::FCCAnalysesVertex vertex;
        vertex = FCCAnalyses::VertexFitterSimple::VertexFitter_Tk(
            1, tracks, doBeamSpotConstraint,
            sigma_beamspotX, sigma_beamspotY, sigma_beamspotZ,
            beamspotX, beamspotY, beamspotZ
        );
        return vertex;
    }""")

# helper function to find tracks not compatible with primary vertex.
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<edm4hep::TrackState> getSecondaryTracks(
        const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
        const ROOT::VecOps::RVec<edm4hep::TrackState>& primaryTracks){

        // skip tracks compatible with primary vertex
        ROOT::VecOps::RVec<edm4hep::TrackState> secondaryTracks;
        secondaryTracks = FCCAnalyses::VertexFitterSimple::get_NonPrimaryTracks(tracks, primaryTracks);
        return secondaryTracks;
    }""")

# same as above but with tracks per jet
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::TrackState>> getSecondaryTracks(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::TrackState>>& tracksPerJet,
        const ROOT::VecOps::RVec<edm4hep::TrackState>& primaryTracks){

        // initialization
        ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::TrackState>> secondaryTracks;

        // loop over jets
        for ( const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks : tracksPerJet) {
            secondaryTracks.push_back( getSecondaryTracks(tracks, primaryTracks) );
        }
        return secondaryTracks;
    }""")

# helper function to associate a set of per-event secondary vertices to jets
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<ROOT::VecOps::RVec<FCCAnalyses::VertexingUtils::FCCAnalysesVertex>>
    distributeSecondaryVerticesOverJets(
        const ROOT::VecOps::RVec<FCCAnalyses::VertexingUtils::FCCAnalysesVertex>& secondaryVertices,
        const ROOT::VecOps::RVec<fastjet::PseudoJet>& jets){

        // initialization
        ROOT::VecOps::RVec<ROOT::VecOps::RVec<FCCAnalyses::VertexingUtils::FCCAnalysesVertex>> secondaryVerticesPerJet;
        for(unsigned int i=0; i<jets.size(); i++){
            ROOT::VecOps::RVec<FCCAnalyses::VertexingUtils::FCCAnalysesVertex> temp;
            secondaryVerticesPerJet.push_back(temp);
        }

        // note: in very rare cases, there can be secondary vertices but no jets
        //       (even with exclusive jet clustering targeting 2 jets in every event);
        //       reason is not yet fully understood, but in any case, need safety against it.
        if( jets.size()==0 ){ return secondaryVerticesPerJet; }

        // get momenta of all vertices
        ROOT::VecOps::RVec<TVector3> vertex_momenta = FCCAnalyses::VertexingUtils::get_p_SV(secondaryVertices);

        // get momenta of all jets
        ROOT::VecOps::RVec<TVector3> jet_momenta;
        for( auto jet : jets ){
            jet_momenta.push_back( TVector3(jet.px(), jet.py(), jet.pz()) );
        }

        // loop over vertices
        for( unsigned int vertex_idx=0; vertex_idx < secondaryVertices.size(); vertex_idx++ ){
            double mindR = 99.;
            unsigned int selected_jet_idx = 0;
            FCCAnalyses::VertexingUtils::FCCAnalysesVertex vertex = secondaryVertices.at(vertex_idx);
            TVector3 vertex_momentum = vertex_momenta.at(vertex_idx);
            for( unsigned int jet_idx=0; jet_idx < jets.size(); jet_idx++){
                TVector3 jet_momentum = jet_momenta.at(jet_idx);
                double dR = vertex_momentum.DeltaR(jet_momentum);
                if( dR < mindR ){
                    mindR = dR;
                    selected_jet_idx = jet_idx;
                }
            }
            secondaryVerticesPerJet.at(selected_jet_idx).push_back(vertex);
        }
        return secondaryVerticesPerJet;
    }""")

# helper function to count the number of tracks per jet
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<int> countTracks(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::TrackState>>& tracks){
        ROOT::VecOps::RVec<int> nTracks;
        for( const ROOT::VecOps::RVec<edm4hep::TrackState>& this_tracks : tracks) {
            nTracks.push_back( this_tracks.size() );
        }
        return nTracks;
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

        # get the beamspot position
        if dtype=='data':
            dfout = (
                dfout
                .Define("BeamspotP4", "getBeamspotCoords(EventHeader.runNumber[0])")
                .Define("Beamspot_x", "BeamspotP4.X()")
                .Define("Beamspot_y", "BeamspotP4.Y()")
                .Define("Beamspot_z", "BeamspotP4.Z()")
            )
        else:
            # set to 0 for simulation
            dfout = (
                dfout
                .Define("Beamspot_x", "0.0")
                .Define("Beamspot_y", "0.0")
                .Define("Beamspot_z", "0.0")
            )

        # find the primary vertex
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
            #.Define("PrimaryVertexP4", "getRecoPrimaryVertex(Vertices)")
            
            # alternative: recalculate reco primary vertex
            .Define("SelectedTracks", "getSelectedTracks(EFlowTrack_1)")
            .Define("PrimaryTracks", "getPrimaryTracks(SelectedTracks, 25., Beamspot_x, Beamspot_y, Beamspot_z)")
            .Define("PrimaryVertexObject", "fitRecoPrimaryVertex(PrimaryTracks, Beamspot_x, Beamspot_y, Beamspot_z)")
            .Define("PrimaryVertex", "FCCAnalyses::VertexingUtils::get_VertexData(PrimaryVertexObject)")
            .Define("PrimaryVertexP4", "TLorentzVector(PrimaryVertex.position.x, PrimaryVertex.position.y, PrimaryVertex.position.z, 0.)")

            # store the primary vertex coordinates
            # (mainly for debugging)
            .Define("PV_x", "PrimaryVertexP4.X()")
            .Define("PV_y", "PrimaryVertexP4.Y()")
            .Define("PV_z", "PrimaryVertexP4.Z()")

            # make a copy of the primary vertex as a 3-vector rather than a 4-vector
            # (needed in some functions below)
            .Define("PrimaryVertexP3", "TVector3(PV_x, PV_y, PV_z)")

            # store properties of fitted vertex
            # (note: only works for fitted vertex, not for other methods)
            .Define("PV_chi2Normalized", "PrimaryVertex.chi2")
            .Define("PV_ndof", "PrimaryVertex.ndf")
        )

        # do jet clustering
        dfout = (
            dfout

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
            # - sorted: jet sorting method; allowed values are:
            #     - 0: sort by pt (default)
            #     - 1: sort by energy
            #   (see FCCAnalyses/analyzers/dataframe/src/JetClusteringUtils.cc / build_jets)
            # - recombination: how jets are summed (leave at default 0).
            # - exponent (of kT algorithm, typically -1, i.e. anti-kT).
            #.Define("FCCAnalysesJets_ee_genkt", "JetClustering::clustering_ee_genkt(1.5, 0, 0, 0, 0, -1)(pseudo_jets)") # inclusive
            #.Define("FCCAnalysesJets_ee_genkt", "JetClustering::clustering_ee_genkt(1.5, 3, 2, 0, 0, -1)(pseudo_jets)") # exclusive

            # alternative jet clustering in sync with CERN team
            # see here: https://github.com/Apranikstar/Aleph/blob/6fe1e52a50a22d3f1e0f978ca1c0e747488bb016/src/stage1.py#L128
            # note: the arguments are (in order):
            # - exclusive
            # - cut
            # - sorted
            # - recombination
            .Define("FCCAnalysesJets_ee_genkt", "JetClustering::clustering_ee_kt(2, 2, 1, 0)(pseudo_jets)")

            # get the jets out of the struct
            .Define("jets_ee_genkt", "JetClusteringUtils::get_pseudoJets(FCCAnalysesJets_ee_genkt)")

            # get the jets constituents out of the struct
            .Define("jetconstituents_ee_genkt", "JetClusteringUtils::get_constituents(FCCAnalysesJets_ee_genkt)")

            # define jet-level observables
            .Define("Jets_px", "JetClusteringUtils::get_px(jets_ee_genkt)")
            .Define("Jets_py", "JetClusteringUtils::get_py(jets_ee_genkt)")
            .Define("Jets_pz", "JetClusteringUtils::get_pz(jets_ee_genkt)")
            .Define("Jets_pt", "JetClusteringUtils::get_pt(jets_ee_genkt)")
            .Define("Jets_e", "JetClusteringUtils::get_e(jets_ee_genkt)")
            .Define("Jets_mass", "JetClusteringUtils::get_m(jets_ee_genkt)")
            .Define("Jets_phi", "JetClusteringUtils::get_phi(jets_ee_genkt)")
            .Define("Jets_eta", "JetClusteringUtils::get_eta(jets_ee_genkt)")
            .Define("Jets_theta", "JetClusteringUtils::get_theta(jets_ee_genkt)")
            .Define("Jets_p4", "JetConstituentsUtils::compute_tlv_jets(jets_ee_genkt)")
        )

        # find secondary vertices (per jet)
        dfout = (
            dfout

            # find track states grouped per jet, and perform baseline selection
            # (output struct is a vector of vectors of TrackState objects, one vector of TrackStates for each jet)
            .Define("TracksPerJet", "JetConstituentsUtils::build_trackstates_cluster(ReconstructedParticles, EFlowTrack_1, jetconstituents_ee_genkt, Reco2TrackLinks)")
            .Define("SelectedTracksPerJet", "getSelectedTracks(TracksPerJet)")

            # find tracks incompatible with the primary vertex (both per event and per jet).
            # note: primary tracks have already been defined before (when calculating the primary vertex),
            #       but an alternative set is re-calculated here, possibly with a tighter chi2 cut.
            .Define("PrimaryTracks2", "getPrimaryTracks(SelectedTracks, 5., Beamspot_x, Beamspot_y, Beamspot_z)")
            .Define("SecondaryTracks", "getSecondaryTracks(SelectedTracks, PrimaryTracks2)")
            .Define("SecondaryTracksPerJet", "getSecondaryTracks(SelectedTracksPerJet, PrimaryTracks2)")

            # fit secondary vertices per jet.
            # (output struct is a vector of vectors of FCCAnalysesVertex objects, one vector for each jet).
            # the input arguments are (in order):
            # - tracks per jet to use
            # - all tracks
            # - primary vertex
            # - whether to do V0 rejection
            # - chi2 upper bound for vertices
            # - invariant mass upper bound for vertices
            # - track chi2 cut (what does this do exactly?)
            #.Define("SecondaryVertices", "FCCAnalyses::VertexFinderLCFIPlus::get_SV_jets(SecondaryTracksPerJet, EFlowTrack_1, PrimaryVertexObject, true, 10., 10., 5.)")
            
            # alternative: fit secondary vertices per event (ignoring jets), and associate them to tracks post-rem.
            # note: not sure how to do this best, but for now do simple dR matching.
            # note: does not seem to work yet; get_SV_event gives a segmentation violation on some events, that is hard to pin down...
            .Define("EventSecondaryVertices", "FCCAnalyses::VertexFinderLCFIPlus::get_SV_event(SecondaryTracks, EFlowTrack_1, PrimaryVertexObject, true, 10., 10., 5.)")
            .Define("SecondaryVertices", "distributeSecondaryVerticesOverJets(EventSecondaryVertices, jets_ee_genkt)")

            # calculate properties of secondary vertices to store
            .Define("SecondaryVertices_xrel", "FCCAnalyses::VertexingUtils::get_xrel_SV_jets(SecondaryVertices, PrimaryVertexP3)")
            .Define("SecondaryVertices_yrel", "FCCAnalyses::VertexingUtils::get_yrel_SV_jets(SecondaryVertices, PrimaryVertexP3)")
            .Define("SecondaryVertices_zrel", "FCCAnalyses::VertexingUtils::get_zrel_SV_jets(SecondaryVertices, PrimaryVertexP3)")
            .Define("SecondaryVertices_thetarel", "FCCAnalyses::VertexingUtils::get_relTheta_SV(SecondaryVertices, jets_ee_genkt)")
            .Define("SecondaryVertices_phirel", "FCCAnalyses::VertexingUtils::get_relPhi_SV(SecondaryVertices, jets_ee_genkt)")
            .Define("SecondaryVertices_p", "FCCAnalyses::VertexingUtils::get_pMag_SV_jets(SecondaryVertices)")
            .Define("SecondaryVertices_prel", "FCCAnalyses::VertexingUtils::get_prel_SV_jets(SecondaryVertices, jets_ee_genkt)")
            .Define("SecondaryVertices_chi2", "FCCAnalyses::VertexingUtils::get_chi2_SV_jets(SecondaryVertices)")
            .Define("SecondaryVertices_chi2Normalized", "FCCAnalyses::VertexingUtils::get_norm_chi2_SV_jets(SecondaryVertices)")
            .Define("SecondaryVertices_ndof", "FCCAnalyses::VertexingUtils::get_nDOF_SV_jets(SecondaryVertices)")
            .Define("SecondaryVertices_nTracks", "FCCAnalyses::VertexingUtils::get_VertexNtrk(SecondaryVertices)")
            .Define("SecondaryVertices_mass", "FCCAnalyses::VertexingUtils::get_invM_jets(SecondaryVertices)")
            .Define("SecondaryVertices_dxy", "FCCAnalyses::VertexingUtils::get_dxy_SV(SecondaryVertices, PrimaryVertexObject)")
            .Define("SecondaryVertices_dxyz", "FCCAnalyses::VertexingUtils::get_d3d_SV(SecondaryVertices, PrimaryVertexObject)")
            .Define("SecondaryVertices_cosPointing", "FCCAnalyses::VertexingUtils::get_pointingangle_SV(SecondaryVertices, PrimaryVertexObject)")

            # get the number of secondary vertices per jet
            .Define("Jets_nSV", "FCCAnalyses::VertexingUtils::get_n_SV_jets(SecondaryVertices)")
            .Define("Jets_nTracksPerJet", "countTracks(TracksPerJet)") # for debugging
            .Define("Jets_nSelectedTracksPerJet", "countTracks(SelectedTracksPerJet)") # for debugging
            .Define("Jets_nSecondaryTracksPerJet", "countTracks(SecondaryTracksPerJet)") # for debugging
        )

        # rest of the analysis
        dfout = (
            dfout

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
            # (mainly for debugging; typically these variables should be re-calculated w.r.t. the primary vertex)
            # note: the parameters have the following meaning:
            #  - d0: transverse impact parameter, i.e. signed transverse distance of closest approach of track to origin
            #  - z0: longitudinal impact parameter, i.e. z-coordinate of the point of closest approach of the track to origin
            #  - phi0: azimuthal angle of track at the point of closest approach of the track to the origin
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
        
            # impact parameters (with respect to the primary vertex) and related quantities (including their uncertainties)
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
            
            # FCC-style signed impact parameters
            .Define("JetsConstituents_Sip2dVal", "JetConstituentsUtils::get_Sip2dVal_clusterV(jets_ee_genkt, JetsConstituents, JetsConstituents_dxy, JetsConstituents_phi0)")
            .Define("JetsConstituents_Sip2dSig", "JetConstituentsUtils::get_Sip2dSig(JetsConstituents_Sip2dVal, JetsConstituents_d0_cov)")
            .Define("JetsConstituents_Sip3dVal", "JetConstituentsUtils::get_Sip3dVal_clusterV(jets_ee_genkt, JetsConstituents, JetsConstituents_dxy, JetsConstituents_dz, JetsConstituents_phi0)")
            .Define("JetsConstituents_Sip3dSig", "JetConstituentsUtils::get_Sip3dSig(JetsConstituents_Sip3dVal, JetsConstituents_d0_cov, JetsConstituents_z0_cov)")
            .Define("JetsConstituents_JetDistVal", "JetConstituentsUtils::get_JetPlaneDistVal_clusterV(jets_ee_genkt, JetsConstituents, JetsConstituents_dxy, JetsConstituents_dz, JetsConstituents_phi0)")
            .Define("JetsConstituents_JetDistSig", "JetConstituentsUtils::get_JetPlaneDistSig(JetsConstituents_JetDistVal, JetsConstituents_d0_cov, JetsConstituents_z0_cov)")

            # ALEPH-style signed impact parameters
            .Define("trackToJetAxisPCAs", "IPAlephTools::getTrackToJetAxisPCA(jets_ee_genkt, JetsConstituents, EFlowTrack_1, Reco2TrackLinks, PrimaryVertexP3)")
            .Define("JetsConstituents_linearSignedIP3D", "IPAlephTools::signedIP3D(trackToJetAxisPCAs, jets_ee_genkt, PrimaryVertexP3)")
            .Define("JetsConstituents_linearSignedIP3DSig", "IPAlephTools::signedIP3DSig(trackToJetAxisPCAs, jets_ee_genkt, PrimaryVertexP3)")
            .Define("JetsConstituents_transverseJetDistance", "IPAlephTools::transverseJetDistance(trackToJetAxisPCAs)")
            .Define("JetsConstituents_longitudinalJetDistance", "IPAlephTools::longitudinalJetDistance(trackToJetAxisPCAs, PrimaryVertexP3)")

            # extension of the above: store coordinates of PCAs (only for checking and debugging)
            .Define("trackPCAToJetAxis", "IPAlephTools::getTrackPCAToJetAxis(trackToJetAxisPCAs)")
            .Define("jetAxisPCAToTrack", "IPAlephTools::getJetAxisPCAToTrack(trackToJetAxisPCAs)")
            .Define("linePCAToPrimaryVertex", "IPAlephTools::getLinePCAToPrimaryVertex(trackToJetAxisPCAs)")
            .Define("JetsConstituents_trackPCAToJetAxis_x", "IPAlephTools::getPCA_x(trackPCAToJetAxis)")
            .Define("JetsConstituents_trackPCAToJetAxis_y", "IPAlephTools::getPCA_y(trackPCAToJetAxis)")
            .Define("JetsConstituents_trackPCAToJetAxis_z", "IPAlephTools::getPCA_z(trackPCAToJetAxis)")
            .Define("JetsConstituents_jetAxisPCAToTrack_x", "IPAlephTools::getPCA_x(jetAxisPCAToTrack)")
            .Define("JetsConstituents_jetAxisPCAToTrack_y", "IPAlephTools::getPCA_y(jetAxisPCAToTrack)")
            .Define("JetsConstituents_jetAxisPCAToTrack_z", "IPAlephTools::getPCA_z(jetAxisPCAToTrack)")
            .Define("JetsConstituents_linePCAToPrimaryVertex_x", "IPAlephTools::getPCA_x(linePCAToPrimaryVertex)")
            .Define("JetsConstituents_linePCAToPrimaryVertex_y", "IPAlephTools::getPCA_y(linePCAToPrimaryVertex)")
            .Define("JetsConstituents_linePCAToPrimaryVertex_z", "IPAlephTools::getPCA_z(linePCAToPrimaryVertex)")

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
            'Event_dtheta'
        ]

        # primary vertex variables
        branchList += [
            'PV_x',
            'PV_y',
            'PV_z',
            'PV_chi2Normalized',
            'PV_ndof'
        ]
        
        # jet-level variables
        branchList += [
            'Jets_e',
            'Jets_mass',
            'Jets_pt',
            'Jets_px',
            'Jets_py',
            'Jets_pz',
            'Jets_phi',
            'Jets_eta',
            'Jets_theta',
            'Jets_nConstituents',
            'Jets_nMu',
            'Jets_nEl',
            'Jets_nChargedHad',
            'Jets_nPhoton',
            'Jets_nNeutralHad',
            'Jets_nSV',
            'Jets_nTracksPerJet',
            'Jets_nSelectedTracksPerJet',
            'Jets_nSecondaryTracksPerJet'
        ]

        # secondary-vertex-level variables
        branchList += [
            'SecondaryVertices_xrel',
            'SecondaryVertices_yrel',
            'SecondaryVertices_zrel',
            'SecondaryVertices_thetarel',
            'SecondaryVertices_phirel',
            'SecondaryVertices_p',
            'SecondaryVertices_prel',
            'SecondaryVertices_chi2',
            'SecondaryVertices_chi2Normalized',
            'SecondaryVertices_ndof',
            'SecondaryVertices_nTracks',
            'SecondaryVertices_mass',
            'SecondaryVertices_dxy',
            'SecondaryVertices_dxyz',
            'SecondaryVertices_cosPointing'
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

            'JetsConstituents_linearSignedIP3D',
            'JetsConstituents_linearSignedIP3DSig',
            'JetsConstituents_transverseJetDistance',
            'JetsConstituents_longitudinalJetDistance',

            "JetsConstituents_trackPCAToJetAxis_x",
            "JetsConstituents_trackPCAToJetAxis_y",
            "JetsConstituents_trackPCAToJetAxis_z",
            "JetsConstituents_jetAxisPCAToTrack_x",
            "JetsConstituents_jetAxisPCAToTrack_y",
            "JetsConstituents_jetAxisPCAToTrack_z",
            "JetsConstituents_linePCAToPrimaryVertex_x",
            "JetsConstituents_linePCAToPrimaryVertex_y",
            "JetsConstituents_linePCAToPrimaryVertex_z",

            'JetsConstituents_isMu', 
            'JetsConstituents_isEl', 
            'JetsConstituents_isChargedHad',
            'JetsConstituents_isGamma', 
            'JetsConstituents_isNeutralHad',
        ]

        return branchList    
