#include "FCCAnalyses/JetTaggingUtils.h"
#include <TFormula.h>
#include <TString.h>
#include <TRandom.h>
#include <stdexcept>
#include <iostream>
#include <cmath>


namespace FCCAnalyses {

namespace JetTaggingUtils {

// Helper: compile a TFormula from an expression that must depend on both pt and eta.
// The user-provided expression must contain the substrings "pt" and "eta".
// These are then replaced with "x" and "y" for TFormula evaluation.
TFormula* compilePtEtaFormula(const char* expression) {
  TString buffer(expression);

  // // Check that the formula depends on both "pt" and "eta".
  // if (!buffer.Contains("pt") || !buffer.Contains("eta")) {
  //   throw std::runtime_error("Error: Formula must depend on both pt and eta.");
  // }

  // Replace variable names with TFormula's internal variable names.
  buffer.ReplaceAll("pt", "x");   // x represents pt
  buffer.ReplaceAll("eta", "y");  // y represents eta

  // Create and compile the formula.
  TFormula* formula = new TFormula("formula", buffer.Data());
  if (formula->Compile() != 0) {
    delete formula;
    throw std::runtime_error("Error: Invalid formula: " + std::string(buffer.Data()));
  }
  return formula;
}




ROOT::VecOps::RVec<int>
get_flavour(ROOT::VecOps::RVec<fastjet::PseudoJet> in,
            ROOT::VecOps::RVec<edm4hep::MCParticleData> MCin) {
  ROOT::VecOps::RVec<int> result(in.size(), 0);

  int loopcount = 0;
  for (size_t i = 0; i < MCin.size(); ++i) {
    auto &parton = MCin[i];
    // Select partons only (for pythia8 71-79, for pythia6 2):
    if ((parton.generatorStatus > 80 || parton.generatorStatus < 70) &&
        parton.generatorStatus != 2)
      continue;
    if (std::abs(parton.PDG) > 5 && parton.PDG != 21)
      continue;
    ROOT::Math::PxPyPzMVector lv(parton.momentum.x, parton.momentum.y,
                                 parton.momentum.z, parton.mass);

    for (size_t j = 0; j < in.size(); ++j) {
      auto &p = in[j];
      // float dEta = lv.Eta() - p.eta();
      // float dPhi = lv.Phi() - p.phi();
      // float deltaR = sqrt(dEta*dEta+dPhi*dPhi);
      // if (deltaR <= 0.5 && gRandom->Uniform() <= efficiency) result[j] =
      // true;

      Float_t dot = p.px() * parton.momentum.x + p.py() * parton.momentum.y +
                    p.pz() * parton.momentum.z;
      Float_t lenSq1 = p.px() * p.px() + p.py() * p.py() + p.pz() * p.pz();
      Float_t lenSq2 = parton.momentum.x * parton.momentum.x +
                       parton.momentum.y * parton.momentum.y +
                       parton.momentum.z * parton.momentum.z;
      Float_t norm = sqrt(lenSq1 * lenSq2);
      Float_t angle = acos(dot / norm);

      if (angle <= 0.) {
        if (result[j] == 21 or result[j] == 0) {
          // if no match before, or matched to gluon, match to
          // this particle (favour quarks over gluons)
          result[j] = std::abs(parton.PDG);
        } else if (parton.PDG != 21) {
          // if matched to quark, and this is a quark, favour
          // heavier flavours
          result[j] = std::max(result[j], std::abs(parton.PDG));
        } else {
          // if matched to quark, and this is a gluon, keep
          // previous result (favour quark)
          ;
        }
      }
    }
  }

  return result;
}


ROOT::VecOps::RVec<int>
get_flavour(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in,
            ROOT::VecOps::RVec<edm4hep::MCParticleData> MCin, int maxPdg) {
  ROOT::VecOps::RVec<int> result(in.size(), 0);

  int loopcount = 0;
  for (size_t i = 0; i < MCin.size(); ++i) {
    auto &parton = MCin[i];

    // std::cout << "MC particle " << i << " with PDG " << parton.PDG << " status:  " << parton.generatorStatus << std::endl;
    // Select partons only (for pythia8 71-79, for pythia6 2):
    if ((parton.generatorStatus > 80 || parton.generatorStatus < 70) &&
        parton.generatorStatus != 2 && std::abs(parton.PDG) != 6)
      continue;
    if (std::abs(parton.PDG) > maxPdg && parton.PDG != 21)
      continue;
    ROOT::Math::PxPyPzMVector lv(parton.momentum.x, parton.momentum.y,
                                 parton.momentum.z, parton.mass);

    for (size_t j = 0; j < in.size(); ++j) {
      auto &p = in[j];
      // float dEta = lv.Eta() - p.eta();
      // float dPhi = lv.Phi() - p.phi();
      // float deltaR = sqrt(dEta*dEta+dPhi*dPhi);
      // if (deltaR <= 0.5 && gRandom->Uniform() <= efficiency) result[j] =
      // true;

      Float_t dot = p.momentum.x * parton.momentum.x + p.momentum.y * parton.momentum.y +
                    p.momentum.z * parton.momentum.z;
      Float_t lenSq1 = p.momentum.x * p.momentum.x + p.momentum.y * p.momentum.y + p.momentum.z * p.momentum.z;
      Float_t lenSq2 = parton.momentum.x * parton.momentum.x +
                       parton.momentum.y * parton.momentum.y +
                       parton.momentum.z * parton.momentum.z;
      Float_t norm = sqrt(lenSq1 * lenSq2);
      Float_t angle = acos(dot / norm);

      if (angle <= 0.4) {
        if (result[j] == 21 or result[j] == 0) {
          // if no match before, or matched to gluon, match to
          // this particle (favour quarks over gluons)
          result[j] = std::abs(parton.PDG);
        } else if (parton.PDG != 21) {
          // if matched to quark, and this is a quark, favour
          // heavier flavours
          result[j] = std::max(result[j], std::abs(parton.PDG));
        } else {
          // if matched to quark, and this is a gluon, keep
          // previous result (favour quark)
          ;
        }
      }
    }
  }

  return result;
}




ROOT::VecOps::RVec<int> get_btag(ROOT::VecOps::RVec<int> in, float efficiency,
                                 float mistag_c, float mistag_l,
                                 float mistag_g) {

  ROOT::VecOps::RVec<int> result(in.size(), 0);

  for (size_t j = 0; j < in.size(); ++j) {
    if (in.at(j) == 5 && gRandom->Uniform() <= efficiency)
      result[j] = 1;
    if (in.at(j) == 4 && gRandom->Uniform() <= mistag_c)
      result[j] = 1;
    if (in.at(j) < 4 && gRandom->Uniform() <= mistag_l)
      result[j] = 1;
    if (in.at(j) == 21 && gRandom->Uniform() <= mistag_g)
      result[j] = 1;
  }
  return result;
}

ROOT::VecOps::RVec<int> get_ctag(ROOT::VecOps::RVec<int> in, float efficiency,
                                 float mistag_b, float mistag_l,
                                 float mistag_g) {

  ROOT::VecOps::RVec<int> result(in.size(), 0);

  for (size_t j = 0; j < in.size(); ++j) {
    if (in.at(j) == 4 && gRandom->Uniform() <= efficiency)
      result[j] = 1;
    if (in.at(j) == 5 && gRandom->Uniform() <= mistag_b)
      result[j] = 1;
    if (in.at(j) < 4 && gRandom->Uniform() <= mistag_l)
      result[j] = 1;
    if (in.at(j) == 21 && gRandom->Uniform() <= mistag_g)
      result[j] = 1;
  }
  return result;
}

ROOT::VecOps::RVec<int> get_ltag(ROOT::VecOps::RVec<int> in, float efficiency,
                                 float mistag_b, float mistag_c,
                                 float mistag_g) {

  ROOT::VecOps::RVec<int> result(in.size(), 0);

  for (size_t j = 0; j < in.size(); ++j) {
    if (in.at(j) < 4 && gRandom->Uniform() <= efficiency)
      result[j] = 1;
    if (in.at(j) == 5 && gRandom->Uniform() <= mistag_b)
      result[j] = 1;
    if (in.at(j) == 4 && gRandom->Uniform() <= mistag_c)
      result[j] = 1;
    if (in.at(j) == 21 && gRandom->Uniform() <= mistag_g)
      result[j] = 1;
  }
  return result;
}

ROOT::VecOps::RVec<int> get_gtag(ROOT::VecOps::RVec<int> in, float efficiency,
                                 float mistag_b, float mistag_c,
                                 float mistag_l) {

  ROOT::VecOps::RVec<int> result(in.size(), 0);

  for (size_t j = 0; j < in.size(); ++j) {
    if (in.at(j) == 21 && gRandom->Uniform() <= efficiency)
      result[j] = 1;
    if (in.at(j) == 5 && gRandom->Uniform() <= mistag_b)
      result[j] = 1;
    if (in.at(j) == 4 && gRandom->Uniform() <= mistag_c)
      result[j] = 1;
    if (in.at(j) < 4 && gRandom->Uniform() <= mistag_l)
      result[j] = 1;
  }
  return result;
}


