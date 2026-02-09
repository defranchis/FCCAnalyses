// Tools for dealing with collections of secondary vertices

#include <ROOT/RVec.hxx>

#include "FCCAnalyses/JetConstituentsUtils.h"
#include "FCCAnalyses/ReconstructedParticle.h"
#include "FCCAnalyses/ReconstructedParticle2Track.h"

#include "edm4hep/Track.h"
#include "edm4hep/TrackData.h"
#include "edm4hep/ReconstructedParticleData.h"

#include <iostream>
#include <algorithm>


namespace SecondaryVertexTools{

// helper function to associate a set of per-event secondary vertices to jets
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
}

// same as above but get indices instead
ROOT::VecOps::RVec<ROOT::VecOps::RVec<int>>
getSecondaryVertexJetIndices(
        const ROOT::VecOps::RVec<FCCAnalyses::VertexingUtils::FCCAnalysesVertex>& secondaryVertices,
        const ROOT::VecOps::RVec<fastjet::PseudoJet>& jets){

        // initialization
        ROOT::VecOps::RVec<ROOT::VecOps::RVec<int>> indicesPerJet;
        for(unsigned int i=0; i<jets.size(); i++){
            ROOT::VecOps::RVec<int> temp;
            indicesPerJet.push_back(temp);
        }

        // note: in very rare cases, there can be secondary vertices but no jets
        //       (even with exclusive jet clustering targeting 2 jets in every event);
        //       reason is not yet fully understood, but in any case, need safety against it.
        if( jets.size()==0 ){ return indicesPerJet; }

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
            TVector3 vertex_momentum = vertex_momenta.at(vertex_idx);
            for( unsigned int jet_idx=0; jet_idx < jets.size(); jet_idx++){
                TVector3 jet_momentum = jet_momenta.at(jet_idx);
                double dR = vertex_momentum.DeltaR(jet_momentum);
                if( dR < mindR ){
                    mindR = dR;
                    selected_jet_idx = jet_idx;
                }
            }
            indicesPerJet.at(selected_jet_idx).push_back(vertex_idx);
        }
        return indicesPerJet;
}

// helper function to associate a set of per-event secondary vertex values to jets
ROOT::VecOps::RVec<ROOT::VecOps::RVec<double>>
distributeOverJets(
        const ROOT::VecOps::RVec<double>& valuesPerEvent,
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<int>>& indicesPerJet){

        // initialization
        ROOT::VecOps::RVec<ROOT::VecOps::RVec<double>> valuesPerJet;
        
        // safety for no jets
        if( indicesPerJet.size()==0 ){ return valuesPerJet; }

        // loop over jets
        for(unsigned int jet_idx=0; jet_idx<indicesPerJet.size(); jet_idx++){
            ROOT::VecOps::RVec<int> valueIndices = indicesPerJet.at(jet_idx);
            ROOT::VecOps::RVec<double> temp;
            // loop over indices for this jet
            for(int value_idx : valueIndices){
                if( value_idx >= valuesPerEvent.size() ){ throw std::runtime_error("Index out of bounds."); }
                temp.push_back( valuesPerEvent.at(value_idx) );
            }
            valuesPerJet.push_back(temp);
        }
        return valuesPerJet;
}

}
