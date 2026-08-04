#include "FCCAnalyses/VertexFitterSimple.h"
#include "FCCAnalyses/MCParticle.h"

#include "edm4hep/EDM4hepVersion.h"

#include <iostream>

#include "TFile.h"
#include "TString.h"

#include <fcntl.h>

//#include "TrkUtil.h"    // from delphes

// -----------------------------------------------------------------------
// VertexFitFast: single-stage vertex fitter (no track parameter steering).
// Copied verbatim from aleph-ntuplizer/analyzers/VertexFitFast.{h,cc}
// for temporary testing — remove once validation is complete.
// -----------------------------------------------------------------------
class VertexFitFast : public TrkUtil {
 private:
  Int_t fNtr;
  std::vector<TVectorD*> fPar, fParNew;
  std::vector<TMatrixDSym*> fCov, fCovNew;
  std::vector<Bool_t> fCharged;
  Bool_t fVtxCst;
  TVectorD fxCst;
  TMatrixDSym fCovCst, fCovCstInv;
  Bool_t fVtxDone;
  Double_t fRstart;
  TVectorD fXv;
  TMatrixDSym fcovXv;
  Double_t fChi2;
  TVectorD fChi2List;
  std::vector<Double_t> ffi;
  std::vector<TVectorD*> fx0i, fai, fdi;
  std::vector<Double_t> fa2i;
  std::vector<TMatrixD*> fAti;
  std::vector<TMatrixDSym*> fDi, fWi, fWinvi;
  void ResetWrkArrays() {
    Int_t N = (Int_t)fdi.size();
    if (N > 0) {
      for (Int_t i = 0; i < N; i++) {
        if (fx0i[i])   { fx0i[i]->Clear();   delete fx0i[i]; }
        if (fai[i])    { fai[i]->Clear();    delete fai[i]; }
        if (fdi[i])    { fdi[i]->Clear();    delete fdi[i]; }
        if (fAti[i])   { fAti[i]->Clear();   delete fAti[i]; }
        if (fDi[i])    { fDi[i]->Clear();    delete fDi[i]; }
        if (fWi[i])    { fWi[i]->Clear();    delete fWi[i]; }
        if (fWinvi[i]) { fWinvi[i]->Clear(); delete fWinvi[i]; }
      }
      fa2i.clear(); fx0i.clear(); fai.clear(); fdi.clear();
      fAti.clear(); fDi.clear(); fWi.clear(); fWinvi.clear();
    }
  }
  TVectorD Fill_x(TVectorD par, Double_t phi, Bool_t Q) {
    TVectorD x(3);
    TVector3 xt = Q ? Xtrack(par, phi) : Xtrack_N(par, phi);
    for (Int_t i = 0; i < 3; i++) x(i) = xt(i);
    return x;
  }
  void VtxFitNoSteer() {
    std::vector<TVectorD*> x0i, ni;
    std::vector<TMatrixDSym*> Ci;
    std::vector<TVectorD*> wi;
    std::vector<Double_t> s_in;
    for (Int_t i = 0; i < fNtr; i++) {
      TVectorD par = *fPar[i];
      TMatrixDSym Cov = *fCov[i];
      Double_t s = 0.;
      if (fRstart > TMath::Abs(par(0))) {
        if (fCharged[i]) s = 2.*TMath::ASin(par(2)*TMath::Sqrt((fRstart*fRstart-par(0)*par(0))/(1.+2.*par(2)*par(0))));
        else             s = TMath::Sqrt(fRstart*fRstart - par(0)*par(0));
      }
      x0i.push_back(new TVectorD(Fill_x(par, s, fCharged[i])));
      TMatrixD A(3, 5);
      if (fCharged[i]) { ni.push_back(new TVectorD(derXds(par, s)));   A = derXdPar(par, s); }
      else             { ni.push_back(new TVectorD(derXds_N(par, s))); A = derXdPar_N(par, s); }
      Ci.push_back(new TMatrixDSym(Cov.Similarity(A)));
      TMatrixDSym Cinv = RegInv(*Ci[i]);
      wi.push_back(new TVectorD(Cinv * (*ni[i])));
      s_in.push_back(s);
    }
    TMatrixDSym D(3); D.Zero();
    TVectorD Dx(3); Dx.Zero();
    for (Int_t i = 0; i < fNtr; i++) {
      TMatrixDSym Cinv = RegInv(*Ci[i]);
      TMatrixDSym W(3);
      W.Rank1Update(*wi[i], 1. / Ci[i]->Similarity(*wi[i]));
      TMatrixDSym Dd = Cinv - W;
      D += Dd; Dx += Dd * (*x0i[i]);
    }
    if (fVtxCst) { D += fCovCstInv; Dx += fCovCstInv * fxCst; }
    fXv = RegInv(D) * Dx;
    fChi2 = 0.0;
    for (Int_t i = 0; i < fNtr; i++) {
      TVectorD r = (*x0i[i]) - fXv;
      TMatrixDSym Cinv = RegInv(*Ci[i]);
      TMatrixDSym W(3);
      W.Rank1Update(*wi[i], 1. / Ci[i]->Similarity(*wi[i]));
      TMatrixDSym Dd = Cinv - W;
      double chi2 = r * (Dd * r);
      fChi2 += chi2;
      fChi2List(i) = chi2;
    }
    for (Int_t i = 0; i < fNtr; i++) {
      Double_t si = Dot(*wi[i], fXv - (*x0i[i])) / Ci[i]->Similarity(*wi[i]);
      ffi.push_back(si + s_in[i]);
    }
    for (Int_t i = 0; i < fNtr; i++) {
      x0i[i]->Clear(); delete x0i[i];
      ni[i]->Clear();  delete ni[i];
      Ci[i]->Clear();  delete Ci[i];
      wi[i]->Clear();  delete wi[i];
    }
  }
  void VertexFitter() {
    if (fNtr < 2 && !fVtxCst) { std::cerr << "VertexFitFast: <2 tracks\n"; std::exit(1); }
    VtxFitNoSteer();
    fVtxDone = kTRUE;
  }
 public:
  VertexFitFast() : fNtr(0), fRstart(-1.), fVtxDone(kFALSE), fVtxCst(kFALSE) {
    fxCst.ResizeTo(3); fCovCst.ResizeTo(3,3); fCovCstInv.ResizeTo(3,3);
    fXv.ResizeTo(3); fcovXv.ResizeTo(3,3);
  }
  VertexFitFast(Int_t Ntr, TVectorD** trkPar, TMatrixDSym** trkCov)
      : fNtr(Ntr), fRstart(-1.), fVtxDone(kFALSE), fVtxCst(kFALSE) {
    fxCst.ResizeTo(3); fCovCst.ResizeTo(3,3); fCovCstInv.ResizeTo(3,3);
    fXv.ResizeTo(3); fcovXv.ResizeTo(3,3);
    fChi2List.ResizeTo(fNtr);
    for (Int_t i = 0; i < fNtr; i++) {
      fPar.push_back(new TVectorD(*trkPar[i]));
      fParNew.push_back(new TVectorD(*trkPar[i]));
      fCov.push_back(new TMatrixDSym(*trkCov[i]));
      fCovNew.push_back(new TMatrixDSym(*trkCov[i]));
      fCharged.push_back(kTRUE);
    }
  }
  ~VertexFitFast() {
    fxCst.Clear(); fCovCst.Clear(); fCovCstInv.Clear();
    fXv.Clear(); fcovXv.Clear(); fChi2List.Clear();
    for (Int_t i = 0; i < fNtr; i++) {
      fPar[i]->Clear(); delete fPar[i]; fParNew[i]->Clear(); delete fParNew[i];
      fCov[i]->Clear(); delete fCov[i]; fCovNew[i]->Clear(); delete fCovNew[i];
    }
    ResetWrkArrays(); ffi.clear(); fCharged.clear(); fNtr = 0;
  }
  TVectorD      GetVtx()        { if (!fVtxDone) VertexFitter(); return fXv; }
  TMatrixDSym   GetVtxCov()     { if (!fVtxDone) VertexFitter(); return fcovXv; }
  Double_t      GetVtxChi2()    { if (!fVtxDone) VertexFitter(); return fChi2; }
  TVectorD      GetVtxChi2List(){ if (!fVtxDone) VertexFitter(); return fChi2List; }
};
// -----------------------------------------------------------------------

