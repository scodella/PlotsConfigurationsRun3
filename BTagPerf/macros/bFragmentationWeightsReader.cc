#ifndef BFRAGSEL
#define BFRAGSEL
#include <iostream>
#include "TString.h"
#include <vector>
#include "TFile.h"
#include "TH2.h"
#include "TH2F.h"
#include "TGraph.h"
#include "ROOT/RVec.hxx"

using namespace ROOT;
using namespace ROOT::VecOps;

class BFragmentationWeightsReader {

  public:
    BFragmentationWeightsReader(TString bfragWeightFile_, TString histoName_, TString bdecayWeightFile_);
    ~BFragmentationWeightsReader();

    vector<double> operator()( int    muonJetIndex,
			       int    muonJetFlavour,
                               double muonJetEta,
                               double muonJetPhi,
			       double muonJetGenPt,
                               int    nBHadron,
                               RVecF  BHadron_pT,
                               RVecF  BHadron_eta,
                               RVecF  BHadron_phi,
                               RVecD  BHadron_mass,
                               RVecI  BHadron_pdgID,
                               RVecL  BHadron_hasBdaughter) {

        vector<double> bFragmentationWeightsReader;
        
        double xB = -1., genJetPt = -1.;
        int bHadronId = -1;

	if (muonJetIndex>=0 && fabs(muonJetFlavour)==5) {
 
          double maxBHadronMass = -1.;

          for (int ibh = 0; ibh<nBHadron; ibh++) {

            float bHadronEta = BHadron_eta[ibh];
            float bHadronPhi = BHadron_phi[ibh];

            double DeltaPhi = acos(cos(bHadronPhi-muonJetPhi));
            double DeltaEta = bHadronEta-muonJetEta;
            if (sqrt(DeltaPhi*DeltaPhi+DeltaEta*DeltaEta)<0.5) {

              double    bHadronMass = BHadron_mass[ibh];
              float     bHadronPt = BHadron_pT[ibh];
              long long bHadronHasDaughter = BHadron_hasBdaughter[ibh];

              if (bHadronMass>maxBHadronMass) {
                genJetPt       = muonJetGenPt;
                xB             = bHadronPt/fabs(genJetPt);
                maxBHadronMass = bHadronMass;
              }

              if (bHadronHasDaughter==0) bHadronId = abs(BHadron_pdgID[ibh]);

            }

          }

        }

        for (int bfsyst = 0; bfsyst<=4; bfsyst++) {

          double bFragmentationWeight = -1.;

	  if (muonJetIndex>=0 && abs(muonJetFlavour)==5) {

            bFragmentationWeight = -1.;
            if (bfsyst==0) bFragmentationWeight = this->GetBFragWeight(bFragmentationWeightsDownHisto, xB, genJetPt);
            if (bfsyst==1) bFragmentationWeight = this->GetBFragWeight(bFragmentationWeightsHisto,     xB, genJetPt);
            if (bfsyst==2) bFragmentationWeight = this->GetBFragWeight(bFragmentationWeightsUpHisto,   xB, genJetPt);
            if (bfsyst==3) bFragmentationWeight = this->GetBRWeight(bdecayWeightsDownGraph,             bHadronId);
            if (bfsyst==4) bFragmentationWeight = this->GetBRWeight(bdecayWeightsUpGraph,               bHadronId);

            if (bFragmentationWeight<=0.) {
              if (bfsyst<=2) { std::cout << "BFragmentationWeightsReader Error for " << bfragWeightFile << " " << xB << " " << genJetPt << std::endl; }
              else { std::cout << "BFragmentationWeightsReader Error for " << bdecayWeightFile << " " << bHadronId << std::endl; }
            }

          } else { bFragmentationWeight = 1.; }

	  bFragmentationWeightsReader.push_back(bFragmentationWeight);

        }

	return bFragmentationWeightsReader;

    }

  private:
    double GetBFragWeight(TH2* hist, double xB, double genJetPt);
    double GetBRWeight(TGraph* graph, int bHadronId);

    TString bfragWeightFile, bdecayWeightFile;

    TH2F*   bFragmentationWeightsHisto;
    TH2F*   bFragmentationWeightsUpHisto;
    TH2F*   bFragmentationWeightsDownHisto;
    TGraph* bdecayWeightsUpGraph;
    TGraph* bdecayWeightsDownGraph;

};

double BFragmentationWeightsReader::GetBFragWeight(TH2* hist, double xB, double genJetPt) {

  if (xB<1 && genJetPt>=30) {
    size_t xb_bin = hist->GetXaxis()->FindBin(xB);
    size_t pt_bin = hist->GetYaxis()->FindBin(genJetPt);
    return hist->GetBinContent(xb_bin, pt_bin);
  } else {
    return 1.;
  }

}

double BFragmentationWeightsReader::GetBRWeight(TGraph* graph, int bHadronId) {

  if (bHadronId == 511 ||  bHadronId == 521 ||  bHadronId == 531 ||  bHadronId == 5122) {
    //int bid(jinfo.hasSemiLepDecay ? absBid : -absBid);
    return graph->Eval(bHadronId);
  } else {
    return 1.;
  }

}

BFragmentationWeightsReader::BFragmentationWeightsReader(TString bfragWeightFile_, TString histoName_, TString bdecayWeightFile_) {

  bfragWeightFile = bfragWeightFile_;
  TFile* bfragRootFile = new TFile(bfragWeightFile);
  bFragmentationWeightsHisto     = (TH2F*) bfragRootFile->Get(histoName_);
  bFragmentationWeightsUpHisto   = (TH2F*) bfragRootFile->Get(histoName_+"up");
  bFragmentationWeightsDownHisto = (TH2F*) bfragRootFile->Get(histoName_+"down");

  bdecayWeightFile = bdecayWeightFile_;
  TFile* bdecayRootFile = new TFile(bdecayWeightFile);
  bdecayWeightsUpGraph   = (TGraph*) bdecayRootFile->Get("semilepbrup");
  bdecayWeightsDownGraph = (TGraph*) bdecayRootFile->Get("semilepbrdown");

}

BFragmentationWeightsReader::~BFragmentationWeightsReader(){
}
 
#endif
