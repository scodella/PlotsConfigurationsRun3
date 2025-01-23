#ifndef MUONSEL
#define MUONSEL
#include <vector>
#include <iostream>

class SoftMuonSelector {

  public:
    SoftMuonSelector(int nMuSelBins_, 
		     vector<double> jetPtEdge_, 
		     vector<double> muonPtCut_, 
		     vector<double> muonJetDRCut_,
		     bool verbose_ = false);
    ~SoftMuonSelector();

    int nMuSelBins;
    vector<double> jetPtEdge, muonPtCut, muonJetDRCut; 
    bool verbose;

    bool operator()(int softMuonIndex, double jetPt, double muonPt, double muonJetDR) {
      
      if (softMuonIndex<0) return false;

      for (int muSelBin = nMuSelBins-1; muSelBin>=0; muSelBin--) {
        if (jetPt>jetPtEdge[muSelBin]) {

	  if (verbose)
	    std::cout << "muonSelection " << jetPt << " " << jetPtEdge[muSelBin] << " " << muonPt << " " << muonPtCut[muSelBin] << " " << muonJetDR << " " << muonJetDRCut[muSelBin] << std::endl;

	  if (muonPt>=muonPtCut[muSelBin] && muonJetDR<muonJetDRCut[muSelBin]) {
            if (verbose) std::cout << " muon selection passed" << std::endl;
	    return true;
          } else {
     	    if (verbose) std::cout << " muon selection failed" << std::endl;
            return false;
          }

	}
      }

      return false;

    }

  private:

};

SoftMuonSelector::SoftMuonSelector(int nMuSelBins_, vector<double> jetPtEdge_, vector<double> muonPtCut_, vector<double> muonJetDRCut_, bool verbose_) {
  nMuSelBins   = nMuSelBins_;
  jetPtEdge    = jetPtEdge_;
  muonPtCut    = muonPtCut_;
  muonJetDRCut = muonJetDRCut_;
  verbose      = verbose_;
}

SoftMuonSelector::~SoftMuonSelector(){
}
 
#endif