namespace FCCAnalyses {

namespace VertexFitterSimple {

int supress_stdout() {
  fflush(stdout);

  int ret = dup(1);
  int nullfd = open("/dev/null", O_WRONLY);
  // check nullfd for error omitted
  dup2(nullfd, 1);
  close(nullfd);

  return ret;
}

void resume_stdout(int fd) {
  fflush(stdout);
  dup2(fd, 1);
  close(fd);
  std::cout << std::flush;
}

// -----------------------------------------------------------------------------

VertexingUtils::FCCAnalysesVertex VertexFitter(
    int Primary,
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> recoparticles,
    ROOT::VecOps::RVec<edm4hep::TrackState> thetracks, bool BeamSpotConstraint,
    double bsc_sigmax, double bsc_sigmay, double bsc_sigmaz, double bsc_x,
    double bsc_y, double bsc_z) {

  // input = a collection of recoparticles (in case one want to make
  // associations to RecoParticles ?) and thetracks = the collection of all
  // TrackState in the event

  VertexingUtils::FCCAnalysesVertex thevertex;

  // retrieve the tracks associated to the recoparticles
  ROOT::VecOps::RVec<edm4hep::TrackState> tracks =
      ReconstructedParticle2Track::getRP2TRK(recoparticles, thetracks);

  // and run the vertex fitter

  // FCCAnalysesVertex thevertex = VertexFitter_Tk( Primary, tracks, thetracks)
  // ;
  thevertex =
      VertexFitter_Tk(Primary, tracks, thetracks, BeamSpotConstraint,
                      bsc_sigmax, bsc_sigmay, bsc_sigmaz, bsc_x, bsc_y, bsc_z);

  // fill the indices of the tracks
  ROOT::VecOps::RVec<int> reco_ind;
  int Ntr = tracks.size();
  for (auto &p : recoparticles) {
    // std::cout << " in VertexFitter:  a recoparticle with charge = " <<
    // p.charge << std::endl;
    if (p.tracks_begin >= 0 && p.tracks_begin < thetracks.size()) {
      reco_ind.push_back(p.tracks_begin);
    }
  }
  if (reco_ind.size() != Ntr)
    std::cout << " ... problem in Vertex, size of reco_ind != Ntr "
              << std::endl;

  thevertex.reco_ind = reco_ind;

  return thevertex;
}

// ---------------------------------------------------------------------------------------------------------------------------

VertexingUtils::FCCAnalysesVertex
VertexFitter_Tk(int Primary, ROOT::VecOps::RVec<edm4hep::TrackState> tracks,
                bool BeamSpotConstraint, double bsc_sigmax, double bsc_sigmay,
                double bsc_sigmaz, double bsc_x, double bsc_y, double bsc_z,
                double solenoidBz, bool rescale_cm_mm, bool fast) {

  ROOT::VecOps::RVec<edm4hep::TrackState> dummy;
  return VertexFitter_Tk(Primary, tracks, dummy, BeamSpotConstraint, bsc_sigmax,
                         bsc_sigmay, bsc_sigmaz, bsc_x, bsc_y, bsc_z, solenoidBz,
                         rescale_cm_mm, fast);
}

// ---------------------------------------------------------------------------------------------------------------------------

VertexingUtils::FCCAnalysesVertex
VertexFitter_Tk(int Primary, ROOT::VecOps::RVec<edm4hep::TrackState> tracks,
                const ROOT::VecOps::RVec<edm4hep::TrackState> &alltracks,
                bool BeamSpotConstraint, double bsc_sigmax, double bsc_sigmay,
                double bsc_sigmaz, double bsc_x, double bsc_y, double bsc_z,
                double solenoidBz, bool rescale_cm_mm, bool fast) {
  // Suppressing printf() output from TMatrixBase:
  // https://github.com/root-project/root/blob/722eb4652bfc79149df00c8b0e92d0837caf054c/math/matrix/src/TMatrixTBase.cxx#L662
  // The solution found here:
  // https://stackoverflow.com/questions/46728680/how-to-temporarily-suppress-output-from-printf
  int fd = supress_stdout();

  // Units for the beam-spot : mum
  // See
  // https://github.com/HEP-FCC/FCCeePhysicsPerformance/tree/master/General#generating-events-under-realistic-fcc-ee-environment-conditions

  // final results :
  VertexingUtils::FCCAnalysesVertex TheVertex;

  edm4hep::VertexData result;
  ROOT::VecOps::RVec<float> reco_chi2;
  ROOT::VecOps::RVec<TVectorD> updated_track_parameters;
  ROOT::VecOps::RVec<int> reco_ind;
  ROOT::VecOps::RVec<float> final_track_phases;
  ROOT::VecOps::RVec<TVector3> updated_track_momentum_at_vertex;

  // if the collection of all tracks has been passed, keep trace of the indices
  // of the tracks that are used to fit this vertex
  if (alltracks.size() > 0) {
    for (int i = 0; i < tracks.size(); i++) { // the fitted tracks
      edm4hep::TrackState tr1 = tracks[i];
      for (int j = 0; j < alltracks.size();
           j++) { // the collection of all tracks
        edm4hep::TrackState tr2 = alltracks[j];
        if (VertexingUtils::compare_Tracks(tr1, tr2)) {
          reco_ind.push_back(j);
          break;
        }
      }
    }
  }

  TheVertex.vertex = result;
  TheVertex.reco_chi2 = reco_chi2;
  TheVertex.updated_track_parameters = updated_track_parameters;
  TheVertex.reco_ind = reco_ind;
  TheVertex.final_track_phases = final_track_phases;
  TheVertex.updated_track_momentum_at_vertex = updated_track_momentum_at_vertex;

  int Ntr = tracks.size();
  TheVertex.ntracks = Ntr;
  if (Ntr <= 1) {
    resume_stdout(fd);
    return TheVertex; // can not reconstruct a vertex with only one track...
  }

  TVectorD **trkPar = new TVectorD *[Ntr];
  TMatrixDSym **trkCov = new TMatrixDSym *[Ntr];

  bool Units_mm = true;

  for (Int_t i = 0; i < Ntr; i++) {
    edm4hep::TrackState t = tracks[i];
    TVectorD par = VertexingUtils::get_trackParam(t, Units_mm);
    trkPar[i] = new TVectorD(par);
    TMatrixDSym Cov = VertexingUtils::get_trackCov(t, Units_mm);
    trkCov[i] = new TMatrixDSym(Cov);
  }

  if (fast) {
    VertexFitFast theVertexFitFast(Ntr, trkPar, trkCov);
    TVectorD x = theVertexFitFast.GetVtx();
    result.position = edm4hep::Vector3f(x(0), x(1), x(2));
    float Chi2 = theVertexFitFast.GetVtxChi2();
    float Ndof = 2.0 * Ntr - 3.0;
    result.chi2 = Chi2 / Ndof;
    TheVertex.vertex = result;
    // per-track chi2: the prefilter in addTrack_best cuts on it, so it must be filled
    // here as well as in the full fit (mirrors VertexFitterMod in the ntuplizer)
    TVectorD tracks_chi2 = theVertexFitFast.GetVtxChi2List();
    for (Int_t i = 0; i < Ntr; i++) {
      reco_chi2.push_back(tracks_chi2[i]);
    }
    TheVertex.reco_chi2 = reco_chi2;
    for (Int_t i = 0; i < Ntr; i++) { delete trkPar[i]; delete trkCov[i]; }
    delete[] trkPar; delete[] trkCov;
    resume_stdout(fd);
    return TheVertex;
  }

  VertexFit theVertexFit(Ntr, trkPar, trkCov);

  if (BeamSpotConstraint) {
    float conv_BSC = 1e-3; // convert mum to mm
    TVectorD xv_BS(3);
    xv_BS[0] = bsc_x * conv_BSC;
    xv_BS[1] = bsc_y * conv_BSC;
    xv_BS[2] = bsc_z * conv_BSC;
    TMatrixDSym cov_BS(3);
    cov_BS[0][0] = pow(bsc_sigmax * conv_BSC, 2);
    cov_BS[1][1] = pow(bsc_sigmay * conv_BSC, 2);
    cov_BS[2][2] = pow(bsc_sigmaz * conv_BSC, 2);
    theVertexFit.AddVtxConstraint(xv_BS, cov_BS);
  }

  TVectorD x = theVertexFit.GetVtx(); // this actually runs the fit

  result.position =
      edm4hep::Vector3f(x(0), x(1), x(2)); // vertex position in mm

  // store the results in an edm4hep::VertexData object

  float Chi2 = theVertexFit.GetVtxChi2();
  float Ndof = 2.0 * Ntr - 3.0;
  ;
  result.chi2 = Chi2 / Ndof;

  // the chi2 of all the tracks :
  TVectorD tracks_chi2 = theVertexFit.GetVtxChi2List();
  for (int it = 0; it < Ntr; it++) {
    reco_chi2.push_back(tracks_chi2[it]);
  }

  // std::cout << " Fitted vertex: " <<  x(0)*conv << " " << x(1)*conv << " " <<
  // x(2)*conv << std::endl;
  TMatrixDSym covX = theVertexFit.GetVtxCov();
  std::array<float, 6>
      covMatrix; // covMat in edm4hep is a LOWER-triangle matrix.
  covMatrix[0] = covX(0, 0);
  covMatrix[1] = covX(1, 0);
  covMatrix[2] = covX(1, 1);
  covMatrix[3] = covX(2, 0);
  covMatrix[4] = covX(2, 1);
  covMatrix[5] = covX(2, 2);
  result.covMatrix = covMatrix;

  result.algorithmType = 1;

#if EDM4HEP_BUILD_VERSION <= EDM4HEP_VERSION(0, 10, 5)
  result.primary = Primary;
#else
  result.type = Primary; // NOTE: Here we are relying on users passing in the
                         // correct value
#endif
  TheVertex.vertex = result;

  if (rescale_cm_mm) {
    // Second fit with track parameters rescaled to mm units for VertexMore.
    // Use when input tracks have D0/Z0 in cm and omega in cm^-1 (ALEPH native).
    // Mirrors VertexFitterMod in the ntuplizer (analyzer_svfinder.cxx).
    TVectorD **trkPar_2 = new TVectorD *[Ntr];
    TMatrixDSym **trkCov_2 = new TMatrixDSym *[Ntr];
    for (Int_t i = 0; i < Ntr; i++) {
      edm4hep::TrackState t = tracks[i];
      TVectorD par = VertexingUtils::get_trackParam(t, Units_mm);
      par[0] *= 10;                   // D0: cm → mm
      par[2] /= 10;                   // omega: cm^-1 → mm^-1
      par[3] *= 10;                   // Z0: cm → mm
      par[2] *= (2.0 / solenoidBz);  // correct for VertexMore's hardcoded 2 T
      trkPar_2[i] = new TVectorD(par);
      TMatrixDSym Cov = VertexingUtils::get_trackCov(t, Units_mm);
      trkCov_2[i] = new TMatrixDSym(Cov);
    }
    VertexFit theVertexFit_2(Ntr, trkPar_2, trkCov_2);
    theVertexFit_2.GetVtx();
    VertexMore theVertexMore(&theVertexFit_2, Units_mm);

    for (Int_t i = 0; i < Ntr; i++) {
      TVectorD updated_par = theVertexFit.GetNewPar(i);
      TVectorD updated_par_edm4hep =
          VertexingUtils::Delphes2Edm4hep_TrackParam(updated_par, Units_mm);
      updated_track_parameters.push_back(updated_par_edm4hep);
      // Momenta from the rescaled second fit — no further Bz correction needed
      TVector3 ptrack_at_vertex = theVertexMore.GetMomentum(i);
      updated_track_momentum_at_vertex.push_back(ptrack_at_vertex);
    }

    for (Int_t i = 0; i < Ntr; i++) {
      delete trkPar_2[i];
      delete trkCov_2[i];
    }
    delete[] trkPar_2;
    delete[] trkCov_2;

  } else {
    // Tracks already in mm — single fit, correct Bz post hoc
    VertexMore theVertexMore(&theVertexFit, Units_mm);
    for (Int_t i = 0; i < Ntr; i++) {
      TVectorD updated_par = theVertexFit.GetNewPar(i);
      TVectorD updated_par_edm4hep =
          VertexingUtils::Delphes2Edm4hep_TrackParam(updated_par, Units_mm);
      updated_track_parameters.push_back(updated_par_edm4hep);
      TVector3 ptrack_at_vertex = theVertexMore.GetMomentum(i) * (solenoidBz / 2.0);
      updated_track_momentum_at_vertex.push_back(ptrack_at_vertex);
    }
  }

  TheVertex.updated_track_parameters = updated_track_parameters;
  TheVertex.updated_track_momentum_at_vertex = updated_track_momentum_at_vertex;
  TheVertex.final_track_phases = final_track_phases;
  TheVertex.reco_chi2 = reco_chi2;

  // memory cleanup
  for (Int_t i = 0; i < Ntr; i++) {
    delete trkPar[i];
    delete trkCov[i];
  }
  delete[] trkPar;
  delete[] trkCov;

  resume_stdout(fd);

  return TheVertex;
}

// ---------------------------------------------------------------------------------------------------------------------------

ROOT::VecOps::RVec<edm4hep::TrackState>
get_PrimaryTracks(ROOT::VecOps::RVec<edm4hep::TrackState> tracks,
                  bool BeamSpotConstraint, double bsc_sigmax, double bsc_sigmay,
                  double bsc_sigmaz, double bsc_x, double bsc_y, double bsc_z,
                  float CHI2MAX) {
  // iterative procedure to determine the primary vertex - and the primary
  // tracks

  // Feb 2023: Avoid the recursive approach used before... else very very slow,
  // with the new VertexFit objects

  // Units for the beam-spot : mum
  // See
  // https://github.com/HEP-FCC/FCCeePhysicsPerformance/tree/master/General#generating-events-under-realistic-fcc-ee-environment-conditions

  // bool debug  = true ;
  bool debug = false;

  if (debug) {
    std::cout << " ... enter in VertexFitterSimple::get_PrimaryTracks   Ntr = "
              << tracks.size() << std::endl;
  }

  ROOT::VecOps::RVec<edm4hep::TrackState> seltracks = tracks;

  if (seltracks.size() <= 1)
    return seltracks;

  int Ntr = tracks.size();

  TVectorD **trkPar = new TVectorD *[Ntr];
  TMatrixDSym **trkCov = new TMatrixDSym *[Ntr];

  for (Int_t i = 0; i < Ntr; i++) {
    edm4hep::TrackState t = tracks[i];
    // same unit convention as VertexFitter_Tk (Units_mm = true), so the
    // selection fit and the final PV fit see the identical beamspot constraint.
    // Deliberate divergence from the luka_FCCAnalyses reference, which calls
    // get_trackParam/get_trackCov with the Units_mm=false default here: with
    // cm-native tracks its selection-fit beamspot constraint is off by x1000,
    // i.e. effectively absent. With Units_mm=true on cm-native input the fit
    // (and its covariance) is numerically in cm, not mm.
    TVectorD par = VertexingUtils::get_trackParam(t, true);
    trkPar[i] = new TVectorD(par);
    TMatrixDSym Cov = VertexingUtils::get_trackCov(t, true);
    trkCov[i] = new TMatrixDSym(Cov);
  }

  VertexFit theVertexFit(Ntr, trkPar, trkCov);

  if (BeamSpotConstraint) {
    float conv_BSC = 1e-3; // convert mum to mm, as in VertexFitter_Tk above
    TVectorD xv_BS(3);
    xv_BS[0] = bsc_x * conv_BSC;
    xv_BS[1] = bsc_y * conv_BSC;
    xv_BS[2] = bsc_z * conv_BSC;
    TMatrixDSym cov_BS(3);
    cov_BS[0][0] = pow(bsc_sigmax * conv_BSC, 2);
    cov_BS[1][1] = pow(bsc_sigmay * conv_BSC, 2);
    cov_BS[2][2] = pow(bsc_sigmaz * conv_BSC, 2);
    theVertexFit.AddVtxConstraint(xv_BS, cov_BS);
  }

  TVectorD x = theVertexFit.GetVtx(); // this actually runs the fit

  // --- check for failure ---
  if (!std::isfinite(x[0]) || 
      !std::isfinite(x[1]) || 
      !std::isfinite(x[2])) {

    std::cerr << "WARNING: Primary vertex fit returned non-finite position!"
              << " N tracks = " << Ntr << std::endl;

    return seltracks;  // return original tracks without pruning
  }

  float chi2_max = 1e30;

  while (chi2_max >= CHI2MAX) {

    TVectorD tracks_chi2 = theVertexFit.GetVtxChi2List();
    chi2_max = tracks_chi2.Max();

    for (int i = 0; i < tracks_chi2.GetNrows(); ++i) {
      if (!std::isfinite(tracks_chi2[i])) {
        std::cerr << "WARNING: Non-finite chi2 encountered in vertex fit!"
                  << " Track index = " << i << std::endl;
        return seltracks;
      }
    }

    int n_removed = 0;
    for (int i = 0; i < theVertexFit.GetNtrk(); i++) {
      float track_chi2 = tracks_chi2[i];
      if (track_chi2 >= chi2_max) {
        theVertexFit.RemoveTrk(i);
        seltracks.erase(seltracks.begin() + i);
        n_removed++;
      }
    }
    if (n_removed > 0) {
      if (theVertexFit.GetNtrk() > 1) {
        // run the fit again:
        x = theVertexFit.GetVtx();
        TVectorD new_tracks_chi2 = theVertexFit.GetVtxChi2List();
        chi2_max = new_tracks_chi2.Max();
      } else {
        chi2_max = 0; // exit from the loop w/o crashing..
      }
    }
  } // end while

  // last safety check
  if (theVertexFit.GetNtrk() == 0) {
    std::cerr << "WARNING: Vertex fit removed all tracks!" << std::endl;
  }

  // memory cleanup :
  for (Int_t i = 0; i < Ntr; i++) {
    delete trkPar[i];
    delete trkCov[i];
  }
  delete[] trkPar;
  delete[] trkCov;

  return seltracks;
}

// ---------------------------------------------------------------------------------------------------------------------------

ROOT::VecOps::RVec<edm4hep::TrackState>
get_NonPrimaryTracks(ROOT::VecOps::RVec<edm4hep::TrackState> allTracks,
                     ROOT::VecOps::RVec<edm4hep::TrackState> primaryTracks) {

  ROOT::VecOps::RVec<edm4hep::TrackState> result;
  for (auto &track : allTracks) {
    bool isInPrimary = false;
    for (auto &primary : primaryTracks) {
      if (VertexingUtils::compare_Tracks(track, primary)) {
        isInPrimary = true;
        break;
      }
    }
    if (!isInPrimary)
      result.push_back(track);
  }

  return result;
}

// ---------------------------------------------------------------------------------------------------------------------------

ROOT::VecOps::RVec<bool>
IsPrimary_forTracks(ROOT::VecOps::RVec<edm4hep::TrackState> allTracks,
                    ROOT::VecOps::RVec<edm4hep::TrackState> primaryTracks) {

  ROOT::VecOps::RVec<bool> result;
  for (auto &track : allTracks) {
    bool isInPrimary = false;
    for (auto &primary : primaryTracks) {
      if (VertexingUtils::compare_Tracks(track, primary)) {
        isInPrimary = true;
        break;
      }
    }
    result.push_back(isInPrimary);
  }
  return result;
}

} // namespace VertexFitterSimple

} // namespace FCCAnalyses
