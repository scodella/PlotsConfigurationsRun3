#ifndef softMuonFinder
#define softMuonFinder

#include "ROOT/RVec.hxx"

using namespace ROOT;
using namespace ROOT::VecOps;

int SoftMuonFinder( int    nPFMuon, int nJet,
	 	    RVecD  PFMuon_pt, 
	            RVecD  PFMuon_eta, 
  		    RVecL  PFMuon_GoodQuality, 
		    RVecL  PFMuon_IdxJet,
	            bool   mustBeUnique=true ) {

  int nGoodSoftMuon = 0, muonIndex = -1, muonJetIndex = -1;
  float ptMaxMuon = 0.;

  for (int imu = 0; imu<nPFMuon; imu++) {

    double muPt      = PFMuon_pt[imu];
    double muEta     = PFMuon_eta[imu];
    int    muQuality = PFMuon_GoodQuality[imu];
    int    muJet     = PFMuon_IdxJet[imu];

    if (muQuality>=2 && muPt>5. && muEta>-2.4 && muEta<2.4 && muJet>=0) {
      if (muPt>ptMaxMuon) {
        muonIndex = imu;
        muonJetIndex = muJet;
        ptMaxMuon = muPt;
      }
      nGoodSoftMuon++;
    }

  }

  if (nGoodSoftMuon==0 || mustBeUnique && nGoodSoftMuon>1) return -1;

  return muonIndex;

}

#endif

