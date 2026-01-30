#include "FCCAnalyses/JetConstituentsUtils.h"

// EDM4hep
#include "edm4hep/EDM4hepVersion.h"
// FastJet
#include "fastjet/JetDefinition.hh"
#include "fastjet/PseudoJet.hh"
#include "fastjet/Selector.hh"
// FCCAnalyses
#include "FCCAnalyses/JetClusteringUtils.h"
#include "FCCAnalyses/ReconstructedParticle.h"
#include "FCCAnalyses/ReconstructedParticle2MC.h"
#include "FCCAnalyses/ReconstructedParticle2Track.h"
#include "FCCAnalyses/TrackUtils.h"

/* *************************
//COMMENTS
1. Neutral particles (Clusters??)
2. units of measurement?

************************ */

namespace FCCAnalyses
{
  namespace JetConstituentsUtils
  {
    rv::RVec<FCCAnalysesJetConstituents> build_constituents(const rv::RVec<edm4hep::ReconstructedParticleData> &jets,
                                                            const rv::RVec<edm4hep::ReconstructedParticleData> &rps)
    {
      /*
      Build the collection of constituents (mapping jet -> reconstructed particles) for all jets in event
      */
      rv::RVec<FCCAnalysesJetConstituents> jcs;
      for (const auto &jet : jets)
      {
        auto &jc = jcs.emplace_back();
        float energy_jet = jet.energy;
        float energy_const = 0;
        for (auto it = jet.particles_begin; it < jet.particles_end; ++it)
        {
          jc.emplace_back(rps.at(it));
          energy_const += rps.at(it).energy;
        }
      }
      return jcs;
    }

    rv::RVec<FCCAnalysesJetConstituents> build_constituents_cluster(const rv::RVec<edm4hep::ReconstructedParticleData> &rps,
                                                                    const std::vector<std::vector<int>> &indices)
    {
      /*
      Build the collection of constituents (mapping jet -> reconstructed particles) for all jets in event
      */
      rv::RVec<FCCAnalysesJetConstituents> jcs;
      for (const auto &jet_index : indices)
      {
        FCCAnalysesJetConstituents jc;
        for (const auto &const_index : jet_index)
        {
          jc.push_back(rps.at(const_index));
        }
        jcs.push_back(jc);
      }
      return jcs;
    }

    rv::RVec<rv::RVec<edm4hep::TrackState>> build_trackstates_cluster(
        const rv::RVec<edm4hep::ReconstructedParticleData>& rps,
        const rv::RVec<edm4hep::TrackState>& tracks,
        const std::vector<std::vector<int>>& jet_indices,
        const rv::RVec<podio::ObjectID>& reco2track_links){
        /*
        Build the collection of track states (mapping jet -> track states of (charged) reconstructed particles)
        */
        rv::RVec<rv::RVec<edm4hep::TrackState>> tracks_perjet;
        // loop over jets
        for (const auto &this_jet_indices : jet_indices){
            // get constituents for this jet
            FCCAnalysesJetConstituents constituents;
            for (const auto &constituent_index : this_jet_indices){
                constituents.push_back(rps.at(constituent_index));
            }
            // get track states for these constituents
            rv::RVec<edm4hep::TrackState> this_jet_tracks;
            this_jet_tracks = ReconstructedParticle2Track::getRP2TRK_trackState(
                constituents, tracks, reco2track_links
            );
            tracks_perjet.push_back(this_jet_tracks);
        }
        return tracks_perjet;
    }

    FCCAnalysesJetConstituents get_jet_constituents(const rv::RVec<FCCAnalysesJetConstituents> &csts, int jet)
    {
      if (jet < 0)
        return FCCAnalysesJetConstituents();
      return csts.at(jet);
    }

    rv::RVec<FCCAnalysesJetConstituents> get_constituents(const rv::RVec<FCCAnalysesJetConstituents> &csts,
                                                          const rv::RVec<int> &jets)
    {
      rv::RVec<FCCAnalysesJetConstituents> jcs;
      for (size_t i = 0; i < jets.size(); ++i)
        if (jets.at(i) >= 0)
          jcs.emplace_back(csts.at(i));
      return jcs;
    }

    /// recasting helper for jet constituents methods
    /// \param[in] jcs collection of jets constituents
    /// \param[in] meth variables retrieval method for constituents
    auto cast_constituent = [](const auto &jcs, auto &&meth)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (const auto &jc : jcs)
        out.emplace_back(meth(jc));
      return out;
    };

