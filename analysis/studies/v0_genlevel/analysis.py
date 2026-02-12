import os
import sys
import json
import ROOT


# helper function for deriving the gen-level event type.
ROOT.gInterpreter.Declare("""
    int get_genEventType(
        const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles) {
        for (const auto& genParticle : genParticles) {
            int pdgid = std::abs(genParticle.PDG);
            if( (pdgid >= 1) && (pdgid <= 6) ){ return pdgid; }
        }
        return -1;
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

# helper function to get Ks particles
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<edm4hep::MCParticleData> get_Ks(
        const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles) {
        ROOT::VecOps::RVec<edm4hep::MCParticleData> result;
        for (const auto& genParticle : genParticles) {
            int pdgid = std::abs(genParticle.PDG);
            if( pdgid==310 ){ result.push_back(genParticle); }
        }
        return result;
    }""")

# helper function to get distance
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<float> get_dxyz(
        const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles,
        TLorentzVector PV,
        bool decay = false) {
        ROOT::VecOps::RVec<float> result;
        TVector3 pv(PV.X(), PV.Y(), PV.Z());
        for (const auto& genParticle : genParticles) {
            TVector3 vtx(genParticle.vertex.x, genParticle.vertex.y, genParticle.vertex.z);
            if( decay ) vtx = {genParticle.endpoint.x, genParticle.endpoint.y, genParticle.endpoint.z};
            result.push_back((vtx-pv).Mag());
        }
        return result;
    }""")

# helper function to get distance
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<float> get_dxy(
        const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles,
        TLorentzVector PV,
        bool decay = false) {
        ROOT::VecOps::RVec<float> result;
        TVector3 pv(PV.X(), PV.Y(), 0);
        for (const auto& genParticle : genParticles) {
            TVector3 vtx(genParticle.vertex.x, genParticle.vertex.y, 0);
            if( decay ) vtx = {genParticle.endpoint.x, genParticle.endpoint.y, 0};
            result.push_back((vtx-pv).Mag());
        }
        return result;
    }""")

