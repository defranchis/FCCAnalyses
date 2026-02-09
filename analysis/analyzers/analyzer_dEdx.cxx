// Tools for collecting the dEdx information for jet constituents

// Orginally copied from here:
// https://github.com/Apranikstar/Aleph/blob/main/src/analyzer.h

#include <ROOT/RVec.hxx>

#include "FCCAnalyses/JetConstituentsUtils.h"
#include "FCCAnalyses/ReconstructedParticle.h"
#include "FCCAnalyses/ReconstructedParticle2Track.h"

#include "edm4hep/MCParticleData.h"
#include "edm4hep/Track.h"
#include "edm4hep/TrackData.h"
#include "edm4hep/ReconstructedParticleData.h"
#include "edm4hep/RecDqdx.h"

#include <iostream>
#include <algorithm>


namespace dEdxTools{

namespace rv = ROOT::VecOps;
using FCCAnalysesJetConstituents = rv::RVec<edm4hep::ReconstructedParticleData>;
using FCCAnalysesJetConstituentsData = rv::RVec<float>;

struct build_constituents_dEdx{
    rv::RVec<rv::RVec<edm4hep::RecDqdxData>>
    operator()(const rv::RVec<edm4hep::ReconstructedParticleData> &recoParticles,
             const rv::RVec<int> &_recoParticlesIndices,
             const rv::RVec<edm4hep::RecDqdxData> &dEdxCollection,
             const rv::RVec<int> &_dEdxIndicesCollection, 
             const std::vector<std::vector<int>> &jet_indices) const
    { 
        rv::RVec<rv::RVec<edm4hep::RecDqdxData>> dedx_constituents;

        // The links dEdx -> Track and RecoPart -> Track are one-directional, we need a map to store
        // Track.index -> dEdx to not have to loop everytime 
        // in addition, the object itself is stored in <Collection>
        // while the relations (=indices we need for links) are on _<Collection>
        std::unordered_map<int, edm4hep::RecDqdxData> track_index_to_dEdx;
        for (size_t i = 0; i < _dEdxIndicesCollection.size(); ++i) {
          int track_index = _dEdxIndicesCollection[i];
          edm4hep::RecDqdxData dedx_value = dEdxCollection[i];
          track_index_to_dEdx[track_index] = dedx_value;
        }

        // Define dummy for particles with no track or for which no dEdx measurement is found
        edm4hep::RecDqdxData dummy{};
        dummy.dQdx.type = -1.f;
        dummy.dQdx.value = -1.f;
        dummy.dQdx.error = -1.f;

        // Now, for each jet loop over the indices of the jet constituents provided by teh JetClusteringUtils
        // retrieve the associated RecoParticle
        // from there get the link to the Track from the corresponding index collection
        for (const auto &jet_const_indices : jet_indices) { //loop over jets
          rv::RVec<edm4hep::RecDqdxData> jet_dEdx;

          for (int constituent_index : jet_const_indices) { // loop over jet constituents
            const auto &recoPart = recoParticles[constituent_index];

            // Find track associated to this reco particle
            if( recoPart.tracks_begin == recoPart.tracks_end ){
                // Case of no track (e.g. neutral particles)
                jet_dEdx.push_back(dummy);
            }
            else{
                // Case of single track (e.g. charged particles)
                int track_index = _recoParticlesIndices.at(recoPart.tracks_begin);
                
                // Find the matching dEdx in the map
                if (track_index_to_dEdx.count(track_index)) {
                    jet_dEdx.push_back(track_index_to_dEdx[track_index]);
                 }
                 else{ jet_dEdx.push_back(dummy); }
            }
          }
          dedx_constituents.push_back(jet_dEdx); 
        }
        return dedx_constituents;
    }
};

//helpers to read the dEdx objects (to check if can reuse existing FCCAna functions instead):

rv::RVec<rv::RVec<float>> get_dEdx_type(const rv::RVec<rv::RVec<edm4hep::RecDqdxData>> &dedx_vec) {
  rv::RVec<rv::RVec<float>> values;
  for (const auto &inner_vec : dedx_vec) {
    rv::RVec<float> inner_values;
    for (const auto &d : inner_vec) {
      inner_values.push_back(d.dQdx.type);
    }
    values.push_back(inner_values);
  }
  return values;
}

rv::RVec<rv::RVec<float>> get_dEdx_value(const rv::RVec<rv::RVec<edm4hep::RecDqdxData>> &dedx_vec) {
  rv::RVec<rv::RVec<float>> values;
  for (const auto &inner_vec : dedx_vec) {
    rv::RVec<float> inner_values;
    for (const auto &d : inner_vec) {
      inner_values.push_back(d.dQdx.value);
    }
    values.push_back(inner_values);
  }
  return values;
}

rv::RVec<rv::RVec<float>> get_dEdx_error(const rv::RVec<rv::RVec<edm4hep::RecDqdxData>> &dedx_vec) {
  rv::RVec<rv::RVec<float>> values;
  for (const auto &inner_vec : dedx_vec) {
    rv::RVec<float> inner_values;
    for (const auto &d : inner_vec) {
      inner_values.push_back(d.dQdx.error);
    }
    values.push_back(inner_values);
  }
  return values;
}

}
