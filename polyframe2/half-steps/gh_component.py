"""Half-steps printed courses (stepped roof v3e).
Each old course of division B is split into `split` courses. Inner face, base ring step,
top course (crown-ring U formwork), crown ring, ribs and columns are unchanged.
Lower half keeps the old outer face; upper half steps in by half the old step.
Generator: polyframe2/half-steps/half_steps_gen.py; samples: half-steps-course-samples.json."""
import sys, importlib
import Grasshopper
P = r'C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\half-steps'
if P not in sys.path:
    sys.path.append(P)


class MyComponent(Grasshopper.Kernel.GH_ScriptInstance):
    def RunScript(self, roof: str, split: int, piece_len: float, wall: float, groove_w: float, groove_d: float):
        import importlib.util
        spec = importlib.util.spec_from_file_location('half_steps_gen', P + r'\half_steps_gen.py')
        H = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(H)
        S = H.load(r'C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\half-steps-course-samples.json')
        R = S[str(roof).strip()]
        prm = dict(H.DEFAULTS)
        prm.update({'piece_len': piece_len, 'wall': wall, 'lid': wall, 'end_wall': wall,
                    'groove_w': groove_w, 'groove_d': groove_d})
        cs = H.new_courses(S, str(roof).strip(), int(round(split)))
        pieces, course, lines = [], [], []
        for j, cc in enumerate(cs):
            pc, info = H.build_course(cc, R['cx'], R['cy'], j, prm)
            pieces += pc
            course += [j] * len(pc)
            lines.append('course %2d  z %.3f-%.3f  h %.1f cm  pieces %d  fails %d' % (
                j + 1, info['z0'], info['z1'], 100 * (info['z1'] - info['z0']), info['n'], info['fails']))
        lines.append('total printed pieces %d in %d courses (+ top U course unchanged)' % (len(pieces), len(cs)))
        return pieces, course, '\n'.join(lines)
