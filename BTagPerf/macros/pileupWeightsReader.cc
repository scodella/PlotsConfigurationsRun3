#ifndef PILEUPSEL
#define PILEUPSEL
#include <iostream>
#include "TString.h"
#include <vector>
#include "TFile.h"
#include "TH2.h"
#include "TH2F.h"

class PileupWeightsReader {

  public:
    PileupWeightsReader(TString weightFileName_);
    ~PileupWeightsReader();

    vector<double> operator()(double nTruePU) {

        vector<double> pileupWeightsReader;

        for (int pusyst = -1; pusyst<=1; pusyst++) {

            double pileupWeight = -1.;
            if (pusyst==-1) pileupWeight = this->GetBinContent4Weight(pileupWeightsDownHisto, nTruePU);
            if (pusyst==0)  pileupWeight = this->GetBinContent4Weight(pileupWeightsHisto,     nTruePU);
            if (pusyst==1)  pileupWeight = this->GetBinContent4Weight(pileupWeightsUpHisto,   nTruePU);

            if (pileupWeight<=0.)
                std::cout << "PileupWeightsReader Error for " << weightFileName << " " << nTruePU << std::endl;

            pileupWeightsReader.push_back(pileupWeight);

        }

	return pileupWeightsReader;

    }

  private:
    double GetBinContent4Weight(TH1* hist, double valx);

    TString weightFileName;
    TH2F*  pileupWeightsHisto{};
    TH2F*  pileupWeightsUpHisto{};
    TH2F*  pileupWeightsDownHisto{};

};

double PileupWeightsReader::GetBinContent4Weight(TH1* hist, double valx) { 

  double xmin=hist->GetXaxis()->GetXmin();
  double xmax=hist->GetXaxis()->GetXmax();
  if(xmin>=0) valx=fabs(valx);
  if(valx<xmin) valx=xmin+0.001;
  if(valx>xmax) valx=xmax-0.001;
  return hist->GetBinContent(hist->FindBin(valx));

}

PileupWeightsReader::PileupWeightsReader(TString weightFileName_) {

  weightFileName = weightFileName_;
  TFile* weightFile = new TFile(weightFileName);
  pileupWeightsHisto     = (TH2F*) weightFile->Get("pileup");
  pileupWeightsUpHisto   = (TH2F*) weightFile->Get("pileup_plus");
  pileupWeightsDownHisto = (TH2F*) weightFile->Get("pileup_minus"); 

}

PileupWeightsReader::~PileupWeightsReader(){
}
 
#endif