    /// This function simply applies the 2 args functions per vector of Rec Particles to a vector of vectors of Rec Particles
    auto cast_constituent_2 = [](const auto &jcs, const auto &coll, auto &&meth)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (const auto &jc : jcs)
      {
        out.emplace_back(meth(jc, coll));
      }
      return out;
    };

    auto cast_constituent_3 = [](const auto &jcs, const auto &coll1, const auto &coll2, auto &&meth)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (const auto &jc : jcs)
      {
        out.emplace_back(meth(jc, coll1, coll2));
      }
      return out;
    };

    auto cast_constituent_4 = [](const auto &jcs, const auto &coll1, const auto &coll2, const auto &coll3, auto &&meth)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (const auto &jc : jcs)
      {
        out.emplace_back(meth(jc, coll1, coll2, coll3));
      }
      return out;
    };

    auto cast_constituent_5 = [](const auto &jcs, const auto &coll1, const auto &coll2, const auto &coll3, const auto &coll4, auto &&meth)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (const auto &jc : jcs)
      {
        out.emplace_back(meth(jc, coll1, coll2, coll3, coll4));
      }
      return out;
    };

    // basic getters
    rv::RVec<FCCAnalysesJetConstituentsData> get_pt(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_pt);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_px(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_px);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_py(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_py);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_pz(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_pz);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_p(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_p);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_e(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_e);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_theta(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_theta);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_phi(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_phi);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_type(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_type);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_charge(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      return cast_constituent(jcs, ReconstructedParticle::get_charge);
    }

    // sorting
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> jets_sorting_on_nconst(const rv::RVec<edm4hep::ReconstructedParticleData> &jets)
    {
      ROOT::VecOps::RVec<int> nconst;
      ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> out;
      for (const auto &jet : jets)
      {
        nconst.push_back(jet.particles_end - jet.particles_begin);
      }
      auto indices = ROOT::VecOps::Argsort(nconst);
      for (int index = 0; index < jets.size(); ++index)
      {
        out.push_back(jets.at(indices.at(indices.size() - 1 - index)));
      }
      return out;
    }

    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> jets_sorting_on_energy(const rv::RVec<edm4hep::ReconstructedParticleData> &jets)
    {
      ROOT::VecOps::RVec<float> energy;
      ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> out;
      for (const auto &jet : jets)
      {
        energy.push_back(jet.energy);
      }
      auto indices = ROOT::VecOps::Argsort(energy);
      for (int index = 0; index < jets.size(); ++index)
      {
        out.push_back(jets.at(indices.at(indices.size() - 1 - index)));
      }
      return out;
    }

    // get basic track properties
    rv::RVec<FCCAnalysesJetConstituentsData> get_chi2(const rv::RVec<FCCAnalysesJetConstituents>& jcs,
                                                    const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_chi2);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_ndof(const rv::RVec<FCCAnalysesJetConstituents>& jcs,
                                                    const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_ndof);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_chi2Normalized(const rv::RVec<FCCAnalysesJetConstituents>& jcs,
                                                    const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_chi2Normalized);
    }

    // get number of track hits in subdetectors
    rv::RVec<FCCAnalysesJetConstituentsData> get_nTrackHits(const rv::RVec<FCCAnalysesJetConstituents>& jcs,
                                                    const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
                                                    const ROOT::VecOps::RVec<int>& subdetectorHitNumbers,
                                                    const int subdetectorNumber,
                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_5(jcs, tracks, subdetectorHitNumbers, subdetectorNumber, reco2track_links,
                                ReconstructedParticle2Track::getRP2TRK_nTrackHits);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_nTrackHits_VDET(const rv::RVec<FCCAnalysesJetConstituents>& jcs,
                                                    const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
                                                    const ROOT::VecOps::RVec<int>& subdetectorHitNumbers,
                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_4(jcs, tracks, subdetectorHitNumbers, reco2track_links,
                                ReconstructedParticle2Track::getRP2TRK_nTrackHits_VDET);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_nTrackHits_ITC(const rv::RVec<FCCAnalysesJetConstituents>& jcs,
                                                    const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
                                                    const ROOT::VecOps::RVec<int>& subdetectorHitNumbers,
                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_4(jcs, tracks, subdetectorHitNumbers, reco2track_links,
                                ReconstructedParticle2Track::getRP2TRK_nTrackHits_ITC);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_nTrackHits_TPC(const rv::RVec<FCCAnalysesJetConstituents>& jcs,
                                                    const ROOT::VecOps::RVec<edm4hep::TrackData>& tracks,
                                                    const ROOT::VecOps::RVec<int>& subdetectorHitNumbers,
                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_4(jcs, tracks, subdetectorHitNumbers, reco2track_links,
                                ReconstructedParticle2Track::getRP2TRK_nTrackHits_TPC);
    }


    // get magnetic field
    rv::RVec<FCCAnalysesJetConstituentsData> get_Bz(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                    const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_Bz);
    }

    // get displacement (w.r.t. nominal origin)
    rv::RVec<FCCAnalysesJetConstituentsData> get_d0(
        const rv::RVec<FCCAnalysesJetConstituents> &jcs,
        const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_D0);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_z0(
        const rv::RVec<FCCAnalysesJetConstituents> &jcs,
        const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_Z0);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_phi0(
        const rv::RVec<FCCAnalysesJetConstituents> &jcs,
        const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_omega(
        const rv::RVec<FCCAnalysesJetConstituents> &jcs,
        const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_omega);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_tanLambda(
        const rv::RVec<FCCAnalysesJetConstituents> &jcs,
        const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_tanLambda);
    }

    // get impact parameters (w.r.t. primary vertex)
    rv::RVec<FCCAnalysesJetConstituentsData> XPtoPar_dxy(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                         const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                         const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links,
                                                         const TLorentzVector &PV,
                                                         const float &Bz)
    {

      return cast_constituent_5(jcs, tracks, reco2track_links, PV, Bz, ReconstructedParticle2Track::XPtoPar_dxy);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> XPtoPar_dz(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                        const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links,
                                                        const TLorentzVector &PV,
                                                        const float &Bz)
    {

      return cast_constituent_5(jcs, tracks, reco2track_links, PV, Bz, ReconstructedParticle2Track::XPtoPar_dz);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> XPtoPar_phi(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                         const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                         const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links,
                                                         const TLorentzVector &PV,
                                                         const float &Bz)
    {

      return cast_constituent_5(jcs, tracks, reco2track_links, PV, Bz, ReconstructedParticle2Track::XPtoPar_phi);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> XPtoPar_C(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                       const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                       const float &Bz)
    {

      return cast_constituent_3(jcs, tracks, Bz, ReconstructedParticle2Track::XPtoPar_C);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> XPtoPar_ct(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                        const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                        const float &Bz)
    {

      return cast_constituent_3(jcs, tracks, Bz, ReconstructedParticle2Track::XPtoPar_ct);
    }

    // Covariance matrix elements of tracks parameters
    // diagonal
    rv::RVec<FCCAnalysesJetConstituentsData> get_omega_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
               const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_omega_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_d0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
            const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_D0_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_z0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
            const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_Z0_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_phi0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
              const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_tanlambda_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                   const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_tanLambda_cov);
    }
    // off-diagonal
    rv::RVec<FCCAnalysesJetConstituentsData> get_d0_z0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
               const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_d0_z0_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_phi0_d0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                 const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_d0_phi0_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_phi0_z0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                 const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi0_z0_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_tanlambda_phi0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                        const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi0_tanlambda_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_tanlambda_d0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                      const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_d0_tanlambda_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_tanlambda_z0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                      const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_z0_tanlambda_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_omega_tanlambda_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                         const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_omega_tanlambda_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_omega_phi0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                    const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi0_omega_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_omega_d0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                              const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_d0_omega_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_omega_z0_cov(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                              const ROOT::VecOps::RVec<edm4hep::TrackState> &trackStates,
        const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links)
    {
      return cast_constituent_3(jcs, trackStates, reco2track_links, ReconstructedParticle2Track::getRP2TRK_omega_z0_cov);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_dndx(
        const rv::RVec<FCCAnalysesJetConstituents> &jetConstituents,
        const TrackUtils::TrackDqdxHandler &dNdxHandler,
        const rv::RVec<edm4hep::TrackData> &trackColl,
        const rv::RVec<FCCAnalysesJetConstituentsData> isJetConstChargedHad) {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      out.reserve(jetConstituents.size());

      for (size_t i = 0; i < jetConstituents.size(); ++i) {
        FCCAnalysesJetConstituents jetConstituentsVec = jetConstituents.at(i);
        FCCAnalysesJetConstituentsData isJetConstChargedHadVec =
            isJetConstChargedHad.at(i);
        FCCAnalysesJetConstituentsData tmp;

        for (size_t j = 0; j < jetConstituentsVec.size(); ++j) {
          if (jetConstituentsVec.at(j).tracks_begin < trackColl.size() &&
              (int)isJetConstChargedHadVec.at(j) == 1) {
            auto trackIndex = jetConstituentsVec.at(j).tracks_begin;

            float dNdx = 0.;
            auto dNdxValues = dNdxHandler.getDqdxValues(trackIndex);
            // Taking only the first value
            if (dNdxValues.size() > 0) {
              dNdx = dNdxValues[0] / 1000.;
            }

            tmp.push_back(dNdx);
          } else {
            tmp.push_back(0.);
          }
        }
        out.push_back(tmp);
      }

      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_Sip2dVal(const rv::RVec<edm4hep::ReconstructedParticleData> &jets,
                                                          const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                          const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                          const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links){
      // calculate signed impact parameter from D0 and phi0 values.
      // for more info on the definition of the signed impact parameter, see below (in get_Sip2dVal_clusterV).
      
      // get D0 and phi0
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      rv::RVec<FCCAnalysesJetConstituentsData> D0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_D0);
      rv::RVec<FCCAnalysesJetConstituentsData> phi0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi);

      for (int i = 0; i < jets.size(); ++i)
      {
        TVector2 p(jets[i].momentum.x, jets[i].momentum.y);
        FCCAnalysesJetConstituentsData cprojs;
        for (int j = 0; j < jcs[i].size(); ++j)
        {
          if (D0.at(i).at(j) != -9)
          {
            TVector2 d0(-D0.at(i).at(j) * TMath::Sin(phi0.at(i).at(j)), D0.at(i).at(j) * TMath::Cos(phi0.at(i).at(j)));
            cprojs.push_back(TMath::Sign(1, d0 * p) * fabs(D0.at(i).at(j)));
          }
          else
          {
            cprojs.push_back(-9.);
          }
        }
        out.push_back(cprojs);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_Sip2dVal_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                  const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                                  const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                                  const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links){
      // calculate signed impact parameter from D0 and phi0 values.
      // for more info on the definition of the signed impact parameter, see below (in get_Sip2dVal_clusterV).

      // get D0 and phi0
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      rv::RVec<FCCAnalysesJetConstituentsData> D0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_D0);
      rv::RVec<FCCAnalysesJetConstituentsData> phi0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi);

      return get_Sip2dVal_clusterV(jets, jcs, D0, phi0);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_Sip2dVal_clusterV(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                   const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                                   const rv::RVec<FCCAnalysesJetConstituentsData> &D0,
                                                                   const rv::RVec<FCCAnalysesJetConstituentsData> &phi0){
      // calculate signed impact parameter from provided D0 and phi0 values.
      // note: this value is defined as:
      //       sign(d * p) * abs(D0)
      //         where d = position vector (in the transverse plane) from reference point to point of closest approach.
      //         where p = momentum vector (in the transvers plane) of the jet.
      //         where D0 = (signed) distance to the point of closest approach.
      //       hence this function returns the same absolute value as the D0 being passed in as an argument;
      //       only the sign is potentially flipped depending on the angle between the PCA and the jet momentum!
      
      // initialize output (will have same shape as D0 and phi0)
      rv::RVec<FCCAnalysesJetConstituentsData> out;

      // loop over jets and jet constituents
      for (int i = 0; i < jets.size(); ++i)
      {
        TVector2 pjet(jets[i].px(), jets[i].py());
        FCCAnalysesJetConstituentsData cprojs;
        for (int j = 0; j < jcs[i].size(); ++j)
        {
          // only consider jet constituents with valid impact parameter
          if (D0.at(i).at(j) != -9)
          {
            TVector2 ptrack(jcs.at(i).at(j).momentum.x, jcs.at(i).at(j).momentum.y);
            TVector2 d0(-D0.at(i).at(j) * TMath::Sin(phi0.at(i).at(j)), D0.at(i).at(j) * TMath::Cos(phi0.at(i).at(j)));
            // option 1: sign from dot product of position vector and jet momentum
            int sign = TMath::Sign(1, d0 * pjet);
            // option 2: sign from dot product of position vector and track momentum
            //int sign = TMath::Sign(1, d0 * ptrack);
            cprojs.push_back(sign * fabs(D0.at(i).at(j)));
          }
          else
          {
            cprojs.push_back(-9.);
          }
        }
        out.push_back(cprojs);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_Sip2dSig(const rv::RVec<FCCAnalysesJetConstituentsData> &Sip2dVals,
                                                          const rv::RVec<FCCAnalysesJetConstituentsData> &err2_D0)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < Sip2dVals.size(); ++i)
      {
        FCCAnalysesJetConstituentsData s;
        for (int j = 0; j < Sip2dVals.at(i).size(); ++j)
        {
          if (err2_D0.at(i).at(j) > 0)
          {
            s.push_back(Sip2dVals.at(i).at(j) / std::sqrt(err2_D0.at(i).at(j)));
          }
          else
          {
            s.push_back(-9);
          }
        }
        out.push_back(s);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_Sip3dVal(const rv::RVec<edm4hep::ReconstructedParticleData> &jets,
                                                          const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                          const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                          const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links){
      // calculate signed impact parameter from D0, Z0 and phi0 values.
      // for more info on the definition of the signed impact parameter, see below (in get_Sip3dVal_clusterV).

      rv::RVec<FCCAnalysesJetConstituentsData> out;
      rv::RVec<FCCAnalysesJetConstituentsData> D0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_D0);
      rv::RVec<FCCAnalysesJetConstituentsData> Z0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_Z0);
      rv::RVec<FCCAnalysesJetConstituentsData> phi0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi);

      for (int i = 0; i < jets.size(); ++i)
      {
        TVector3 p(jets[i].momentum.x, jets[i].momentum.y, jets[i].momentum.z);
        FCCAnalysesJetConstituentsData cprojs;
        for (int j = 0; j < jcs[i].size(); ++j)
        {
          if (D0.at(i).at(j) != -9)
          {
            TVector3 d(-D0.at(i).at(j) * TMath::Sin(phi0.at(i).at(j)), D0.at(i).at(j) * TMath::Cos(phi0.at(i).at(j)), Z0.at(i).at(j));
            cprojs.push_back(TMath::Sign(1, d * p) * fabs(sqrt(D0.at(i).at(j) * D0.at(i).at(j) + Z0.at(i).at(j) * Z0.at(i).at(j))));
          }
          else
          {
            cprojs.push_back(-9);
          }
        }
        out.push_back(cprojs);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_Sip3dVal_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                  const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                                  const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                                  const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links){
      // calculate signed impact parameter from D0, Z0 and phi0 values.
      // for more info on the definition of the signed impact parameter, see below (in get_Sip3dVal_clusterV).
      
      // get D0, Z0 and phi0
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      rv::RVec<FCCAnalysesJetConstituentsData> D0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_D0);
      rv::RVec<FCCAnalysesJetConstituentsData> Z0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_Z0);
      rv::RVec<FCCAnalysesJetConstituentsData> phi0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi);

      return get_Sip3dVal_clusterV(jets, jcs, D0, Z0, phi0);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_Sip3dVal_clusterV(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                   const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                                   const rv::RVec<FCCAnalysesJetConstituentsData> &D0,
                                                                   const rv::RVec<FCCAnalysesJetConstituentsData> &Z0,
                                                                   const rv::RVec<FCCAnalysesJetConstituentsData> &phi0){
      // calculate signed impact parameter from provided D0, Z0 and phi0 values.
      // note: this value is defined as:
      //       sign(d * p) * sqrt(D0**2 + Z0**2)
      //         where d = position vector (in 3D) from reference point to point of closest approach.
      //         where p = momentum vector (in 3D) of the jet.
      //         where D0 = (signed) distance to the point of closest approach in the transverse plane.
      //         where Z0 = (signed) distance to the point of closest approach along the longitudinal axis.
      //       hence this function returns the same absolute value as the D0 and Z0 (summed in quadrature) being passed in as an argument;
      //       only the sign is potentially flipped depending on the angle between the PCA and the jet momentum!
     
      // initialize output (will have same shape as D0, Z0 and phi0)
      rv::RVec<FCCAnalysesJetConstituentsData> out;

      // loop over jets and jet constituents
      for (int i = 0; i < jets.size(); ++i)
      {
        TVector3 pjet(jets[i].px(), jets[i].py(), jets[i].pz());
        FCCAnalysesJetConstituentsData cprojs;
        for (int j = 0; j < jcs[i].size(); ++j)
        {
          // only consider jet constituents with valid impact parameter
          if (D0.at(i).at(j) != -9)
          {
            TVector3 ptrack(jcs.at(i).at(j).momentum.x, jcs.at(i).at(j).momentum.y, jcs.at(i).at(j).momentum.z);
            TVector3 d(-D0.at(i).at(j) * TMath::Sin(phi0.at(i).at(j)), D0.at(i).at(j) * TMath::Cos(phi0.at(i).at(j)), Z0.at(i).at(j));
            // option 1: sign from dot product between position vector and jet momentum
            int sign = TMath::Sign(1, d * pjet);
            // option 2: sign from dot product between position vector and track momentum
            //int sign = TMath::Sign(1, d * ptrack);
            cprojs.push_back(sign * fabs(sqrt(D0.at(i).at(j) * D0.at(i).at(j) + Z0.at(i).at(j) * Z0.at(i).at(j))));
          }
          else
          {
            cprojs.push_back(-9);
          }
        }
        out.push_back(cprojs);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_Sip3dSig(const rv::RVec<FCCAnalysesJetConstituentsData> &Sip3dVals,
                                                          const rv::RVec<FCCAnalysesJetConstituentsData> &err2_D0,
                                                          const rv::RVec<FCCAnalysesJetConstituentsData> &err2_Z0)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < Sip3dVals.size(); ++i)
      {
        FCCAnalysesJetConstituentsData s;
        for (int j = 0; j < Sip3dVals.at(i).size(); ++j)
        {
          if (err2_D0.at(i).at(j) > 0.)
          {
            s.push_back(Sip3dVals.at(i).at(j) / sqrt(err2_D0.at(i).at(j) + err2_Z0.at(i).at(j)));
          }
          else
          {
            s.push_back(-9);
          }
        }
        out.push_back(s);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_JetPlaneDistVal(const rv::RVec<edm4hep::ReconstructedParticleData> &jets,
                                                            const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                            const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                            const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links){
      // calculate jet-distance from D0, Z0 and phi0 values.
      // for more info on the definition of the jet-distance, see below (in get_JetDistVal_clusterV).

      // get D0, Z0 and phi0
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      rv::RVec<FCCAnalysesJetConstituentsData> D0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_D0);
      rv::RVec<FCCAnalysesJetConstituentsData> Z0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_Z0);
      rv::RVec<FCCAnalysesJetConstituentsData> phi0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi);
      
      for (int i = 0; i < jets.size(); ++i)
      {
        FCCAnalysesJetConstituentsData tmp;
        TVector3 p_jet(jets[i].momentum.x, jets[i].momentum.y, jets[i].momentum.z);
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
          if (D0.at(i).at(j) != -9)
          {
            TVector3 d(-D0.at(i).at(j) * TMath::Sin(phi0.at(i).at(j)), D0.at(i).at(j) * TMath::Cos(phi0.at(i).at(j)), Z0.at(i).at(j));
            TVector3 p_ct(ct[j].momentum.x, ct[j].momentum.y, ct[j].momentum.z);
            TVector3 r_jet(0.0, 0.0, 0.0);
            TVector3 n = p_ct.Cross(p_jet).Unit(); // What if they are parallel?
            tmp.push_back(n.Dot(d - r_jet));
          }
          else
          {
            tmp.push_back(-9);
          }
        }
        out.push_back(tmp);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_JetPlaneDistVal_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                    const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                                    const ROOT::VecOps::RVec<edm4hep::TrackState> &tracks,
                                                                    const ROOT::VecOps::RVec<podio::ObjectID>& reco2track_links){
      // calculate jet-distance from D0, Z0 and phi0 values.
      // for more info on the definition of the jet-distance, see below (in get_JetDistVal_clusterV).

      // get D0, Z0 and phi0
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      rv::RVec<FCCAnalysesJetConstituentsData> D0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_D0);
      rv::RVec<FCCAnalysesJetConstituentsData> Z0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_Z0);
      rv::RVec<FCCAnalysesJetConstituentsData> phi0 = cast_constituent_3(jcs, tracks, reco2track_links, ReconstructedParticle2Track::getRP2TRK_phi);
    
      return get_JetPlaneDistVal_clusterV(jets, jcs, D0, Z0, phi0);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_JetPlaneDistVal_clusterV(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                     const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                                     const rv::RVec<FCCAnalysesJetConstituentsData> &D0,
                                                                     const rv::RVec<FCCAnalysesJetConstituentsData> &Z0,
                                                                     const rv::RVec<FCCAnalysesJetConstituentsData> &phi0){
      // calculate distance between a track and the jet-track plane from provided D0, Z0 and phi0 values.
      // note: the jet-distance is define as:
      //       (p_ct x p_jet).unit() * d
      //       where p_ct is the jet constituent momentum vector,
      //       where p_jet is the jet momentum vector,
      //       where (p_ct x p_jet).unit() is the unit vector in the direction of the cross-product between p_ct and p_jet,
      //       where d is the position vector from the reference point to the point of closest approach.
      //       Intuitively, this seems to imply a measure for how far the track sits outside the jet-track plane.
      
      // initialize output (will have same shape as D0, Z0 and phi0)
      rv::RVec<FCCAnalysesJetConstituentsData> out;

      // loop over jets and jet constituents
      for (int i = 0; i < jets.size(); ++i)
      {
        FCCAnalysesJetConstituentsData tmp;
        TVector3 p_jet(jets[i].px(), jets[i].py(), jets[i].pz());
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
          if (D0.at(i).at(j) != -9)
          {
            TVector3 d(-D0.at(i).at(j) * TMath::Sin(phi0.at(i).at(j)), D0.at(i).at(j) * TMath::Cos(phi0.at(i).at(j)), Z0.at(i).at(j));
            TVector3 p_ct(ct[j].momentum.x, ct[j].momentum.y, ct[j].momentum.z);
            TVector3 r_jet(0.0, 0.0, 0.0);
            TVector3 n = p_ct.Cross(p_jet).Unit(); // What if they are parallel?
            tmp.push_back(n.Dot(d - r_jet));
          }
          else
          {
            tmp.push_back(-9);
          }
        }
        out.push_back(tmp);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_JetPlaneDistSig(const rv::RVec<FCCAnalysesJetConstituentsData> &JetDistVal,
                                                            const rv::RVec<FCCAnalysesJetConstituentsData> &err2_D0,
                                                            const rv::RVec<FCCAnalysesJetConstituentsData> &err2_Z0)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < JetDistVal.size(); ++i)
      {
        FCCAnalysesJetConstituentsData tmp;
        for (int j = 0; j < JetDistVal.at(i).size(); ++j)
        {
          if (err2_D0.at(i).at(j) > 0)
          {
            float err3d = std::sqrt(err2_D0.at(i).at(j) + err2_Z0.at(i).at(j));
            float jetdistsig = JetDistVal.at(i).at(j) / err3d;
            tmp.push_back(jetdistsig);
          }
          else
          {
            tmp.push_back(-9.);
          }
        }
        out.push_back(tmp);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_JetOrthogonalDistVal_clusterV(
        const rv::RVec<fastjet::PseudoJet> &jets,
        const rv::RVec<FCCAnalysesJetConstituents> &jcs,
        const rv::RVec<FCCAnalysesJetConstituentsData> &D0,
        const rv::RVec<FCCAnalysesJetConstituentsData> &Z0,
        const rv::RVec<FCCAnalysesJetConstituentsData> &phi0){
      // calculate (orthogonal) distance between a track and a jet from provided D0, Z0 and phi0 values.
      // note: this distance is define as: todo

      // initialize output (will have same shape as D0, Z0 and phi0)
      rv::RVec<FCCAnalysesJetConstituentsData> out;

      // loop over jets and jet constituents
      for (int i = 0; i < jets.size(); ++i)
      {
        FCCAnalysesJetConstituentsData tmp;
        TVector3 p_jet(jets[i].px(), jets[i].py(), jets[i].pz());
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
          if (D0.at(i).at(j) != -9)
          {
            // dummy, actual implementation to do...
            tmp.push_back(-9);
          }
          else
          {
            tmp.push_back(-9);
          }
        }
        out.push_back(tmp);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_JetOrthogonalDistSig(
        const rv::RVec<FCCAnalysesJetConstituentsData> &JetOrthogonalDistVal,
        const rv::RVec<FCCAnalysesJetConstituentsData> &err2_D0,
        const rv::RVec<FCCAnalysesJetConstituentsData> &err2_Z0){

        return get_JetPlaneDistSig(JetOrthogonalDistVal, err2_D0, err2_Z0);
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_JetParallelDistVal_clusterV(
        const rv::RVec<fastjet::PseudoJet> &jets,
        const rv::RVec<FCCAnalysesJetConstituents> &jcs,
        const rv::RVec<FCCAnalysesJetConstituentsData> &D0,
        const rv::RVec<FCCAnalysesJetConstituentsData> &Z0,
        const rv::RVec<FCCAnalysesJetConstituentsData> &phi0){
      // calculate (parallel) distance between a track and a jet from provided D0, Z0 and phi0 values.
      // note: this distance is define as: todo

      // initialize output (will have same shape as D0, Z0 and phi0)
      rv::RVec<FCCAnalysesJetConstituentsData> out;

      // loop over jets and jet constituents
      for (int i = 0; i < jets.size(); ++i)
      {
        FCCAnalysesJetConstituentsData tmp;
        TVector3 p_jet(jets[i].px(), jets[i].py(), jets[i].pz());
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
          if (D0.at(i).at(j) != -9)
          {
            // dummy, actual implementation to do...
            tmp.push_back(-9);
          }
          else
          {
            tmp.push_back(-9);
          }
        }
        out.push_back(tmp);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_JetParallelDistSig(
        const rv::RVec<FCCAnalysesJetConstituentsData> &JetOrthogonalDistVal,
        const rv::RVec<FCCAnalysesJetConstituentsData> &err2_D0,
        const rv::RVec<FCCAnalysesJetConstituentsData> &err2_Z0){

        return get_JetPlaneDistSig(JetOrthogonalDistVal, err2_D0, err2_Z0);
    }


    // we measure L, tof; mtof in GeV
    // neutrals are set to 0; muons and electrons are set to their mass;
    //  only charged hads are considered (mtof used to disctriminate charged kaons and pions)

    // eventually will have to update this function to compute tof with respect to hard vertex
    // reconstructed with a 4D algorithm

    // TODO:
    // - extend MC vertex method to 4-vector to have time as well
    // - recompute neutral L here using Vertex pos
    // - check if approx possible for charged as well
    // - use Tin from vertex
    rv::RVec<FCCAnalysesJetConstituentsData> get_mtof(const rv::RVec<FCCAnalysesJetConstituents> &jcs,
                                                      const rv::RVec<float> &track_L,
                                                      const rv::RVec<edm4hep::TrackData> &trackdata,
                                                      const rv::RVec<edm4hep::TrackerHit3DData> &trackerhits,
                                                      const rv::RVec<edm4hep::ClusterData> &gammadata,
                                                      const rv::RVec<edm4hep::ClusterData> &nhdata,
                                                      const rv::RVec<edm4hep::CalorimeterHitData> &calohits,
                                                      const TLorentzVector &V // primary vertex position and time in mm
    )
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < jcs.size(); ++i)
      {
        FCCAnalysesJetConstituents ct = jcs.at(i);
        FCCAnalysesJetConstituentsData tmp;
        for (int j = 0; j < ct.size(); ++j)
        {
          if (ct.at(j).clusters_begin < nhdata.size() + gammadata.size())
          {
#if edm4hep_VERSION > EDM4HEP_VERSION(0, 10, 5)
            if (ct.at(j).PDG == 130)
#else
            if (ct.at(j).type == 130)
#endif
            {
              // this assumes that in converter photons are filled first and nh after
              float T = calohits.at(nhdata.at(ct.at(j).clusters_begin - gammadata.size()).hits_begin).time;
              float X = calohits.at(nhdata.at(ct.at(j).clusters_begin - gammadata.size()).hits_begin).position.x;
              float Y = calohits.at(nhdata.at(ct.at(j).clusters_begin - gammadata.size()).hits_begin).position.y;
              float Z = calohits.at(nhdata.at(ct.at(j).clusters_begin - gammadata.size()).hits_begin).position.z;

              float tof = T;
              // compute path length wrt to PV
              float L = std::sqrt((X - V.X()) * (X - V.X()) + (Y - V.Y()) * (Y - V.Y()) + (Z - V.Z()) * (Z - V.Z())) * 0.001;
              // std::cout << "tof n: " << T << "  -  L: " << L << std::endl;
              float beta = L / (tof * 2.99792458e+8);
              float E = ct.at(j).energy;
              // std::cout << "tof: " << tof << " - L: " << L << " - beta: " << beta << " - energy: " << E <<" - true PID: "<<abs(pids.at(j))<<std::endl;
              if (beta < 1. && beta > 0.)
              {
                tmp.push_back(E * std::sqrt(1 - beta * beta));
                // std::cout << "mtof n:" << E * std::sqrt(1-beta*beta)<< std::endl;
              }
              else
              {
                // std::cout << "problem" << std::endl;
                tmp.push_back((9.));
              }
            }
#if edm4hep_VERSION > EDM4HEP_VERSION(0, 10, 5)
            else if (ct.at(j).PDG == 22)
#else
            else if (ct.at(j).type == 22)
#endif
            {
              tmp.push_back((0.));
            }
          }

          if (ct.at(j).tracks_begin < trackdata.size())
          {
            if (abs(ct.at(j).charge) > 0 and abs(ct.at(j).mass - 0.000510999) < 1.e-05)
            {
              tmp.push_back(0.000510999);
            }
            else if (abs(ct.at(j).charge) > 0 and abs(ct.at(j).mass - 0.105658) < 1.e-03)
            {
              tmp.push_back(0.105658);
            }
            else
            {

              // this is the time of the track origin from MC
              // float Tin = trackerhits.at(trackdata.at(ct.at(j).tracks_begin).trackerHits_begin).time;

              // time given by primary vertex
              float Tin = V.T() * 1e-3 / 2.99792458e+8;

              float Tout = trackerhits.at(trackdata.at(ct.at(j).tracks_begin).trackerHits_end - 1).time; // one track and 3 hits per recon. particle are assumed
              float tof = (Tout - Tin);

              // TODO: path length will have to be re-calculated from vertex position
              float L = track_L.at(ct.at(j).tracks_begin) * 0.001;
              // std::cout << "tof: " << tof << "  -  L: " << L << std::endl;
              float beta = L / (tof * 2.99792458e+8);
              float p = std::sqrt(ct.at(j).momentum.x * ct.at(j).momentum.x + ct.at(j).momentum.y * ct.at(j).momentum.y + ct.at(j).momentum.z * ct.at(j).momentum.z);
              // std::cout << "tof: " << tof << " - L: " << L << " - beta: " << beta << " - momentum: " << p << " - mtof: " << p * std::sqrt(1/(beta*beta)-1) << std::endl;
              if (beta < 1. && beta > 0.)
              {
                tmp.push_back(p * std::sqrt(1 / (beta * beta) - 1));
              }
              else
              {
                tmp.push_back(0.13957039);
              }
            }
          }
        }
        out.push_back(tmp);
      }
      return out;
    }

    // kinematics const/jet
    rv::RVec<FCCAnalysesJetConstituentsData> get_erel_log(const rv::RVec<edm4hep::ReconstructedParticleData> &jets,
                                                          const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        float e_jet = jets.at(i).energy;
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          float val = (e_jet > 0.) ? jc.energy / e_jet : 1.;
          float erel_log = float(std::log10(val));
          jet_csts.emplace_back(erel_log);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_erel_log_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                  const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        float e_jet = jets.at(i).E();
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          float val = (e_jet > 0.) ? jc.energy / e_jet : 1.;
          float erel_log = float(std::log10(val));
          jet_csts.emplace_back(erel_log);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_ptrel_log_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                   const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        float pt_jet = jets.at(i).pt();
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          TLorentzVector jcvec;
          jcvec.SetXYZM(jc.momentum.x, jc.momentum.y, jc.momentum.z, jc.mass);
          float val = (pt_jet > 0.) ? jcvec.Pt() / pt_jet : 1.;
          float ptrel_log = float(std::log10(val));
          jet_csts.emplace_back(ptrel_log);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_erel(const rv::RVec<edm4hep::ReconstructedParticleData> &jets,
                                                      const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        double e_jet = jets.at(i).energy;
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          float val = (e_jet > 0.) ? jc.energy / e_jet : 1.;
          float erel = val;
          jet_csts.emplace_back(erel);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_erel_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                              const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        double e_jet = jets.at(i).E();
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          float val = (e_jet > 0.) ? jc.energy / e_jet : 1.;
          float erel = val;
          jet_csts.emplace_back(erel);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_ptrel_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                               const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        double pt_jet = jets.at(i).pt();
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          TLorentzVector jcvec;
          jcvec.SetXYZM(jc.momentum.x, jc.momentum.y, jc.momentum.z, jc.mass);
          float val = (pt_jet > 0.) ? jcvec.Pt() / pt_jet : 1.;
          float ptrel = val;
          jet_csts.emplace_back(ptrel);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_thetarel(const rv::RVec<edm4hep::ReconstructedParticleData> &jets,
                                                          const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        TLorentzVector tlv_jet;
        tlv_jet.SetXYZM(jets.at(i).momentum.x, jets.at(i).momentum.y, jets.at(i).momentum.z, jets.at(i).mass);
        float theta_jet = tlv_jet.Theta();
        float phi_jet = tlv_jet.Phi();
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          TLorentzVector tlv_const;
          tlv_const.SetXYZM(jc.momentum.x, jc.momentum.y, jc.momentum.z, jc.mass);
          TVector3 v_const = tlv_const.Vect();
          v_const.RotateZ(-phi_jet);
          v_const.RotateY(-theta_jet);
          float theta_rel = v_const.Theta();
          jet_csts.emplace_back(theta_rel);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_thetarel_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                  const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        TLorentzVector tlv_jet;
        tlv_jet.SetXYZM(jets.at(i).px(), jets.at(i).py(), jets.at(i).pz(), jets.at(i).m());
        float theta_jet = tlv_jet.Theta();
        float phi_jet = tlv_jet.Phi();
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          TLorentzVector tlv_const;
          tlv_const.SetXYZM(jc.momentum.x, jc.momentum.y, jc.momentum.z, jc.mass);
          TVector3 v_const = tlv_const.Vect();
          v_const.RotateZ(-phi_jet);
          v_const.RotateY(-theta_jet);
          float theta_rel = v_const.Theta();
          jet_csts.emplace_back(theta_rel);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_phirel(const rv::RVec<edm4hep::ReconstructedParticleData> &jets,
                                                        const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        TLorentzVector tlv_jet;
        tlv_jet.SetXYZM(jets.at(i).momentum.x, jets.at(i).momentum.y, jets.at(i).momentum.z, jets.at(i).mass);
        float theta_jet = tlv_jet.Theta();
        float phi_jet = tlv_jet.Phi();
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          TLorentzVector tlv_const;
          tlv_const.SetXYZM(jc.momentum.x, jc.momentum.y, jc.momentum.z, jc.mass);
          TVector3 v_const = tlv_const.Vect();
          v_const.RotateZ(-phi_jet);
          v_const.RotateY(-theta_jet);
          float phi_rel = v_const.Phi();
          jet_csts.emplace_back(phi_rel);
        }
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_phirel_cluster(const rv::RVec<fastjet::PseudoJet> &jets,
                                                                const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (size_t i = 0; i < jets.size(); ++i)
      {
        auto &jet_csts = out.emplace_back();
        TLorentzVector tlv_jet;
        tlv_jet.SetXYZM(jets.at(i).px(), jets.at(i).py(), jets.at(i).pz(), jets.at(i).m());
        float theta_jet = tlv_jet.Theta();
        float phi_jet = tlv_jet.Phi();
        auto csts = get_jet_constituents(jcs, i);
        for (const auto &jc : csts)
        {
          TLorentzVector tlv_const;
          tlv_const.SetXYZM(jc.momentum.x, jc.momentum.y, jc.momentum.z, jc.mass);
          TVector3 v_const = tlv_const.Vect();
          v_const.RotateZ(-phi_jet);
          v_const.RotateY(-theta_jet);
          float phi_rel = v_const.Phi();
          jet_csts.emplace_back(phi_rel);
        }
      }
      return out;
    }

    // Identification

    rv::RVec<FCCAnalysesJetConstituentsData> get_PIDs(const ROOT::VecOps::RVec<int> recin,
                                                      const ROOT::VecOps::RVec<int> mcin,
                                                      const rv::RVec<edm4hep::ReconstructedParticleData> &RecPart,
                                                      const rv::RVec<edm4hep::MCParticleData> &Particle,
                                                      const rv::RVec<edm4hep::ReconstructedParticleData> &jets)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      FCCAnalysesJetConstituentsData PIDs = FCCAnalyses::ReconstructedParticle2MC::getRP2MC_pdg(recin, mcin, RecPart, Particle);

      for (const auto &jet : jets)
      {
        FCCAnalysesJetConstituentsData tmp;
        for (auto it = jet.particles_begin; it < jet.particles_end; ++it)
        {
          tmp.push_back(PIDs.at(it));
        }
        out.push_back(tmp);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_PIDs_cluster(const ROOT::VecOps::RVec<int> recin,
                                                              const ROOT::VecOps::RVec<int> mcin,
                                                              // const rv::RVec<FCCAnalysesJetConstituents>& jcs,
                                                              const rv::RVec<edm4hep::ReconstructedParticleData> &RecPart,
                                                              const rv::RVec<edm4hep::MCParticleData> &Particle,
                                                              const std::vector<std::vector<int>> &indices)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      FCCAnalysesJetConstituentsData PIDs = FCCAnalyses::ReconstructedParticle2MC::getRP2MC_pdg(recin, mcin, RecPart, Particle);

      for (const auto &jet_index : indices)
      {
        FCCAnalysesJetConstituentsData tmp;
        for (const auto &const_index : jet_index)
        {
          tmp.push_back(PIDs.at(const_index));
        }
        out.push_back(tmp);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_isEl(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < jcs.size(); ++i)
      {
        FCCAnalysesJetConstituentsData is_El;
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
          if (abs(ct.at(j).charge) > 0 and abs(ct.at(j).mass - 0.000510999) < 1.e-05)
          {
            is_El.push_back(1.);
          }
          else
          {
            is_El.push_back(0.);
          }
        }

        out.push_back(is_El);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_isMu(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < jcs.size(); ++i)
      {
        FCCAnalysesJetConstituentsData is_Mu;
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
          if (abs(ct.at(j).charge) > 0 and abs(ct.at(j).mass - 0.105658) < 1.e-03)
          {
            is_Mu.push_back(1.);
          }
          else
          {
            is_Mu.push_back(0.);
          }
        }

        out.push_back(is_Mu);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_isChargedHad(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < jcs.size(); ++i)
      {
        FCCAnalysesJetConstituentsData is_ChargedHad;
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
          if (abs(ct.at(j).charge) > 0 and abs(ct.at(j).mass - 0.13957) < 1.e-03)
          {
            is_ChargedHad.push_back(1.);
          }
          else
          {
            is_ChargedHad.push_back(0.);
          }
        }

        out.push_back(is_ChargedHad);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_isNeutralHad(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < jcs.size(); ++i)
      {
        FCCAnalysesJetConstituentsData is_NeutralHad;
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
#if edm4hep_VERSION > EDM4HEP_VERSION(0, 10, 5)
          if (ct.at(j).PDG == 130)
#else
          if (ct.at(j).type == 130)
#endif
          {
            is_NeutralHad.push_back(1.);
          }
          else
            is_NeutralHad.push_back(0.);
        }
        out.push_back(is_NeutralHad);
      }
      return out;
    }

    rv::RVec<FCCAnalysesJetConstituentsData> get_isGamma(const rv::RVec<FCCAnalysesJetConstituents> &jcs)
    {
      rv::RVec<FCCAnalysesJetConstituentsData> out;
      for (int i = 0; i < jcs.size(); ++i)
      {
        FCCAnalysesJetConstituentsData is_NeutralHad;
        FCCAnalysesJetConstituents ct = jcs.at(i);
        for (int j = 0; j < ct.size(); ++j)
        {
#if edm4hep_VERSION > EDM4HEP_VERSION(0, 10, 5)
          if (ct.at(j).PDG == 22)
#else
          if (ct.at(j).type == 22)
#endif
          {
            is_NeutralHad.push_back(1.);
          }
          else
            is_NeutralHad.push_back(0.);
        }
        out.push_back(is_NeutralHad);
      }
      return out;
    }

    // countings
    int count_jets(rv::RVec<FCCAnalysesJetConstituents> jets)
    {
      return jets.size();
    }

    rv::RVec<int> count_consts(rv::RVec<FCCAnalysesJetConstituents> jets)
    {
      rv::RVec<int> out;
      for (int i = 0; i < jets.size(); ++i)
      {
        out.push_back(jets.at(i).size());
      }
      return out;
    }

    rv::RVec<int> count_type(const rv::RVec<FCCAnalysesJetConstituentsData> &isType)
    {
      rv::RVec<int> out;
      for (int i = 0; i < isType.size(); ++i)
      {
        int count = 0;
        rv::RVec<float> istype = isType.at(i);
        for (int j = 0; j < istype.size(); ++j)
        {
          if ((int)(istype.at(j)) == 1)
            count++;
        }
        out.push_back(count);
      }
      return out;
    }

    // compute residues
    rv::RVec<TLorentzVector> compute_tlv_jets(const rv::RVec<fastjet::PseudoJet> &jets)
    {
      rv::RVec<TLorentzVector> out;
      for (const auto &jet : jets)
      {
        TLorentzVector tlv_jet;
        tlv_jet.SetPxPyPzE(jet.px(), jet.py(), jet.pz(), jet.E());
        out.push_back(tlv_jet);
      }
      return out;
    }

    rv::RVec<TLorentzVector> sum_tlv_constituents(const rv::RVec<FCCAnalysesJetConstituents> &jets)
    {
      rv::RVec<TLorentzVector> out;
      for (int i = 0; i < jets.size(); ++i)
      {
        TLorentzVector sum_tlv; // initialized by (0., 0., 0., 0.)
        FCCAnalysesJetConstituents jcs = jets.at(i);
        for (const auto &jc : jcs)
        {
          TLorentzVector tlv;
          tlv.SetPxPyPzE(jc.momentum.x, jc.momentum.y, jc.momentum.z, jc.energy);
          sum_tlv += tlv;
        }
        out.push_back(sum_tlv);
      }
      return out;
    }

    float InvariantMass(const TLorentzVector &tlv1, const TLorentzVector &tlv2)
    {
      float E = tlv1.E() + tlv2.E();
      float px = tlv1.Px() + tlv2.Px();
      float py = tlv1.Py() + tlv2.Py();
      float pz = tlv1.Pz() + tlv2.Pz();
      return std::sqrt(E * E - px * px - py * py - pz * pz);
    }


    rv::RVec<double> all_invariant_masses(rv::RVec<TLorentzVector> AllJets) {

      TLorentzVector tlv1;
      TLorentzVector tlv2;
      double E, px, py, pz; 
      double invmass; 
      
      rv::RVec<double> InvariantMasses;

      if(AllJets.size() < 2) return InvariantMasses;

      // For each jet, take its invariant mass with the remaining jets. Stop at last jet.
      for(int i = 0; i < AllJets.size()-1; ++i) {

        tlv1 = AllJets.at(i); 

        for(int j=i+1; j < AllJets.size(); ++j){ // go until end
          tlv2 = AllJets.at(j);
          E = tlv1.E() + tlv2.E();
          px = tlv1.Px() + tlv2.Px();
          py = tlv1.Py() + tlv2.Py();
          pz = tlv1.Pz() + tlv2.Pz();

          invmass = std::sqrt(E*E - px*px - py*py - pz*pz);
          InvariantMasses.push_back(invmass);

        }
      }

      return InvariantMasses;
    }    

    rv::RVec<double> compute_residue_energy(const rv::RVec<TLorentzVector>& tlv_jet, const rv::RVec<TLorentzVector>& sum_tlv_jcs) {
    
      rv::RVec<double> out;
      for (int i = 0; i < tlv_jet.size(); ++i)
      {
        float de = (sum_tlv_jcs.at(i).E() - tlv_jet.at(i).E()) / tlv_jet.at(i).E();
        out.push_back(de);
      }
      return out;
    }

    rv::RVec<double> compute_residue_px(const rv::RVec<TLorentzVector> &tlv_jet, const rv::RVec<TLorentzVector> &sum_tlv_jcs)
    {
      rv::RVec<double> out;
      for (int i = 0; i < tlv_jet.size(); ++i)
      {
        float dpx = (sum_tlv_jcs.at(i).Px() - tlv_jet.at(i).Px()) / tlv_jet.at(i).Px();
        out.push_back(dpx);
      }
      return out;
    }

    rv::RVec<double> compute_residue_py(const rv::RVec<TLorentzVector> &tlv_jet, const rv::RVec<TLorentzVector> &sum_tlv_jcs)
    {
      rv::RVec<double> out;
      for (int i = 0; i < tlv_jet.size(); ++i)
      {
        float dpy = (sum_tlv_jcs.at(i).Py() - tlv_jet.at(i).Py()) / tlv_jet.at(i).Py();
        out.push_back(dpy);
      }
      return out;
    }

    rv::RVec<double> compute_residue_pz(const rv::RVec<TLorentzVector> &tlv_jet, const rv::RVec<TLorentzVector> &sum_tlv_jcs)
    {
      rv::RVec<double> out;
      for (int i = 0; i < tlv_jet.size(); ++i)
      {
        float dpz = (sum_tlv_jcs.at(i).Pz() - tlv_jet.at(i).Pz()) / tlv_jet.at(i).Pz();
        out.push_back(dpz);
      }
      return out;
    }

    rv::RVec<double> compute_residue_pt(const rv::RVec<TLorentzVector> &tlv_jet, const rv::RVec<TLorentzVector> &sum_tlv_jcs)
    {
      rv::RVec<double> out;
      for (int i = 0; i < tlv_jet.size(); ++i)
      {
        double pt_jet = std::sqrt(tlv_jet.at(i).Px() * tlv_jet.at(i).Px() + tlv_jet.at(i).Py() * tlv_jet.at(i).Py());
        double pt_jcs = std::sqrt(sum_tlv_jcs.at(i).Px() * sum_tlv_jcs.at(i).Px() + sum_tlv_jcs.at(i).Py() * sum_tlv_jcs.at(i).Py());
        double dpt = (pt_jcs - pt_jet) / pt_jet;
        out.push_back(dpt);
      }
      return out;
    }

    rv::RVec<double> compute_residue_phi(const rv::RVec<TLorentzVector> &tlv_jet, const rv::RVec<TLorentzVector> &sum_tlv_jcs)
    {
      rv::RVec<double> out;
      for (int i = 0; i < tlv_jet.size(); ++i)
      {
        double phi_jet = tlv_jet.at(i).Phi();
        double phi_jcs = sum_tlv_jcs.at(i).Phi();
        double dphi = (phi_jcs - phi_jet) / phi_jet;
        out.push_back(dphi);
      }
      return out;
    }

    rv::RVec<double> compute_residue_theta(const rv::RVec<TLorentzVector> &tlv_jet, const rv::RVec<TLorentzVector> &sum_tlv_jcs)
    {
      rv::RVec<double> out;
      for (int i = 0; i < tlv_jet.size(); ++i)
      {
        double theta_jet = tlv_jet.at(i).Theta();
        double theta_jcs = sum_tlv_jcs.at(i).Theta();
        double dtheta = (theta_jcs - theta_jet) / theta_jet;
        out.push_back(dtheta);
      }
      return out;
    }

  } // namespace JetConstituentsUtils
} // namespace FCCAnalyses
