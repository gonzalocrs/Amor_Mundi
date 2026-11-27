param($dir, $pattern = "karamba-model-*-raw.png")
# Crop each *-raw.png (transparent-background Rhino capture) to its opaque pixels and centre it on a white
# 3200 x 2000 sheet at ~90 % fill; writes the file without '-raw'. Run with Windows PowerShell 5 (powershell.exe).
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Drawing.Drawing2D; using System.Runtime.InteropServices;
public static class CropWhite2 { public static string Run(string src, string dst) {
  var b = new Bitmap(src); var r = new Rectangle(0,0,b.Width,b.Height);
  var d = b.LockBits(r, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
  int n = d.Stride*d.Height; var px = new byte[n]; Marshal.Copy(d.Scan0, px, 0, n); b.UnlockBits(d);
  int x0=b.Width, y0=b.Height, x1=0, y1=0;
  var cc = new int[b.Width]; var rr = new int[b.Height];
  for (int y=0;y<b.Height;y++) for (int x=0;x<b.Width;x++) if (px[y*d.Stride+4*x+3]>200) { cc[x]++; rr[y]++; }
  for (int x=0;x<b.Width;x++) if (cc[x]>25) { if(x<x0)x0=x; if(x>x1)x1=x; }
  for (int y=0;y<b.Height;y++) if (rr[y]>25) { if(y<y0)y0=y; if(y>y1)y1=y; }
  int cw=x1-x0+1, ch=y1-y0+1; double s=Math.Min(0.92*3200/cw, 0.90*2000/ch);
  var o = new Bitmap(3200,2000); using (var g = Graphics.FromImage(o)) { g.Clear(Color.White); g.InterpolationMode=InterpolationMode.HighQualityBicubic; g.SmoothingMode=SmoothingMode.HighQuality;
    float dw=(float)(cw*s), dh=(float)(ch*s); g.DrawImage(b, new RectangleF((3200-dw)/2,(2000-dh)/2,dw,dh), new RectangleF(x0,y0,cw,ch), GraphicsUnit.Pixel); }
  b.Dispose(); o.Save(dst, ImageFormat.Png); o.Dispose(); return cw+"x"+ch+" scale "+s.ToString("0.00"); } }
"@
Get-ChildItem (Join-Path $dir $pattern) | % { $o = $_.FullName -replace '-raw\.png$','.png'; "$($_.Name) " + [CropWhite2]::Run($_.FullName, $o) }
