#ifndef KINWEIGHTSEL
#define KINWEIGHTSEL
#include <iostream>
#include "TString.h"
#include "ROOT/RVec.hxx"
#include <fstream>
#include <vector>
#include "TFile.h"
#include "TH2.h"
#include "TH2F.h"

using namespace ROOT;
using namespace ROOT::VecOps;

class KinematicWeightsReader {

  public:
    KinematicWeightsReader(TString weightFile_, TString histoName_);
    ~KinematicWeightsReader();

    vector<double> operator()(int nJet, RVecD Jet_pt, RVecD Jet_eta) {
     
      vector<double> kinematicWeights;

      for (int ijet = 0; ijet<nJet; ijet++) {

        double JetPt  = Jet_pt[ijet];
        double JetEta = Jet_eta[ijet];

        double kinematicWeight = this->GetBinContent4Weight(kinematicWeightsHisto, JetPt, JetEta, 0);

        if (kinematicWeight<=0.)
          std::cout << "KinematicWeightsReader Error for " << weightFile << " " << histoName << " " << JetPt << " " << JetEta << std::endl;

	kinematicWeights.push_back(kinematicWeight);

      }

      return kinematicWeights;

    }

    double operator()(double JetPt, double JetEta) {

      double kinematicWeight = this->GetBinContent4Weight(kinematicWeightsHisto, JetPt, JetEta, 0);

      if (kinematicWeight<=0.)
        std::cout << "KinematicWeightsReader Error for " << weightFile << " " << histoName << " " << JetPt << " " << JetEta << std::endl;

      return kinematicWeight;

    }

  private:
    double GetBinContent4Weight(TH2* hist, double valx, double valy, double sys);
    TString weightFile, histoName;
    TH2F* kinematicWeightsHisto;

};

double KinematicWeightsReader::GetBinContent4Weight(TH2* hist, double valx, double valy, double sys){

  double xmin=hist->GetXaxis()->GetXmin();
  double xmax=hist->GetXaxis()->GetXmax();
  double ymin=hist->GetYaxis()->GetXmin();
  double ymax=hist->GetYaxis()->GetXmax();
  if(xmin>=0) valx=fabs(valx);
  if(valx<xmin) valx=xmin+0.001;
  if(valx>xmax) valx=xmax-0.001;
  if(ymin>=0) valy=fabs(valy);
  if(valy<ymin) valy=ymin+0.001;
  if(valy>ymax) valy=ymax-0.001;
  float weight = hist->GetBinContent(hist->FindBin(valx,valy));
  if (sys!=0) {
    weight += sys*hist->GetBinError(hist->FindBin(valx,valy));
  }
  return weight;

}

KinematicWeightsReader::KinematicWeightsReader(TString weightFile_, TString histoName_) {

    weightFile = weightFile_;
    histoName  = histoName_;
    TFile* rootFile = new TFile(weightFile);
    kinematicWeightsHisto = (TH2F*) rootFile->Get(histoName);	

}

KinematicWeightsReader::~KinematicWeightsReader(){
}
 
#endif
