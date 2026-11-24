"""capture the active viewport to a file (Arctic)"""
import Rhino, Rhino.Geometry as G, System


def snap(doc, path, cam, tgt, w=1400, h=1000, mode="Arctic", lens=24):
    v = doc.Views.ActiveView
    if v.ActiveViewport.IsParallelProjection:
        v.ActiveViewport.ChangeToPerspectiveProjection(True, lens)
    dm = Rhino.Display.DisplayModeDescription.FindByName(mode)
    if dm:
        v.ActiveViewport.DisplayMode = dm
    v.ActiveViewport.Camera35mmLensLength = lens
    v.ActiveViewport.SetCameraLocations(G.Point3d(*tgt), G.Point3d(*cam))
    v.Redraw()
    vc = Rhino.Display.ViewCapture(); vc.Width = w; vc.Height = h; vc.ScaleScreenItems = False; vc.DrawAxes = False; vc.DrawGrid = False
    bmp = vc.CaptureToBitmap(v)
    bmp.Save(path, System.Drawing.Imaging.ImageFormat.Png)
    return path