# helper function to get pi+ pi- pair coming from Ks decay
# note: MC chain not available, so use other cuts instead
ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>> get_PiPiFromKs(
        const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles,
        const TLorentzVector& PV) {
        ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>> result;
        for (unsigned int idx1 = 0; idx1 < genParticles.size(); idx1++) {
            const edm4hep::MCParticleData genParticle1 = genParticles.at(idx1);
            if( std::abs(genParticle1.PDG)!=211 ) continue;
            for (unsigned int idx2 = idx1+1; idx2 < genParticles.size(); idx2++) {
                const edm4hep::MCParticleData genParticle2 = genParticles.at(idx2);
                if( std::abs(genParticle2.PDG)!=211 ) continue;
                
                // selection: opposite charge
                if( genParticle1.PDG * genParticle2.PDG > 0 ) continue;

                // find origin vertices
                TVector3 vtx1(genParticle1.vertex.x, genParticle1.vertex.y, genParticle1.vertex.z);
                TVector3 vtx2(genParticle2.vertex.x, genParticle2.vertex.y, genParticle2.vertex.z);

                // selection: same origin vertex
                if( (vtx1 - vtx2).Mag() > 1e-24 ) continue;

                // selection: displacement
                TVector3 PV3(PV.X(), PV.Y(), PV.Z());
                if( (vtx1 - PV3).Mag() < 0.5 ) continue;

                // selection: invariant mass
                ROOT::Math::PxPyPzMVector p1(genParticle1.momentum.x, genParticle1.momentum.y, genParticle1.momentum.z, genParticle1.mass);
                ROOT::Math::PxPyPzMVector p2(genParticle2.momentum.x, genParticle2.momentum.y, genParticle2.momentum.z, genParticle2.mass);
                if( std::abs((p1 + p2).mass() - 0.5) > 0.05 ) continue;

                ROOT::VecOps::RVec<edm4hep::MCParticleData> temp;
                temp.push_back(genParticle1);
                temp.push_back(genParticle2);
                result.push_back(temp);
            }
        }
        return result;
    }""")

ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<float> get_resonanceMass(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>>& resonances) {
        ROOT::VecOps::RVec<float> result;
        for (const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles : resonances) {
            ROOT::Math::PxPyPzMVector p4sum(0, 0, 0, 0);
            for (const edm4hep::MCParticleData gp : genParticles) {
                ROOT::Math::PxPyPzMVector p4(gp.momentum.x, gp.momentum.y, gp.momentum.z, gp.mass);
                p4sum += p4;
            }
            result.push_back(p4sum.mass());
        }
        return result;
    }""")

ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<float> get_resonanceMomentum(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>>& resonances) {
        ROOT::VecOps::RVec<float> result;
        for (const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles : resonances) {
            ROOT::Math::PxPyPzMVector p4sum(0, 0, 0, 0);
            for (const edm4hep::MCParticleData gp : genParticles) {
                ROOT::Math::PxPyPzMVector p4(gp.momentum.x, gp.momentum.y, gp.momentum.z, gp.mass);
                p4sum += p4;
            }
            result.push_back(p4sum.P());
        }
        return result;
    }""")

ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<float> get_resonanceDeltaR(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>>& resonances) {
        ROOT::VecOps::RVec<float> result;
        for (const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles : resonances) {
            const edm4hep::MCParticleData gp1 = genParticles.at(0);
            const edm4hep::MCParticleData gp2 = genParticles.at(1);
            ROOT::Math::PxPyPzMVector p1(gp1.momentum.x, gp1.momentum.y, gp1.momentum.z, gp1.mass);
            ROOT::Math::PxPyPzMVector p2(gp2.momentum.x, gp2.momentum.y, gp2.momentum.z, gp2.mass);
            result.push_back(ROOT::Math::VectorUtil::DeltaR(p1, p2));
        }
        return result;
    }""")

ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<float> get_resonanceAngle(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>>& resonances) {
        ROOT::VecOps::RVec<float> result;
        for (const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles : resonances) {
            const edm4hep::MCParticleData gp1 = genParticles.at(0);
            const edm4hep::MCParticleData gp2 = genParticles.at(1);
            ROOT::Math::PxPyPzMVector p1(gp1.momentum.x, gp1.momentum.y, gp1.momentum.z, gp1.mass);
            ROOT::Math::PxPyPzMVector p2(gp2.momentum.x, gp2.momentum.y, gp2.momentum.z, gp2.mass);
            double dtheta = p1.Theta() - p2.Theta();
            double dphi = ROOT::Math::VectorUtil::DeltaPhi(p1, p2);
            double angle = std::sqrt(dtheta*dtheta + dphi*dphi);
            result.push_back(angle);
        }
        return result;
    }""")

ROOT.gInterpreter.Declare("""
    ROOT::VecOps::RVec<float> get_resonanceConstituentP(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>>& resonances,
        unsigned int index) {
        ROOT::VecOps::RVec<float> result;
        for (const ROOT::VecOps::RVec<edm4hep::MCParticleData>& genParticles : resonances) {
            const edm4hep::MCParticleData gp = genParticles.at(index);
            ROOT::Math::PxPyPzMVector p4(gp.momentum.x, gp.momentum.y, gp.momentum.z, gp.mass);
            result.push_back(p4.P());
        }
        return result;
    }

    ROOT::VecOps::RVec<float> get_resonanceConstituentP1(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>>& resonances) {
        return get_resonanceConstituentP(resonances, 0);
    }

    ROOT::VecOps::RVec<float> get_resonanceConstituentP2(
        const ROOT::VecOps::RVec<ROOT::VecOps::RVec<edm4hep::MCParticleData>>& resonances) {
        return get_resonanceConstituentP(resonances, 1);
    }""")



# main analyzer class
class RDFanalysis():

    def analysers(df):

        # initialization
        dfout = df

        # translations
        dfout = dfout.Alias("Particle", "MCParticles")
        dfout = dfout.Alias("ReconstructedParticles", "RecoParticles")
        dfout = dfout.Alias("ParticleIDs", "ParticleID")

        # generic gen-level stuff
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

        # find K-shorts
        dfout = (
            dfout
            .Define("Ks", "get_Ks(Particle)")
            .Define("nKs", "Ks.size()")
            .Define("Ks_pt", "FCCAnalyses::MCParticle::get_pt(Ks)")
            .Define("Ks_production_dxyz", "get_dxyz(Ks, GenPrimaryVertexP4, false)")
            .Define("Ks_production_dxy", "get_dxy(Ks, GenPrimaryVertexP4, false)")
            .Define("Ks_decay_dxyz", "get_dxyz(Ks, GenPrimaryVertexP4, true)")
            .Define("Ks_decay_dxy", "get_dxy(Ks, GenPrimaryVertexP4, true)")
        )

        # find pi-pi resonances
        dfout = (
            dfout
            .Define("PiPiResonances", "get_PiPiFromKs(Particle, GenPrimaryVertexP4)")
            .Define("nPiPi", "PiPiResonances.size()")
            .Define("PiPi_mass", "get_resonanceMass(PiPiResonances)")
            .Define("PiPi_p", "get_resonanceMomentum(PiPiResonances)")
            .Define("PiPi_deltaR", "get_resonanceDeltaR(PiPiResonances)")
            .Define("PiPi_angle", "get_resonanceAngle(PiPiResonances)")
            .Define("PiPi_p1", "get_resonanceConstituentP1(PiPiResonances)")
            .Define("PiPi_p2", "get_resonanceConstituentP2(PiPiResonances)")
        )

        return dfout

    def output():

        # define output branches
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

        # Ks variables
        branchList += [
            'nKs',
            'Ks_pt',
            'Ks_production_dxyz',
            'Ks_production_dxy',
            'Ks_decay_dxyz',
            'Ks_decay_dxy'
        ]

        # pi-pi variables
        branchList += [
            'nPiPi',
            'PiPi_mass',
            'PiPi_p',
            'PiPi_deltaR',
            'PiPi_angle',
            'PiPi_p1',
            'PiPi_p2'
        ]

        return branchList
