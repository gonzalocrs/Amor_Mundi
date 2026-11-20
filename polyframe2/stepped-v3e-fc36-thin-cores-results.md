# Thin rib cores in Fc 36: Karamba check (2026-11-20)

This check covers the thin-rib option. Methods A and B use the same rib; they differ only in how deep it sits in the printed piece.

- **Model:** the v3e Karamba models (`stepped-15x10-v3e-karamba.gh`, `stepped-10x10-v3e-karamba.gh`) with only the rib cores changed. Results are saved as `*-fc36.gh`.
- **Load cases:** LONG, W±X, W±Y, W45 (typhoon), LIVEX/Y, EQX/Y.
- **Allowable concrete compression, Fc 36 (AIJ):** 12 MPa long-term (LONG, LIVE) and 24 MPa short-term (wind, earthquake).
- **Stress:** σc = N/A + M/W on the core section.

## 15x10: cores D20 / D14 / D12 (were D22 / D16 / D12)

| band | worst long-term σc | utilisation | worst short-term σc | utilisation |
|---|---|---|---|---|
| bottom D20 | 10.1 MPa (LIVEY) | 84 % | 16.0 MPa (W-Y) | 67 % |
| middle D14 | 4.4 MPa (LIVEY) | 37 % | 8.7 MPa (W45) | 36 % |
| top D12 | 3.2 MPa (LIVE) | 27 % | 8.7 MPa (W45) | 36 % |

- **Displacement:** 5.4 mm under LONG and 16.6 mm under W+Y (15.6 mm horizontal).
- **2nd-order analysis (ThII):** 5.6 mm under LONG and 17.2 mm under W+Y.
- **Buckling:** the first buckling load factor is 42.1.
- **Columns:** N up to 138 kN and M up to 33.9 kNm, the same as before (the columns were not changed).

## 10x10: cores D16 / D12 / D12 (were D18 / D14 / D12)

| band | worst long-term σc | utilisation | worst short-term σc | utilisation |
|---|---|---|---|---|
| bottom D16 | 7.6 MPa (LIVE) | 63 % | 11.6 MPa (W45) | 48 % |
| middle D12 | 3.1 MPa (LIVE) | 26 % | 6.3 MPa (W45) | 26 % |
| top D12 | 2.5 MPa (LIVE) | 21 % | 6.6 MPa (W±) | 28 % |

- **Displacement:** 1.8 mm under LONG and 5.8 mm under wind.
- **2nd-order analysis (ThII):** 1.8 mm under LONG and 5.8 mm under wind.
- **Buckling:** the first buckling load factor is 88.1.

## Verdict

- No band has to go up a size.
- The governing member is the 15x10 bottom band, at 84 % long-term.
- The upper bands of both roofs are at 40 % or less, so they could go thinner later if wanted.
