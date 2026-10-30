using Grasshopper; using Grasshopper.Kernel; using System.Drawing;
var canvas=Instances.ActiveCanvas; var doc=canvas.Document;
var bb=RectangleF.Empty; foreach(var o in doc.Objects){ var b=o.Attributes.Bounds; bb = bb.IsEmpty? b : RectangleF.Union(bb,b);} bb.Inflate(30,30);
var vp=new Grasshopper.GUI.Canvas.GH_Viewport(canvas.Viewport);
vp.Width=(int)bb.Width; vp.Height=(int)bb.Height; vp.Zoom=1f; vp.Tx=(int)(-bb.X); vp.Ty=(int)(-bb.Y);
var img=canvas.GenerateHiResImageTile(vp, Color.White);
img.Save(@"__P__", System.Drawing.Imaging.ImageFormat.Png);
Console.WriteLine("saved "+img.Width+"x"+img.Height+" bb "+bb);
