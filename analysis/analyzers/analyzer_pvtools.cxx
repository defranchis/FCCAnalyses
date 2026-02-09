// Tools for dealing with primary vertex reconstruction

#include <ROOT/RVec.hxx>

#include "FCCAnalyses/JetConstituentsUtils.h"
#include "FCCAnalyses/ReconstructedParticle.h"
#include "FCCAnalyses/ReconstructedParticle2Track.h"

#include "edm4hep/Track.h"
#include "edm4hep/TrackData.h"
#include "edm4hep/ReconstructedParticleData.h"

#include <iostream>
#include <algorithm>


namespace PrimaryVertexTools{

// helper function to find primary tracks.
// note: need to keep in sync with fitRecoPrimaryVertex (below)...
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
}

// helper function to re-calculate the primary vertex from the collection of tracks.
// note: no track selection is performed, this is assumed to be done beforehand.
// note: need to keep in sync with getPrimaryTracks (above)...
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
}

}
