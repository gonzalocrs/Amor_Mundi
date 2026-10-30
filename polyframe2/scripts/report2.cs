void Tap(IGH_Component src,string outName,string tag){
 var e=Add("Explode PFoam"); W(src,outName,e,"PFoam"); e.NickName="X_"+tag;
 var ie=Add("Inspect PFEdge"); W(e,"PFEdges",ie,"PFEdge"); ie.NickName="E_"+tag;
 var iv2=Add("Inspect PFVertex"); W(e,"PFVertices",iv2,"PFVertex"); iv2.NickName="V_"+tag;
}
