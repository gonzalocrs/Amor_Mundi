# PolyFrame 2 session scripts

C# scripts run inside Rhino 8 through the Rhino MCP server (`run_csharp`), used to build and check the PolyFrame roof iterations in `polyframe2/`. They are working scripts, kept as a record of how each file was made.

- `mcp.py` sends a script to Rhino: `python mcp.py run_csharp <file.cs> <port> <timeout>`.
- `run.sh` + `pre.cs` + `inc.py` assemble a script from parts: `#gen` is replaced by `gen.cs`.
- `gen.cs` holds the force-diagram generators. `GenDiamond7` is the irregular-polygon version used for #14–#16, with feet at chosen positions along each side.
- `even_iter*.cs` + `it*.sh` run the even-load re-find for one diagram, one round per call.
- `build*.cs` build the slider-driven Grasshopper definitions.
- `kchain*.cs` / `kroof*.cs` run the Karamba check (C30/37, 150 x 250 ribs, 7 kN/m² on the pyramid surface).
- `addskin.cs`, `addlattice.cs`, `addcut.cs`, `addeave.cs`, `addsupport.cs`, `addstruts.cs`, `addflat.cs`, `atbase.cs` build the outer pyramid steps on #15 (skin → branches → cut → eaves → supported → struts → flat corners → at base).
- `print15*.cs` export the 1:50 / 1:100 STL print models.
- `review*.cs`, `bake*.cs` build the combined review `.3dm` files.
