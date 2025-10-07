// standard library header files
#include <vector>
#include <iostream>
#include <fstream>
#include <iomanip>

// ROOT header files
#include "TH1F.h"
#include "TCanvas.h"
#include "TFile.h"
#include "TTree.h"
#include "TString.h"
#include "TStyle.h"
#include <Rtypes.h>
#include "ROOT/RVec.hxx"


int main(int argc, char* argv[]) {
  std::cout << "Starting makentuples.cpp..." << std::endl;

  // check command line args
  // note: use the following command line args:
  //       - path to input file
  //       - path to output file
  //       - start entry
  //       - stop entry
  // note: start entry and stop entry can also be fractional numbers
  //       instead of integer numbers, in which case the provided fractions
  //       of the total number of events in the input file are used.
  if( argc!= 5 ) {
    std::cerr << "USAGE: ./makentuples [input root file] [output root file]";
    std::cerr << " [start entry] [stop entry]" << std::endl;
    exit(1);
  }

  // set input file from command-line args
  std::string infileName(argv[1]);

  // open the input file
  TFile* infile = TFile::Open(infileName.c_str());
  if( !infile->IsOpen() ){
    std::cerr << "Problems opening root file. Exiting." << std::endl;
    exit(-1);
  }
  std::cout << "Opened file " << infileName.c_str()  << std::endl;

  // get the tree          
  TTree* ev = (TTree*)infile->Get("events");
  if(!ev) {
    std::cerr << "null pointer for TTree! Exiting." << std::endl;
    exit(-2);
  }
  std::cout << "Opened tree " << "events" << std::endl;
  
  // declare variables to be read from the tree

  // event properties
  int genEventType;
  int nJets;

  // jet properties
  ROOT::VecOps::RVec<float> *Jets_e=0;
  ROOT::VecOps::RVec<float> *Jets_mass=0;
  ROOT::VecOps::RVec<float> *Jets_pt = 0;
  ROOT::VecOps::RVec<float> *Jets_phi = 0;
  ROOT::VecOps::RVec<float> *Jets_eta = 0;
  ROOT::VecOps::RVec<float> *Jets_theta = 0;
  ROOT::VecOps::RVec<int>* count_Const = 0;
  ROOT::VecOps::RVec<int>* count_Mu = 0;
  ROOT::VecOps::RVec<int>* count_El = 0;
  ROOT::VecOps::RVec<int>* count_ChargedHad = 0;
  ROOT::VecOps::RVec<int>* count_Photon = 0;
  ROOT::VecOps::RVec<int>* count_NeutralHad = 0;
 
  // jet constituent properties
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_e = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_pt = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_px = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_py = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_pz = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_theta = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_phi = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_charge = 0;
  
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_erel = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_erel_log = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_ptrel = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_ptrel_log = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_thetarel = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_phirel = 0;
  
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_dndx = 0;
  //ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_mtof = 0;

  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_dxy = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_dz = 0;

  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_omega_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_d0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_z0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_phi0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_tanlambda_cov = 0;
  
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_d0_z0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_phi0_d0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_phi0_z0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_tanlambda_phi0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_tanlambda_d0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_tanlambda_z0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_omega_tanlambda_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_omega_phi0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_omega_d0_cov = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_omega_z0_cov = 0;
  
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_Sip2dVal = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_Sip2dSig = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_Sip3dVal = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_Sip3dSig = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_JetDistVal = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_JetDistSig = 0;

  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_isMu = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_isEl = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_isChargedHad = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_isGamma = 0;
  ROOT::VecOps::RVec<ROOT::VecOps::RVec<float> > *JetsConstituents_isNeutralHad = 0;

  // map variables to branches in the input tree 
  
  // event properties
  ev->SetBranchAddress("genEventType", &genEventType);
  ev->SetBranchAddress("njet", &nJets);

  // jet properties
  ev->SetBranchAddress("Jets_e", &Jets_e);
  ev->SetBranchAddress("Jets_mass", &Jets_mass);
  ev->SetBranchAddress("Jets_pt", &Jets_pt);
  ev->SetBranchAddress("Jets_phi", &Jets_phi);
  ev->SetBranchAddress("Jets_eta", &Jets_eta);
  ev->SetBranchAddress("Jets_theta", &Jets_theta);
  ev->SetBranchAddress("nconst", &count_Const);
  ev->SetBranchAddress("nmu", &count_Mu);
  ev->SetBranchAddress("nel", &count_El);
  ev->SetBranchAddress("nchargedhad", &count_ChargedHad);
  ev->SetBranchAddress("nphoton", &count_Photon);
  ev->SetBranchAddress("nneutralhad", &count_NeutralHad);

  // jet constituent properties
  ev->SetBranchAddress("JetsConstituents_e", &JetsConstituents_e);
  ev->SetBranchAddress("JetsConstituents_pt", &JetsConstituents_pt);
  ev->SetBranchAddress("JetsConstituents_px", &JetsConstituents_px);
  ev->SetBranchAddress("JetsConstituents_py", &JetsConstituents_py);
  ev->SetBranchAddress("JetsConstituents_pz", &JetsConstituents_pz);
  ev->SetBranchAddress("JetsConstituents_theta", &JetsConstituents_theta);
  ev->SetBranchAddress("JetsConstituents_phi", &JetsConstituents_phi);
  ev->SetBranchAddress("JetsConstituents_charge", &JetsConstituents_charge);
  
  ev->SetBranchAddress("JetsConstituents_erel", &JetsConstituents_erel);
  ev->SetBranchAddress("JetsConstituents_erel_log", &JetsConstituents_erel_log);
  ev->SetBranchAddress("JetsConstituents_ptrel", &JetsConstituents_ptrel);
  ev->SetBranchAddress("JetsConstituents_ptrel_log", &JetsConstituents_ptrel_log);
  ev->SetBranchAddress("JetsConstituents_thetarel", &JetsConstituents_thetarel);
  ev->SetBranchAddress("JetsConstituents_phirel", &JetsConstituents_phirel);

  ev->SetBranchAddress("JetsConstituents_dndx", &JetsConstituents_dndx);
  //ev->SetBranchAddress("JetsConstituents_mtof", &JetsConstituents_mtof);

  ev->SetBranchAddress("JetsConstituents_dxy", &JetsConstituents_dxy);
  ev->SetBranchAddress("JetsConstituents_dz", &JetsConstituents_dz);

  ev->SetBranchAddress("JetsConstituents_omega_cov", &JetsConstituents_omega_cov);
  ev->SetBranchAddress("JetsConstituents_d0_cov", &JetsConstituents_d0_cov);
  ev->SetBranchAddress("JetsConstituents_z0_cov", &JetsConstituents_z0_cov);
  ev->SetBranchAddress("JetsConstituents_phi0_cov", &JetsConstituents_phi0_cov);
  ev->SetBranchAddress("JetsConstituents_tanlambda_cov", &JetsConstituents_tanlambda_cov);
  
  ev->SetBranchAddress("JetsConstituents_d0_z0_cov", &JetsConstituents_d0_z0_cov);
  ev->SetBranchAddress("JetsConstituents_phi0_d0_cov", &JetsConstituents_phi0_d0_cov);
  ev->SetBranchAddress("JetsConstituents_phi0_z0_cov", &JetsConstituents_phi0_z0_cov);
  ev->SetBranchAddress("JetsConstituents_tanlambda_phi0_cov", &JetsConstituents_tanlambda_phi0_cov);
  ev->SetBranchAddress("JetsConstituents_tanlambda_d0_cov", &JetsConstituents_tanlambda_d0_cov);
  ev->SetBranchAddress("JetsConstituents_tanlambda_z0_cov", &JetsConstituents_tanlambda_z0_cov);
  ev->SetBranchAddress("JetsConstituents_omega_phi0_cov", &JetsConstituents_omega_phi0_cov);
  ev->SetBranchAddress("JetsConstituents_omega_d0_cov", &JetsConstituents_omega_d0_cov);
  ev->SetBranchAddress("JetsConstituents_omega_z0_cov", &JetsConstituents_omega_z0_cov);
  ev->SetBranchAddress("JetsConstituents_omega_tanlambda_cov", &JetsConstituents_omega_tanlambda_cov);
  
  ev->SetBranchAddress("JetsConstituents_Sip2dVal", &JetsConstituents_Sip2dVal);
  ev->SetBranchAddress("JetsConstituents_Sip2dSig", &JetsConstituents_Sip2dSig);
  ev->SetBranchAddress("JetsConstituents_Sip3dVal", &JetsConstituents_Sip3dVal);
  ev->SetBranchAddress("JetsConstituents_Sip3dSig", &JetsConstituents_Sip3dSig);
  ev->SetBranchAddress("JetsConstituents_JetDistVal", &JetsConstituents_JetDistVal);
  ev->SetBranchAddress("JetsConstituents_JetDistSig", &JetsConstituents_JetDistSig);
  
  ev->SetBranchAddress("JetsConstituents_isMu", &JetsConstituents_isMu);
  ev->SetBranchAddress("JetsConstituents_isEl", &JetsConstituents_isEl);
  ev->SetBranchAddress("JetsConstituents_isChargedHad", &JetsConstituents_isChargedHad);
  ev->SetBranchAddress("JetsConstituents_isGamma", &JetsConstituents_isGamma);
  ev->SetBranchAddress("JetsConstituents_isNeutralHad", &JetsConstituents_isNeutralHad);

  // make output file and output tree
  std::string outfileName(argv[2]);
  TFile* outfile = new TFile(outfileName.c_str(), "recreate");
  std::cout << "Opened outfile " << std::endl;
  TTree* ntuple = new TTree("tree", "jets_Ntuple");
  std::cout << "Opened ntuple " << std::endl;
 
  // define variables to write
  
  // jet variables
  double recojet_e, recojet_mass, recojet_pt, recojet_phi, recojet_eta, recojet_theta;
  float flavour = -1;
  float is_q = 0.;
  float is_t = 0.;
  float is_b = 0.;
  float is_c = 0.;
  float is_s = 0.;
  float is_u = 0.;
  float is_d = 0.;
  float is_g = 0.;
  float is_udsg = 0.;
  int nconst = 0;
  int nphotons = 0;
  int ncharged = 0;
  int nchargedhad = 0;
  int nneutralhad = 0;
  int nel = 0;
  int nmu = 0;

  // jet constituent variables
  float pfcand_e[1000] = {0.};
  float pfcand_pt[1000] = {0.};
  float pfcand_px[1000] = {0.};
  float pfcand_py[1000] = {0.};
  float pfcand_pz[1000] = {0.};
  float pfcand_charge[1000] = {0.};
  float pfcand_theta[1000] = {0.};
  float pfcand_phi[1000] = {0.};
  
  float pfcand_erel[1000] = {0.};
  float pfcand_erel_log[1000] = {0.};
  float pfcand_ptrel[1000] = {0.};
  float pfcand_ptrel_log[1000] = {0.};
  float pfcand_thetarel[1000] = {0.};
  float pfcand_phirel[1000] = {0.};

  float pfcand_dndx[1000] = {0.};
  //float pfcand_mtof[1000] = {0.};
  
  float pfcand_dxy[1000] = {0.};
  float pfcand_dz[1000] = {0.};
  
  float pfcand_dptdpt[1000] = {0.};
  float pfcand_dxydxy[1000] = {0.};
  float pfcand_dzdz[1000] = {0.};
  float pfcand_dphidphi[1000] = {0.};
  float pfcand_detadeta[1000] = {0.};

  float pfcand_dxydz[1000] = {0.};
  float pfcand_dphidxy[1000] = {0.};
  float pfcand_phidz[1000] = {0.};
  float pfcand_phictgtheta[1000] = {0.};
  float pfcand_dxyctgtheta[1000] = {0.};
  float pfcand_dlambdadz[1000] = {0.};
  float pfcand_cctgtheta[1000] = {0.};
  float pfcand_phic[1000] = {0.};
  float pfcand_dxyc[1000] = {0.};
  float pfcand_cdz[1000] = {0.};

  float pfcand_btagSip2dVal[1000] = {0.};
  float pfcand_btagSip2dSig[1000] = {0.};
  float pfcand_btagSip3dVal[1000] = {0.};
  float pfcand_btagSip3dSig[1000] = {0.};
  float pfcand_btagJetDistVal[1000] = {0.};
  float pfcand_btagJetDistSig[1000] = {0.};

  float pfcand_isMu[1000] = {0.};
  float pfcand_isEl[1000] ={0.};
  float pfcand_isChargedHad[1000] ={0.};
  float pfcand_isGamma[1000] ={0.};
  float pfcand_isNeutralHad[1000] ={0.};

  // counting
  int njet = 0;
  int anomaly_njets_counts_less = 0;
  int anomaly_njets_counts_more = 0;
  int anomaly_njets_counts = 0;
  int saved_events_counts = 0;                                                                                             

  // define output branches

  // jet variables 
  ntuple->Branch("recojet_e", &recojet_e);
  ntuple->Branch("recojet_mass", &recojet_mass);
  ntuple->Branch("recojet_pt", &recojet_pt);
  ntuple->Branch("recojet_phi", &recojet_phi);
  ntuple->Branch("recojet_eta", &recojet_eta);
  ntuple->Branch("recojet_theta", &recojet_theta);
 
  ntuple->Branch("flavour", &flavour);
  ntuple->Branch("recojet_isQ", &is_q);
  ntuple->Branch("recojet_isT", &is_t);
  ntuple->Branch("recojet_isB", &is_b);
  ntuple->Branch("recojet_isC", &is_c);
  ntuple->Branch("recojet_isS", &is_s);
  ntuple->Branch("recojet_isU", &is_u);
  ntuple->Branch("recojet_isD", &is_d);
  ntuple->Branch("recojet_isG", &is_g);
  ntuple->Branch("recojet_isUDSG", &is_udsg);
  
  ntuple->Branch("nconst", &nconst, "nconst/I");
  ntuple->Branch("nphotons", &nphotons, "nphotons/I");
  ntuple->Branch("ncharged", &ncharged, "ncharged/I");
  ntuple->Branch("nneutralhad", &nneutralhad, "nneutralhad/I");
  ntuple->Branch("nchargedhad", &nchargedhad, "nchargedhad/I");
  ntuple->Branch("nel", &nel, "nel/I");
  ntuple->Branch("nmu", &nmu, "nmu/I");

  // jet constituent variables
  ntuple->Branch("pfcand_e", pfcand_e, "pfcand_e[nconst]/F");
  ntuple->Branch("pfcand_pt", pfcand_pt, "pfcand_pt[nconst]/F");
  ntuple->Branch("pfcand_px", pfcand_px, "pfcand_px[nconst]/F");
  ntuple->Branch("pfcand_py", pfcand_py, "pfcand_py[nconst]/F");
  ntuple->Branch("pfcand_pz", pfcand_pz, "pfcand_pz[nconst]/F");
  ntuple->Branch("pfcand_charge", pfcand_charge, "pfcand_charge[nconst]/F");
  ntuple->Branch("pfcand_theta", pfcand_theta, "pfcand_theta[nconst]/F");
  ntuple->Branch("pfcand_phi", pfcand_phi, "pfcand_phi[nconst]/F");
  
  ntuple->Branch("pfcand_erel", pfcand_erel, "pfcand_erel[nconst]/F");
  ntuple->Branch("pfcand_erel_log", pfcand_erel_log, "pfcand_erel_log[nconst]/F");
  ntuple->Branch("pfcand_ptrel", pfcand_ptrel, "pfcand_ptrel[nconst]/F");
  ntuple->Branch("pfcand_ptrel_log", pfcand_ptrel_log, "pfcand_ptrel_log[nconst]/F");
  ntuple->Branch("pfcand_thetarel", pfcand_thetarel, "pfcand_thetarel[nconst]/F");
  ntuple->Branch("pfcand_phirel", pfcand_phirel, "pfcand_phirel[nconst]/F");
  
  ntuple->Branch("pfcand_dndx", pfcand_dndx, "pfcand_dndx[nconst]/F");
  //ntuple->Branch("pfcand_mtof", pfcand_mtof, "pfcand_mtof[nconst]/F");

  ntuple->Branch("pfcand_dxy", pfcand_dxy, "pfcand_dxy[nconst]/F");
  ntuple->Branch("pfcand_dz", pfcand_dz, "pfcand_dz[nconst]/F");

  ntuple->Branch("pfcand_dptdpt", pfcand_dptdpt, "pfcand_dptdpt[nconst]/F");
  ntuple->Branch("pfcand_dxydxy", pfcand_dxydxy, "pfcand_dxydxy[nconst]/F");
  ntuple->Branch("pfcand_dzdz", pfcand_dzdz, "pfcand_dzdz[nconst]/F");
  ntuple->Branch("pfcand_dphidphi", pfcand_dphidphi, "pfcand_dphidphi[nconst]/F");
  ntuple->Branch("pfcand_detadeta", pfcand_detadeta, "pfcand_detadeta[nconst]/F");
  
  ntuple->Branch("pfcand_dxydz", pfcand_dxydz, "pfcand_dxydz[nconst]/F");
  ntuple->Branch("pfcand_dphidxy", pfcand_dphidxy, "pfcand_dphidxy[nconst]/F");
  ntuple->Branch("pfcand_phidz", pfcand_phidz, "pfcand_phidz[nconst]/F");
  ntuple->Branch("pfcand_phictgtheta", pfcand_phictgtheta, "pfcand_phictgtheta[nconst]/F");
  ntuple->Branch("pfcand_dxyctgtheta", pfcand_dxyctgtheta, "pfcand_dxyctgtheta[nconst]/F");
  ntuple->Branch("pfcand_dlambdadz", pfcand_dlambdadz, "pfcand_dlambdadz[nconst]/F");
  ntuple->Branch("pfcand_cctgtheta", pfcand_cctgtheta, "pfcand_cctgtheta[nconst]/F");
  ntuple->Branch("pfcand_phic", pfcand_phic, "pfcand_phic[nconst]/F");
  ntuple->Branch("pfcand_dxyc", pfcand_dxyc, "pfcand_dxyc[nconst]/F");
  ntuple->Branch("pfcand_cdz", pfcand_cdz, "pfcand_cdz[nconst]/F");

  ntuple->Branch("pfcand_btagSip2dVal", pfcand_btagSip2dVal, "pfcand_btagSip2dVal[nconst]/F");
  ntuple->Branch("pfcand_btagSip2dSig", pfcand_btagSip2dSig, "pfcand_btagSip2dSig[nconst]/F");
  ntuple->Branch("pfcand_btagSip3dVal", pfcand_btagSip3dVal, "pfcand_btagSip3dVal[nconst]/F");
  ntuple->Branch("pfcand_btagSip3dSig", pfcand_btagSip3dSig, "pfcand_btagSip3dSig[nconst]/F");
  ntuple->Branch("pfcand_btagJetDistVal", pfcand_btagJetDistVal, "pfcand_btagJetDistVal[nconst]/F");
  ntuple->Branch("pfcand_btagJetDistSig", pfcand_btagJetDistSig, "pfcand_btagJetDistSig[nconst]/F");

  ntuple->Branch("pfcand_isMu", pfcand_isMu, "pfcand_isMu[nconst]/F");
  ntuple->Branch("pfcand_isEl", pfcand_isEl, "pfcand_isEl[nconst]/F");
  ntuple->Branch("pfcand_isChargedHad", pfcand_isChargedHad, "pfcand_isChargedHad[nconst]/F");
  ntuple->Branch("pfcand_isGamma", pfcand_isGamma, "pfcand_isGamma[nconst]/F");
  ntuple->Branch("pfcand_isNeutralHad", pfcand_isNeutralHad, "pfcand_isNeutralHad[nconst]/F");

  // read the start entry and stop entry
  // (and convert fractions to absolute numbers if needed)
  float f_i = atof(argv[3]);
  float f_f = atof(argv[4]);
  int nentries = ev->GetEntries();
  int N_i = 0;
  int N_f = 0;
  if( f_i > 1. ){ N_i = (int) f_i; }
  else{ N_i = (int) (f_i*nentries); }
  if( f_f > 1.){ N_f = (int) f_f; }
  else{ N_f = (int) (f_f*nentries); }
  int Nevents_Max = N_f - N_i;
  std::cout << "Number of events in input tree: " << nentries << std::endl;
  std::cout << "Will run over event " << N_i << " to " << N_f << std::endl;

  // run over each entry in the tree
  for(int i = N_i; i < nentries; ++i) {
    
    // get the event
    ev->GetEntry(i);

    // derive event level properties
    njet = nJets;
    int eventFlavour = genEventType;

    // do some printouts to track progress
    if(i % 10000 == 0) {
      std::cout<< "-----" << std::endl;
      std::cout << "-> event: " << i << " -  " << "#jets: " << njet << " -  (*Jets_e).size(): " << (*Jets_e).size() << std::endl;
      std::cout << "-----" << std::endl;
    }

    // count anomalous cases where number of jets is different from 2
    if(njet != 2) {
      anomaly_njets_counts += 1;
      if (njet > 2) { anomaly_njets_counts_more += 1; }
      else { anomaly_njets_counts_less += 1; }
    }
    
    // skip events with less than 2 jets
    if (njet < 2) {
      continue ;
    }

    // run over the jets in the event
    // note: we only take the first two jets (the ones having more energy, they're ordered in stage1);
    //       any more jets are because of inefficiencies in the clustering.
    for(int j=0; j < 2; ++j) {

      // get jet type (from event type)
      flavour = (float)eventFlavour;
      is_q = (eventFlavour!=0);
      is_t = (eventFlavour==6);
      is_b = (eventFlavour==5);
      is_c = (eventFlavour==4);
      is_s = (eventFlavour==3);
      is_u = (eventFlavour==2);
      is_d = (eventFlavour==1);
      is_g = (eventFlavour==0);
      is_udsg = (eventFlavour>=0 && eventFlavour<=3);

      // get properties
      recojet_e = (*Jets_e)[j];
      recojet_mass = (*Jets_mass)[j];
      recojet_pt = (*Jets_pt)[j];
      recojet_phi = (*Jets_phi)[j];
      recojet_eta = (*Jets_eta)[j];
      recojet_theta = (*Jets_theta)[j];
      nconst = (count_Const->at(j));
      nel = (count_El->at(j));
      nmu = (count_Mu->at(j));
      nchargedhad = (count_ChargedHad->at(j));
      nphotons = (count_Photon->at(j));
      nneutralhad = (count_NeutralHad->at(j));
      
      // do some printouts
      /*if(i % 10000 == 0) {
          std::cout << "-> jet: " << j << " -  " << "nconst: " << nconst << "-> (JetsConstituents_e->at(j)).size(): " << (JetsConstituents_e->at(j)).size() << std::endl;
          std::cout << "-> jet_e: " << recojet_e << " -  jet_pt: " << recojet_pt << std::endl;
          std::cout<< "-----" << std::endl;
      }*/

      // loop over constituents
      for(int k = 0; k < nconst; ++k){
        pfcand_e[k] = (JetsConstituents_e->at(j))[k];
        pfcand_pt[k] = (JetsConstituents_pt->at(j))[k];
        pfcand_px[k] = (JetsConstituents_px->at(j))[k];
        pfcand_py[k] = (JetsConstituents_py->at(j))[k];
        pfcand_pz[k] = (JetsConstituents_pz->at(j))[k];
        pfcand_theta[k] = (JetsConstituents_theta->at(j))[k];
        pfcand_phi[k] = (JetsConstituents_phi->at(j))[k];
        pfcand_charge[k] = (JetsConstituents_charge->at(j))[k];
        
        pfcand_erel[k] = (JetsConstituents_erel->at(j))[k];
        pfcand_erel_log[k] = (JetsConstituents_erel_log->at(j))[k];
        pfcand_ptrel[k] = (JetsConstituents_ptrel->at(j))[k];
        pfcand_ptrel_log[k] = (JetsConstituents_ptrel_log->at(j))[k];
        pfcand_thetarel[k] = (JetsConstituents_thetarel->at(j))[k];
        pfcand_phirel[k] = (JetsConstituents_phirel->at(j))[k];
        
        pfcand_dndx[k] = (JetsConstituents_dndx->at(j))[k]/1000.; //transformed in mm
        //pfcand_mtof[k] = (JetsConstituents_mtof->at(j))[k];

        pfcand_dxy[k] = (JetsConstituents_dxy->at(j))[k];
        pfcand_dz[k] = (JetsConstituents_dz->at(j))[k];
       
        pfcand_dptdpt[k] = (JetsConstituents_omega_cov->at(j))[k];
        pfcand_dxydxy[k] = (JetsConstituents_d0_cov->at(j))[k];
        pfcand_dzdz[k] = (JetsConstituents_z0_cov->at(j))[k];
        pfcand_dphidphi[k] = (JetsConstituents_phi0_cov->at(j))[k];
        pfcand_detadeta[k] = (JetsConstituents_tanlambda_cov->at(j))[k];
    
        pfcand_dxydz[k] = (JetsConstituents_d0_z0_cov->at(j))[k];
        pfcand_dphidxy[k] = (JetsConstituents_phi0_d0_cov->at(j))[k];
        pfcand_phidz[k] = (JetsConstituents_phi0_z0_cov->at(j))[k];
        
        pfcand_phictgtheta[k] = (JetsConstituents_tanlambda_phi0_cov->at(j))[k];
        pfcand_dxyctgtheta[k] = (JetsConstituents_tanlambda_d0_cov->at(j))[k];
        pfcand_dlambdadz[k] = (JetsConstituents_tanlambda_z0_cov->at(j))[k];
        
        pfcand_cctgtheta[k] = (JetsConstituents_omega_tanlambda_cov->at(j))[k];
        pfcand_phic[k] = (JetsConstituents_omega_phi0_cov->at(j))[k];
        pfcand_dxyc[k] = (JetsConstituents_omega_d0_cov->at(j))[k];
        pfcand_cdz[k] = (JetsConstituents_omega_z0_cov->at(j))[k];
        
        pfcand_btagSip2dVal[k] = (JetsConstituents_Sip2dVal->at(j))[k];
        pfcand_btagSip2dSig[k] = (JetsConstituents_Sip2dSig->at(j))[k];
        pfcand_btagSip3dVal[k] = (JetsConstituents_Sip3dVal->at(j))[k];
        pfcand_btagSip3dSig[k] = (JetsConstituents_Sip3dSig->at(j))[k];
        pfcand_btagJetDistVal[k] = (JetsConstituents_JetDistVal->at(j))[k];
        pfcand_btagJetDistSig[k] = (JetsConstituents_JetDistSig->at(j))[k];

        pfcand_isMu[k] = (JetsConstituents_isMu->at(j))[k];
        pfcand_isEl[k] = (JetsConstituents_isEl->at(j))[k];
        pfcand_isChargedHad[k] = (JetsConstituents_isChargedHad->at(j))[k];
        pfcand_isGamma[k] = (JetsConstituents_isGamma->at(j))[k];
        pfcand_isNeutralHad[k] = (JetsConstituents_isNeutralHad->at(j))[k];
      }  // end of loop over constituents per jet

      // fill ntuple (per jet, not per event!) 
      ntuple->Fill();
    
    } // end of loop over jets per event

    // we count the number of events saved
    saved_events_counts += 1;

    // interrupt the loop if the maximum number of events has been reached
    if (saved_events_counts >= Nevents_Max) { break; }
  
  } // end of loop over events

  // do some printouts
  std::cout << "-> number of entries run: " << nentries <<std::endl;
  std::cout << "-> number of entries considered: " << saved_events_counts <<std::endl;
  std::cout<< " " << std::endl;
  std::cout << "--> number of events with njets != 2: " << anomaly_njets_counts  << std::endl; 
  std::cout << "--> number of events with njets > 2: " <<  anomaly_njets_counts_more << std::endl;
  std::cout << "--> number of events with njets < 2: " <<  anomaly_njets_counts_less << std::endl;
  

  // write output file
  ntuple->Write();
  infile->Close();
  outfile->Close();
  std::cout << "Closed files "<<std::endl;
  std::cout << "Done." << std::endl;
  
  return 0;
}