  // Generalized b-tagging function.
  // The additional string parameters are the expressions for:
  // b-jet efficiency, c-jet mistag rate, light-jet mistag rate, gluon-jet mistag rate.
  // Each formula must include both "pt" and "eta".
  ROOT::VecOps::RVec<int> get_btag(
       const ROOT::VecOps::RVec<int>& flavors,
       const ROOT::VecOps::RVec<float>& pts,
       const ROOT::VecOps::RVec<float>& etas,
       const std::string& b_formula_str,
       const std::string& c_formula_str,
       const std::string& l_formula_str,
       const std::string& g_formula_str) {

    // Compile the formulas from the input strings.
    TFormula* b_formula = compilePtEtaFormula(b_formula_str.c_str());
    TFormula* c_formula = compilePtEtaFormula(c_formula_str.c_str());
    TFormula* l_formula = compilePtEtaFormula(l_formula_str.c_str());
    TFormula* g_formula = compilePtEtaFormula(g_formula_str.c_str());

    // Check that the input vectors all have the same size.
    if (flavors.size() != pts.size() || flavors.size() != etas.size()) {
      throw std::runtime_error("Input vectors must have the same size.");
    }

    ROOT::VecOps::RVec<int> result(flavors.size(), 0);
    for (size_t j = 0; j < flavors.size(); ++j) {
      float pt = pts[j];
      float eta = etas[j];
      float rate = 0.0;
      int flavor = flavors[j];

      // std::cout << "pt: " << pt << " eta: " << eta << " flavor: " << flavor << std::endl;
      // std::cout << "b_formula: " << b_formula->Eval(pt, eta) << std::endl;
      // std::cout << "c_formula: " << c_formula->Eval(pt, eta) << std::endl;
      // std::cout << "l_formula: " << l_formula->Eval(pt, eta) << std::endl;
      // std::cout << "g_formula: " << g_formula->Eval(pt, eta) << std::endl;

      // Evaluate the appropriate formula based on jet flavor.
      if (flavor == 5) {
        rate = b_formula->Eval(pt, eta);
      } else if (flavor == 4) {
        rate = c_formula->Eval(pt, eta);
      } else if (flavor < 4) {
        rate = l_formula->Eval(pt, eta);
      } else if (flavor == 21) {
        rate = g_formula->Eval(pt, eta);
      }

      // Tag the jet if a random number is less than or equal to the rate.
      if (gRandom->Uniform() <= rate)
        result[j] = 1;
    }

    // Clean up the allocated TFormula objects.
    delete b_formula;
    delete c_formula;
    delete l_formula;
    delete g_formula;

    return result;
  }

