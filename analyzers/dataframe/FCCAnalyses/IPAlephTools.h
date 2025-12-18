/*
Tools for calculating ALEPH-style impact parameters
*/


#ifndef FCCAnalyses_IPAlephTools_h
#define FCCAnalyses_IPAlephTools_h

#include <cmath>
#include "ROOT/RVec.hxx"
#include "TVector3.h"
#include "TMatrixD.h"
#include "TMatrixDSym.h"
#include "edm4hep/Track.h"
#include "edm4hep/TrackData.h"
#include "edm4hep/TrackState.h"
#include "edm4hep/ReconstructedParticle.h"
#include "podio/ObjectID.h"
#include "fastjet/JetDefinition.hh"

namespace FCCAnalyses{

namespace IPAlephTools{

namespace rv = ROOT::VecOps;

rv::RVec<rv::RVec<rv::RVec<TVector3>>> getTrackToJetAxisPCA(
    const rv::RVec<fastjet::PseudoJet>& jets,
    const rv::RVec<rv::RVec<edm4hep::ReconstructedParticleData>>& jetConstituents,
    const rv::RVec<edm4hep::TrackState>& tracks,
    const rv::RVec<podio::ObjectID>& reco2track_links,
    const TVector3& primaryVertex);

rv::RVec<rv::RVec<TVector3>> getTrackPCAToJetAxis(
    const rv::RVec<rv::RVec<rv::RVec<TVector3>>>& pcas);

rv::RVec<rv::RVec<TVector3>> getJetAxisPCAToTrack(
    const rv::RVec<rv::RVec<rv::RVec<TVector3>>>& pcas);

rv::RVec<rv::RVec<TVector3>> getLinePCAToPrimaryVertex(
    const rv::RVec<rv::RVec<rv::RVec<TVector3>>>& pcas);

rv::RVec<rv::RVec<float>> getPCA_x(const rv::RVec<rv::RVec<TVector3>>& pcas);
rv::RVec<rv::RVec<float>> getPCA_y(const rv::RVec<rv::RVec<TVector3>>& pcas);
rv::RVec<rv::RVec<float>> getPCA_z(const rv::RVec<rv::RVec<TVector3>>& pcas);

rv::RVec<rv::RVec<float>> signedIP3D(
    const rv::RVec<rv::RVec<rv::RVec<TVector3>>>& pcas,
    const rv::RVec<fastjet::PseudoJet>& jets,
    const TVector3& primaryVertex);

rv::RVec<rv::RVec<float>> IP3DUnc(
    const rv::RVec<rv::RVec<rv::RVec<TVector3>>>& pcas,
    const TVector3& primaryVertex);

rv::RVec<rv::RVec<float>> signedIP3DSig(
    const rv::RVec<rv::RVec<rv::RVec<TVector3>>>& pcas,
    const rv::RVec<fastjet::PseudoJet>& jets,
    const TVector3& primaryVertex);

rv::RVec<rv::RVec<float>> transverseJetDistance(
    const rv::RVec<rv::RVec<rv::RVec<TVector3>>>& pcas);

rv::RVec<rv::RVec<float>> longitudinalJetDistance(
    const rv::RVec<rv::RVec<rv::RVec<TVector3>>>& pcas,
    const TVector3& primaryVertex);

} // end namespace IPAlephTools

} // end namespace FCCAnalyses

#endif
