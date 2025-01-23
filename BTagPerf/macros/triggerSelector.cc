#ifndef TRIGGERSEL
#define TRIGGERSEL
#include <iostream>
#include "TString.h"
#include "ROOT/RVec.hxx"
#include <fstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace ROOT;
using namespace ROOT::VecOps;

class TriggerSelector {

  public:
    TriggerSelector(TString triggerInfosJSON, TString triggerPrimaryDataset_, bool applyTriggerEmulation_, double maxJetEta_);
    ~TriggerSelector();

    json triggerInfos;
    TString triggerPrimaryDataset;
    bool applyTriggerEmulation;
    double maxJetEta;

    bool operator()(int muonJetIndex, int nJets, RVecD Jet_pt, RVecD Jet_eta, RVecI Jet_tightID, RVecI BitTrigger) {
      
      TString triggerPath = "None"; int triggerIdx; double ptTriggerEmulation;
      for (json::iterator it = triggerInfos.begin(); it != triggerInfos.end(); ++it) {
	  string lowPtEdge = triggerInfos[it.key()]["jetPtRange"][0], highPtEdge = triggerInfos[it.key()]["jetPtRange"][1];
	  if (Jet_pt[muonJetIndex]>=stof(lowPtEdge) && Jet_pt[muonJetIndex]<stof(highPtEdge)) {
              triggerPath = it.key();
	      triggerIdx = (triggerPrimaryDataset=="BTagMu") ? triggerInfos[it.key()]["idx"] : triggerInfos[it.key()]["idxJetTrigger"];
	      ptTriggerEmulation = triggerInfos[it.key()]["ptTriggerEmulation"];
	  }
      }

      if (triggerPath=="None") return false;

      int bitIdx = int(triggerIdx/32);
      bool triggerPass = ( BitTrigger[bitIdx] & ( 1 << (triggerIdx - bitIdx*32) ) );

      if (!triggerPass || !applyTriggerEmulation || ptTriggerEmulation==0.) return triggerPass;

      for (int ijet = 0; ijet<nJets; ijet++)
	  if (ijet!=muonJetIndex && fabs(Jet_eta[ijet])<maxJetEta && Jet_tightID[ijet]==1 && Jet_pt[ijet]>=ptTriggerEmulation) return true;

      return false;

    }

  private:

};

TriggerSelector::TriggerSelector(TString triggerInfosJSON, TString triggerPrimaryDataset_, bool applyTriggerEmulation_, double maxJetEta_) {
 
    // https://github.com/nlohmann/json
    std::ifstream f(triggerInfosJSON);
    triggerInfos = json::parse(f);

    triggerPrimaryDataset = triggerPrimaryDataset_;
    applyTriggerEmulation = applyTriggerEmulation_;
    maxJetEta = maxJetEta_;

}

TriggerSelector::~TriggerSelector(){
}
 
#endif
