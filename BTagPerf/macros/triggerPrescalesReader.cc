#ifndef PRESCALESEL
#define PRESCALESEL
#include <iostream>
#include "TString.h"
#include "ROOT/RVec.hxx"
#include <fstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace ROOT;
using namespace ROOT::VecOps;

class TriggerPrescalesReader {

  public:
    TriggerPrescalesReader(TString triggerInfosJSON, TString triggerPrimaryDataset_, TString triggerPrescalesFileName_);
    ~TriggerPrescalesReader();

    double operator()(double jetPt, unsigned int Run, int LumiBlock) {

      for (json::iterator it = triggerInfos.begin(); it != triggerInfos.end(); ++it) {
	  string lowPtEdge = triggerInfos[it.key()]["jetPtRange"][0], highPtEdge = triggerInfos[it.key()]["jetPtRange"][1];
	  if (jetPt>=stof(lowPtEdge) && jetPt<stof(highPtEdge)) {
              
	      string hltPath = it.key();
              if (triggerPrimaryDataset!="BTagMu") hltPath = triggerInfos[it.key()]["jetTrigger"];
	      string run = std::to_string(Run);
	      int lumiblock = -1; 
	      double prescale = 1.;

	      for (json::iterator itlb = triggerPrescales[hltPath][run].begin(); itlb != triggerPrescales[hltPath][run].end(); ++itlb) {
		  if (LumiBlock>=stoi(itlb.key()) && stoi(itlb.key())>=lumiblock) {
		      string sprescale = triggerPrescales[hltPath][run][itlb.key()];
		      lumiblock = stoi(itlb.key());
		      prescale = stof(sprescale);
		  }
	      }

	      if (lumiblock>=1) return prescale;

	  }
      }

      return 1.;

    }

  private:

    TString triggerPrimaryDataset;
    json triggerInfos, triggerPrescales;

};

TriggerPrescalesReader::TriggerPrescalesReader(TString triggerInfosJSON, TString triggerPrimaryDataset_, TString triggerPrescalesFileName_) {
 
    // https://github.com/nlohmann/json
    std::ifstream f(triggerInfosJSON);
    triggerInfos = json::parse(f);

    std::ifstream tps(triggerPrescalesFileName_);
    triggerPrescales = json::parse(tps);

    triggerPrimaryDataset = triggerPrimaryDataset_;

}

TriggerPrescalesReader::~TriggerPrescalesReader(){
}
 
#endif
