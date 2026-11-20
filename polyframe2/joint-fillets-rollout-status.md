# Joint fillets rollout: status (2026-11-20, COMPLETE at about 17:50)

**Done on both roofs (snapshot 177).**
- 15x10: 222 of 236 nodes are merged joints; 6 lost a branch and were left as separate pieces (nodes 21, 29, 82, 84, 85, 121); 8 free ends are halves. 547/1101 crotch fillets. 40/40 landings. 274 objects.
- 10x10: 122 of 132 merged; 10 left as separate pieces (nodes 33, 34, 38, 39, 42, 46, 47, 62, 63, 103). 236/564 crotch fillets. 32/32 landings. 178 objects.
- Coverage check: 0 missing tube quarter-points on either roof.
- Fillet layers are ON; plain pushed-in tube layers are OFF (cores unchanged); Bay test B is hidden (it overlaps). Main 3dm saved.

---
(History below.)

## What the rollout is
Option A ("joint fillets only") from snapshots 175–176, applied to every rib joint on both roofs. The ribs stay the plain pushed-in straight tubes, on the same axes and at the same sizes. At each joint:
- a ball of the tube radius closes the outside notch;
- a rolling-ball fillet goes in the inside corners only, sized by band:
  - 15x10: 4 cm on 28 cm tubes, 3 cm on 22 cm, 2.5 cm on 18 cm;
  - 10x10: 4 cm on 24 cm, 3 cm on 20 cm, 2.5 cm on 18 cm;
- an area-loss check (more than 3 %) rejects any fillet result that drops a branch. A rejected joint stays merged, with the ball but no crotch fillet ("square").

At the ring, the two feet of each V are cut flat at the ring top (z 2.80), merged with a local piece of the base ring, then filleted: first the tube-to-ring edges, then the crotch of the V.

## Where it stopped
- 15x10: 236 joint nodes in total (192 with 3 tubes, 20 with 4, 16 with 2, 8 ends), 368 tubes, 40 feet.
  - **Done: nodes 0–39** (40 nodes). 101 of 164 crotch edges filleted, 0 merge failures.
  - Baked to layer "Joint fillets (in progress)::15x10 ribs joint fillets" (40 objects, hidden).
  - **Left: nodes 40–235, then the ring landings (feet).**
- 10x10: 132 nodes, 212 tubes, 32 feet. **Not started.** Its layer "Joint fillets (in progress)::10x10 ribs joint fillets" exists and is empty.
- Node order is the order the tubes are read from the live "printed rib tubes - pushed in" layer. That order is stable as long as that layer isn't edited.

## How to resume
1. Script: `backup-2026-11-20-afternoon/joint_fillets_jf.py` (copied from /tmp/jf/jf.py on the Mac).
2. Read the tubes: `jf.extract(doc, "<roof> complete v3e-ring-step::printed rib tubes - pushed in (bottom 4 cm showing, same sizes)", 2.8)`, then `jf.cluster(recs, 2.8)`.
3. Set the fillet radii: `jf.RADMAP = {0.14: 0.04, 0.11: 0.03, 0.09: 0.025}` for 15x10, or `{0.12: 0.04, 0.10: 0.03, 0.09: 0.025}` for 10x10.
4. Joints: `jf.joints_range(recs, nodes, 0.14, i0, i1)` in batches of about 40 nodes (about 40–60 s each; Rhino MCP calls time out at 300 s).
5. Feet: `jf.foot(group, ring_piece, 0.04, 2.8)` for each group in `jf.foot_groups(recs, 2.8)`, one call per few groups. They're slow, about 60 s each.
6. Bake to the two layers. Check that every tube half is present: the quarter-point closest-point test returned 0 missing on the bay test. Then turn the fillet layers on and the plain pushed-in tube layers off (keep the cores layer as is).

## Layer tree (regrouped at the same time, reparenting only)
- 15x10 complete v3e-ring-step (live, unchanged, 12 sublayers)
- 10x10 complete v3e-ring-step (live, unchanged, 12 sublayers)
- Joint fillets (in progress): 15x10 ribs joint fillets, 10x10 ribs joint fillets, Bay tests A-B (A = joints only, B = plus thicker base)
- Rib studies 2026-11-20 (SubD etc., hidden): SubD Multipipe + B + B2, Method B fin, Drip tests (bay), SubD flowy, SubD branches G2, Feet + roots

Layer names were not changed, so older scripts that look layers up by name still find them. Full paths of the study layers now include their new parent group.

## Files
- The latest state of the model (regrouped layers, partial rollout, bay tests A/B, plain pushed-in ribs live) is saved in `backup-2026-11-20-afternoon/stepped-15x10-10x10-v3e-current.3dm`.
- `polyframe2/stepped-15x10-10x10-v3e-current.3dm` was saved at 16:13 on 2026-11-20 and holds the same state as the backup.

## Fix at 18:15: open pieces and crown domes
- Some fillets had left open holes in joint pieces, so the core showed through: 77 joints + 15 landings on the 15x10, and 58 joints + 11 landings on the 10x10. All were rebuilt with a solid-only rule: a fillet is kept only if the result is a closed solid (jf.py now checks IsSolid). Every rib piece on both roofs is now a closed solid. 0 tube quarter-points missing.
- The 8 cut rib ends at the 15x10 crown (nodes 221, 222, 225, 226, 229, 230, 233, 234) now have a full ball of the tube radius, unioned in. The 10x10 crown already had 16 full domes.
- The fillet layers moved into the roof groups as "ribs (final, joint fillets)". The "Joint fillets (in progress)" folder was removed, and Bay tests A-B moved into the Rib studies folder.
