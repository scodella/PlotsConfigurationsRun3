#ifndef AWAYJETSEL
#define AWAYJETSEL
#include <iostream>
#include "TString.h"
#include "ROOT/RVec.hxx"
#include <fstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace ROOT;
using namespace ROOT::VecOps;

class AwayJetSelector {

  public:
    AwayJetSelector(TString triggerInfosJSON, bool awayJetIsUnique_, bool awayJetTagOnLeading_, double minJetPt_, double maxJetEta_, double awayJetDeltaRCut_, double awayJetBTagCut_);
    ~AwayJetSelector();

    json triggerInfos;
    bool awayJetIsUnique, awayJetTagOnLeading;
    double minJetPt, maxJetEta, awayJetDeltaRCut, awayJetBTagCut;

    bool operator()(int muonJetIndex, int nJets, RVecD Jet_pt, RVecD Jet_eta, RVecD Jet_phi, RVecI Jet_tightID, RVecD Jet_btagDiscriminant) {
     
      int nAwayJets = 0;
      double awayJetPt = -1., awayJetBTagDiscriminant = -999.;

      for (int ijet = 0; ijet<nJets; ijet++) {
        if (ijet!=muonJetIndex && Jet_pt[ijet]>=minJetPt && fabs(Jet_eta[ijet])<maxJetEta && Jet_tightID[ijet]==1) {

	    double awayJetDeltaPhi = acos(cos(Jet_phi[ijet]-Jet_phi[muonJetIndex]));
            double awayJetDeltaEta = (Jet_eta[ijet]-Jet_eta[muonJetIndex]);
            double awayJetDeltaR  = sqrt(awayJetDeltaPhi*awayJetDeltaPhi + awayJetDeltaEta*awayJetDeltaEta);
            if (awayJetDeltaR>awayJetDeltaRCut) {
		if (Jet_btagDiscriminant[ijet]>=awayJetBTagCut || awayJetTagOnLeading) {
		    if (Jet_pt[ijet]>awayJetPt) {

		        awayJetPt = Jet_pt[ijet];
			awayJetBTagDiscriminant = Jet_btagDiscriminant[ijet];
			nAwayJets++;

		    }	    
		}
	    }	

	}
      }

      if (nAwayJets==0) return false;      
      if (awayJetTagOnLeading && awayJetBTagDiscriminant<awayJetBTagCut) return false;
      if (awayJetIsUnique && nAwayJets>1) return false;

      for (json::iterator it = triggerInfos.begin(); it != triggerInfos.end(); ++it) {
	  string lowPtEdge = triggerInfos[it.key()]["jetPtRange"][0], highPtEdge = triggerInfos[it.key()]["jetPtRange"][1];
	  if (Jet_pt[muonJetIndex]>=stof(lowPtEdge) && Jet_pt[muonJetIndex]<stof(highPtEdge)) {
	      if (awayJetPt>=triggerInfos[it.key()]["ptAwayJet"]) return true;
	  }
      }

      return false;

    }

  private:

};

AwayJetSelector::AwayJetSelector(TString triggerInfosJSON, bool awayJetIsUnique_, bool awayJetTagOnLeading_, double minJetPt_, double maxJetEta_, double awayJetDeltaRCut_, double awayJetBTagCut_) {
 
    std::ifstream f(triggerInfosJSON);
    triggerInfos = json::parse(f);

    awayJetIsUnique        = awayJetIsUnique_;
    awayJetTagOnLeading    = awayJetTagOnLeading_;
    minJetPt               = minJetPt_;
    maxJetEta              = maxJetEta_;
    awayJetDeltaRCut       = awayJetDeltaRCut_;
    awayJetBTagCut         = awayJetBTagCut_;

}

AwayJetSelector::~AwayJetSelector(){
}
 
#endif
