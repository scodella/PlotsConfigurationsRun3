#ifndef JEU
#define JEU
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

class JetEnergyUncertaintyReader {

  public:
    JetEnergyUncertaintyReader(TString jeuFileName_);
    ~JetEnergyUncertaintyReader();

    vector<float> operator()(int nJet, RVecD Jet_pt, RVecD Jet_eta, TString jeuVariation) {
     
      vector<float> correctedJetEnergies;

      for (int ijet = 0; ijet<nJet; ijet++) {

        double JetPt  = Jet_pt[ijet];
        double JetEta = Jet_eta[ijet];

        double jetEnergyUncertaintyValue = GetJetEnergyUncertaintyValue(JetPt, JetEta);

        if (jeuVariation=="Down") correctedJetEnergies.push_back(JetPt*(1.-jetEnergyUncertaintyValue));
        else if (jeuVariation=="Up") correctedJetEnergies.push_back(JetPt*(1.+jetEnergyUncertaintyValue));

      }

      return correctedJetEnergies;

    }

    float operator()(int nJet, double JetPt, double JetEta, TString jeuVariation) {

      if (nJet==0) return -1.;

      float jetEnergyUncertaintyValue = GetJetEnergyUncertaintyValue(JetPt, JetEta);	   

      if (jeuVariation=="Down") return JetPt*(1.-jetEnergyUncertaintyValue);
      else return JetPt*(1.+jetEnergyUncertaintyValue);

    }

  private:
    float GetJetEnergyUncertaintyValue(double JetPt, double JetEta);

    TString jeuFileName;
    int nJEUEtaBin, nJEUPtPoint;

    static const int nJEUEtaBins = 500, nJEUPtPoints = 500;
    float JEUEtaEdge[nJEUEtaBins][2];
    float JEUPtPoint[nJEUPtPoints];
    float Jet_JEU[nJEUEtaBins][nJEUPtPoints][2];

};

float JetEnergyUncertaintyReader::GetJetEnergyUncertaintyValue(double JetPt, double JetEta) {

  float jetEnergyUncertaintyValue = -1.;

  for (int ib = 0; ib<nJEUEtaBin; ib++)
    if (JetEta>=JEUEtaEdge[ib][0] && JetEta<JEUEtaEdge[ib][1])
      for (int ipt = 0; ipt<nJEUPtPoint; ipt++)
        if (JetPt>=JEUPtPoint[ipt]) jetEnergyUncertaintyValue = Jet_JEU[ib][ipt][0];

  if (jetEnergyUncertaintyValue<=0.) {
    std::cout << "JetEnergyUncertaintyReader Error for " << jeuFileName << " " << JetPt << " " << JetEta << " " << jetEnergyUncertaintyValue << std::endl;
    return 1.;
  }

  return jetEnergyUncertaintyValue;

}

JetEnergyUncertaintyReader::JetEnergyUncertaintyReader(TString jeuFileName_) {

  jeuFileName = jeuFileName_;
  ifstream jeuFile; jeuFile.open(jeuFileName);
  if (!jeuFile) throw std::invalid_argument("JEU file not found!");

  nJEUEtaBin = 0;

  std::string delimiter = " ";

  std::string line;

  while (std::getline(jeuFile, line)) {

    if (line.find("{")!=std::string::npos) continue;

    nJEUPtPoint = 0;

    int ntoken = 0;
    size_t pos = 0;
    std::string token;

    while ((pos = line.find(delimiter)) != std::string::npos) {
      token = line.substr(0, pos);
      if (ntoken==0) JEUEtaEdge[nJEUEtaBin][0] = atof(token.c_str());
      else if (ntoken==1) JEUEtaEdge[nJEUEtaBin][1] = atof(token.c_str());
      else if (ntoken==2) {
        if (atoi(token.c_str())!=150) throw std::invalid_argument("Bad bho value reading JEU file");
      } else {
        if (ntoken%3==0) {
          JEUPtPoint[nJEUPtPoint] = atof(token.c_str());
        } else if (ntoken%3==1) {
          Jet_JEU[nJEUEtaBin][nJEUPtPoint][0] = atof(token.c_str());
        } else if (ntoken%3==2) {
          Jet_JEU[nJEUEtaBin][nJEUPtPoint][1] = atof(token.c_str());
          if (Jet_JEU[nJEUEtaBin][nJEUPtPoint][0]!=Jet_JEU[nJEUEtaBin][nJEUPtPoint][1]) throw std::invalid_argument("Asymmetric uncertainties reading JEU file");
          nJEUPtPoint++;
        }
      }
      line.erase(0, pos + delimiter.length());
      ntoken++;
    }

    nJEUEtaBin++;

  }

}

JetEnergyUncertaintyReader::~JetEnergyUncertaintyReader(){
}
 
#endif