  // Generalized top-tagging function.
  // The additional string parameters are the expressions for:
  // top-jet efficiency, qcd-jet mistag rate.
  ROOT::VecOps::RVec<int> get_toptag(
       const ROOT::VecOps::RVec<int>& flavors,
       const ROOT::VecOps::RVec<float>& pts,
       const ROOT::VecOps::RVec<float>& etas,
       const std::string& top_formula_str,
       const std::string& qcd_formula_str) {

    // Compile the formulas from the input strings.
    TFormula* top_formula = compilePtEtaFormula(top_formula_str.c_str());
    TFormula* qcd_formula = compilePtEtaFormula(qcd_formula_str.c_str());

    // Check that the input vectors all have the same size.
    if (flavors.size() != pts.size() || flavors.size() != etas.size()) {
      throw std::runtime_error("Input vectors must have the same size.");
    }

    ROOT::VecOps::RVec<int> result(flavors.size(), 0);
    for (size_t j = 0; j < flavors.size(); ++j) {
      float pt = pts[j];
      float eta = etas[j];
      float rate = 0.0;
      int flavor = flavors[j];

      // std::cout << "pt: " << pt << " eta: " << eta << " flavor: " << flavor << std::endl;
      // std::cout << "top_formula: " << top_formula->Eval(pt, eta) << std::endl;
      // std::cout << "qcd_formula: " << qcd_formula->Eval(pt, eta) << std::endl;

      // Evaluate the appropriate formula based on jet flavor.
      if (flavor == 6) {
        rate = top_formula->Eval(pt, eta);
      } else {
        rate = qcd_formula->Eval(pt, eta);
      }

      // Tag the jet if a random number is less than or equal to the rate.
      if (gRandom->Uniform() <= rate)
        result[j] = 1;
    }

    // Clean up the allocated TFormula objects.
    delete top_formula;
    delete qcd_formula;

    return result;
  }



sel_tag::sel_tag(bool arg_pass) : m_pass(arg_pass){};
ROOT::VecOps::RVec<fastjet::PseudoJet>
sel_tag::operator()(ROOT::VecOps::RVec<bool> tags,
                    ROOT::VecOps::RVec<fastjet::PseudoJet> in) {
  ROOT::VecOps::RVec<fastjet::PseudoJet> result;
  for (size_t i = 0; i < in.size(); ++i) {
    if (m_pass) {
      if (tags.at(i))
        result.push_back(in.at(i));
    } else {
      if (!tags.at(i))
        result.push_back(in.at(i));
    }
  }
  return result;
}


} // namespace JetTaggingUtils

} // namespace FCCAnalyses
