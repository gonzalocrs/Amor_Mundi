"""Half-steps rings: base ring step and crown course in the 0.25 m rhythm.
Each ring face is split into two half-height bands; the upper band steps in by half a step.
Printed U formwork (3 cm walls, 3 cm lid over the step) in ~1.2 m pieces; cast core follows
the stepped face (same top and bottom levels as now). Generator: half_steps_gen.build_ring."""
import importlib.util
import Grasshopper
P = r'C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\half-steps'


class MyComponent(Grasshopper.Kernel.GH_ScriptInstance):
    def RunScript(self, roof: str, piece_len: float, wall: float):
        spec = importlib.util.spec_from_file_location('half_steps_gen', P + r'\half_steps_gen.py')
        H = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(H)
        S = H.load(r'C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\half-steps-course-samples.json')
        prm = dict(H.DEFAULTS)
        prm.update({'piece_len': piece_len, 'wall': wall})
        roof = str(roof).strip()
        bp, bc, bi = H.build_ring(S, roof, 'base', prm)
        cp, cc, ci = H.build_ring(S, roof, 'crown', prm)
        rep = []
        for nm, i, p in (('base ring step', bi, bp), ('crown course', ci, cp)):
            rep.append('%s: z %.3f / %.3f / %.3f, %d formwork pieces (%d fails), cast solid %s, cast avg section %.4f m2' % (
                nm, i['z0'], i['zs'], i['z1'], len(p), i['fails'], i['cast_ok'], i['cast_area_avg']))
        return bp, [bc], cp, [cc], '\n'.join(rep)
