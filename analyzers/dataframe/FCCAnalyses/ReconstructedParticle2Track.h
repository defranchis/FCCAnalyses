
#ifndef  RECONSTRUCTEDPARTICLE2TRACK_ANALYZERS_H
#define  RECONSTRUCTEDPARTICLE2TRACK_ANALYZERS_H

#include <cmath>
#include <vector>

#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"
#include "edm4hep/TrackData.h"
#include "edm4hep/TrackState.h"
#include "podio/ObjectID.h"
#if __has_include("edm4hep/TrackerHit3DData.h")
#include "edm4hep/TrackerHit3DData.h"
#else
#include "edm4hep/TrackerHitData.h"
namespace edm4hep {
  using TrackerHit3DData = edm4hep::TrackerHitData;
}
#endif
#include <TVectorD.h>
#include <TVector3.h>
#include <TLorentzVector.h>

#include <TMath.h>
#include <iostream>

namespace FCCAnalyses{

namespace ReconstructedParticle2Track{

  // get all track states for a set of given reconstructed particles
  ROOT::VecOps::RVec<edm4hep::TrackState> getRP2TRK_trackState(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
        const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);

  // get the momentum of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_mom(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in, 
					   ROOT::VecOps::RVec<edm4hep::TrackState> tracks);

  // get the charge of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_charge(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,  
					     ROOT::VecOps::RVec<edm4hep::TrackState> tracks);

  // get chi2 and ndof
  ROOT::VecOps::RVec<float> getRP2TRK_chi2(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
        const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);
  ROOT::VecOps::RVec<int> getRP2TRK_ndof(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
        const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);
  ROOT::VecOps::RVec<float> getRP2TRK_chi2Normalized(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
        const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);

  // get number of track hits in subdetectors
  ROOT::VecOps::RVec<int> getRP2TRK_nTrackHits(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
        const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
        const ROOT::VecOps::RVec<int>& subdetectorHitNumbers,
        const int subdetectorNumber,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);

  ROOT::VecOps::RVec<int> getRP2TRK_nTrackHits_VDET(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
        const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
        const ROOT::VecOps::RVec<int>& subdetectorHitNumbers,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);

  ROOT::VecOps::RVec<int> getRP2TRK_nTrackHits_ITC(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
        const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
        const ROOT::VecOps::RVec<int>& subdetectorHitNumbers,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);

  ROOT::VecOps::RVec<int> getRP2TRK_nTrackHits_TPC(
        const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
        const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
        const ROOT::VecOps::RVec<int>& subdetectorHitNumbers,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);

  // compute the magnetic field Bz
  ROOT::VecOps::RVec<float> getRP2TRK_Bz(
      const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
	  const ROOT::VecOps::RVec<edm4hep::TrackState>& trackStates,
      const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);

  float Bz(const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& rps,
	       const ROOT::VecOps::RVec<edm4hep::TrackState>& trackStates,
           const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links);

  // impact parameter calculations
  ROOT::VecOps::RVec<float> XPtoPar_dxy(const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& in,
					const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links,
					const TLorentzVector& PV,
					const float& Bz);

  ROOT::VecOps::RVec<float> XPtoPar_dz(const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& in,
                                        const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
                                        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links,
                                        const TLorentzVector& PV,
                                        const float& Bz);

  ROOT::VecOps::RVec<float> XPtoPar_phi(const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& in,
					const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links,
                    const TLorentzVector& PV,
                    const float& Bz);

  ROOT::VecOps::RVec<float> XPtoPar_C(const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& in,
					const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
                                        const float& Bz);

  ROOT::VecOps::RVec<float> XPtoPar_ct(const ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>& in,
					const ROOT::VecOps::RVec<edm4hep::TrackState>& tracks,
                                        const float& Bz);

  // get the D0 of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_D0 (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					  ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                      ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the Z0 of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_Z0 (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					  ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the Phi of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_phi (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					   ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the omega of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_omega (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					     ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the tanLambda of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_tanLambda (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						 ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the D0 significance of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_D0_sig (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					      ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the Z0 significance of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_Z0_sig (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					      ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);


  // get the variance (not the sigma)  of the the D0 of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_D0_cov (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					      ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the variance (not the sigma)  of the the Z0 of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_Z0_cov (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					      ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the variance (not the sigma)  of the the Phi of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_phi_cov (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
					       ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the variance (not the sigma)  of the omega of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_omega_cov (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						 ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the variance (not the sigma)  of the tanLambda of a track to a reconstructed particle
  ROOT::VecOps::RVec<float> getRP2TRK_tanLambda_cov (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						     ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (d0, phi0) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_d0_phi0_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						  ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (d0, omega) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_d0_omega_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						   ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (d0,z0) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_d0_z0_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (d0,tanlambda) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_d0_tanlambda_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						       ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (phi0,omega) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_phi0_omega_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						     ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (phi0,z0) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_phi0_z0_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						  ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (phi0,tanlambda) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_phi0_tanlambda_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
							 ROOT::VecOps::RVec<edm4hep::TrackState> tracks,
                             ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (omega,z0) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_omega_z0_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						   ROOT::VecOps::RVec<edm4hep::TrackState> tracks,
                           ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (omega,tanlambda) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_omega_tanlambda_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
							  ROOT::VecOps::RVec<edm4hep::TrackState> tracks,
                              ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);

  // get the off-diag term (z0,tanlambda) of the covariance matrix
  ROOT::VecOps::RVec<float> getRP2TRK_z0_tanlambda_cov(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						       ROOT::VecOps::RVec<edm4hep::TrackState> trackStates,
                            ROOT::VecOps::RVec<podio::ObjectID> reco2track_links);


  // get the tracks associated to reco'ed particles
  ROOT::VecOps::RVec<edm4hep::TrackState> getRP2TRK( ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
						     ROOT::VecOps::RVec<edm4hep::TrackState> tracks ) ;

  // get the reco indices of particles that have tracks
  ROOT::VecOps::RVec<int> get_recoindTRK( ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in, 
					  ROOT::VecOps::RVec<edm4hep::TrackState> tracks ) ;
  
  // get the size of a collection of TrackStates
  int getTK_n(ROOT::VecOps::RVec<edm4hep::TrackState> x) ;

  // get if a Reco particle have an associated track
  ROOT::VecOps::RVec<bool> hasTRK( ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in ) ;

}//end NS ReconstructedParticle2Track

}//end NS FCCAnalyses
#endif
