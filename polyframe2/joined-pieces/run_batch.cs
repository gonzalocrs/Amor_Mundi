// run one batch of the joined-pieces GH component and bake it (called from the MCP with ROOT/START/COUNT replaced)
var doc = __rhino_doc__;
var gd = Grasshopper.Instances.ActiveCanvas.Document;
Func<string, Grasshopper.Kernel.IGH_DocumentObject> F = s => gd.FindObject(new Guid(s), true);
string ROOT = "__ROOT__"; double CX = __CX__, CY = __CY__; int START = __START__, COUNT = __COUNT__;
var root = (Grasshopper.Kernel.Special.GH_Panel)F("727dd383-a824-4131-a0c1-d0001d8d38e7"); root.UserText = ROOT; root.ExpireSolution(false);
((Grasshopper.Kernel.Special.GH_NumberSlider)F("2f008e84-63e7-4516-9833-2289e3477e27")).SetSliderValue((decimal)CX);
((Grasshopper.Kernel.Special.GH_NumberSlider)F("578c1938-8159-4a33-94eb-78ef6f680319")).SetSliderValue((decimal)CY);
((Grasshopper.Kernel.Special.GH_NumberSlider)F("00b0e194-f8d3-490a-9f3e-e7a14e764de0")).SetSliderValue(START);
((Grasshopper.Kernel.Special.GH_NumberSlider)F("b9e65027-155e-40cf-902a-25f9df47de7b")).SetSliderValue(COUNT);
var comp = (Grasshopper.Kernel.IGH_Component)F("85230f17-e1d0-4dd3-a4d1-33604e85b2a3");
comp.Locked = false; comp.ExpireSolution(false);
var sw = System.Diagnostics.Stopwatch.StartNew();
gd.NewSolution(false);
comp.Locked = true;
int li = doc.Layers.FindByFullPath(ROOT + "::printed pieces + rib (joined)", -1);
if (li < 0) { var L = new Rhino.DocObjects.Layer(); L.Name = "printed pieces + rib (joined)"; L.ParentLayerId = doc.Layers[doc.Layers.FindByFullPath(ROOT, -1)].Id; L.Color = System.Drawing.Color.FromArgb(236, 229, 214); li = doc.Layers.Add(L); }
var js = comp.Params.Output[1].VolatileData.AllData(true).ToList();
var ids = comp.Params.Output[2].VolatileData.AllData(true).ToList();
var st = comp.Params.Output[3].VolatileData.AllData(true).ToList();
int baked = 0;
for (int i = 0; i < js.Count; i++) {
  Rhino.Geometry.Brep b = null; js[i].CastTo<Rhino.Geometry.Brep>(out b); if (b == null) continue;
  var a = new Rhino.DocObjects.ObjectAttributes(); a.LayerIndex = li;
  string s = st[i].ToString(); a.Name = s.StartsWith("fail") ? "FAILED (" + s + ") - plain piece" : s;
  a.SetUserString("source_piece", ids[i].ToString()); a.SetUserString("join_status", s);
  doc.Objects.AddBrep(b, a); baked++;
}
doc.ClearUndoRecords(true);
var rep = comp.Params.Output[4].VolatileData.AllData(true).FirstOrDefault();
Console.WriteLine("t " + sw.Elapsed.TotalSeconds.ToString("F0") + " baked " + baked + " | " + (rep == null ? string.Join("|", comp.RuntimeMessages(Grasshopper.Kernel.GH_RuntimeMessageLevel.Error)) : rep.ToString()));
Console.WriteLine("mem " + (System.Diagnostics.Process.GetCurrentProcess().WorkingSet64 / 1e9).ToString("F1"));
