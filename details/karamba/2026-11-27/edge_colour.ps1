param($dir, $pattern = "*-raw.png")
# Coloured facet edges for the Karamba BeamView captures (midterm page-04 look: coloured facets, coloured wireframe).
# Input per view: <name>-raw.png = shaded, mesh wires OFF; <name>-wire.png = same view, mesh wires ON in black.
# Wherever the wire pass is clearly darker than the shaded pass, the shaded colour is darkened by 25 %, so every
# facet edge takes the colour of its own face. Overwrites <name>-raw.png. Run with Windows PowerShell 5 (powershell.exe).
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class EdgeColour3 { public static int Run(string shaded, string wire) {
  var a = new Bitmap(shaded); var b = new Bitmap(wire); var r = new Rectangle(0,0,a.Width,a.Height);
  var da = a.LockBits(r, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb); var db = b.LockBits(r, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
  int n = da.Stride*da.Height; var pa = new byte[n]; var pb = new byte[n]; Marshal.Copy(da.Scan0, pa, 0, n); Marshal.Copy(db.Scan0, pb, 0, n);
  int c = 0;
  for (int i=0;i<n;i+=4) { if (pa[i+3] < 10) continue;
    int la = pa[i]+pa[i+1]+pa[i+2], lb = pb[i]+pb[i+1]+pb[i+2];
    if (la - lb > 90) { pa[i]=(byte)(pa[i]*0.75); pa[i+1]=(byte)(pa[i+1]*0.75); pa[i+2]=(byte)(pa[i+2]*0.75); c++; } }
  Marshal.Copy(pa, 0, da.Scan0, n); a.UnlockBits(da); b.UnlockBits(db); b.Dispose();
  string tmp = shaded + ".tmp.png"; a.Save(tmp, ImageFormat.Png); a.Dispose();
  System.IO.File.Delete(shaded); System.IO.File.Move(tmp, shaded); return c; } }
"@
Get-ChildItem (Join-Path $dir $pattern) | % { $w = $_.FullName -replace '-raw\.png$','-wire.png'; if (Test-Path $w) { "$($_.Name) edge px " + [EdgeColour3]::Run($_.FullName, $w) } }
