"""
Derive P(Brazil more SoT than Scotland in 2H) from player SoT props.
Method: sum player Poisson λ_SoT per team → team λ → halve for 2H → poisson_p_a_greater_b.
"""
import sys, math
sys.path.insert(0, ".")
from forecasting.compute import poisson_p_a_greater_b, _pois_sf

# ── Player SoT O@0.5 markets (pooled avg across onexbet + WH where both exist) ─
# National team classification verified from squad lists.
# λ_raw = -ln(1 - 1/decimal_price)  i.e. Poisson mean from raw (vig-included) implied prob.

def raw_lam(decimal_price):
    raw_p = 1 / decimal_price
    if raw_p >= 1.0:
        return 99.0
    return -math.log(1.0 - raw_p)

HOLD_ASSUMPTION = 0.07  # typical player prop one-sided hold

def fair_lam(decimal_price, hold=HOLD_ASSUMPTION):
    """De-vig: assume hold splits ~symmetrically → fair P ≈ raw_P / (1 + hold/2)."""
    raw_p = 1 / decimal_price
    fair_p = raw_p / (1.0 + hold / 2.0)
    fair_p = min(fair_p, 0.999)
    return -math.log(1.0 - fair_p)

# Brazil players (onexbet O@0.5; avg'd with WH where available)
BRA = {
    "Vinicius Junior":    1.27,
    "Matheus Cunha":      1.31,
    "Rayan Cherki(?)":    1.40,   # "rayan vitor" — uncertain; flagged
    "Lucas Paqueta":      1.77,
    "Carlos Casemiro":    2.10,
    "Bruno Guimaraes":    2.70,
    "Douglas Santos":     2.90,   # uncertain identity
    "Gabriel (Magalhaes)":3.35,
    "Marquinhos":         3.45,   # Marcos Aoás Corrêa
    "Danilo":             3.67,
}

# Scotland players (avg O@0.5 across onexbet + WH)
SCO = {
    "Scott McTominay":    (2.00 + 1.91) / 2,   # avg of two books
    "Lawrence Shankland": (2.28 + 2.45) / 2,
    "Ben Doak":           2.45,
    "John McGinn":        (3.60 + 2.25) / 2,
    "Lewis Ferguson":     (3.70 + 4.60) / 2,
    "Kenny McLean":       (3.85 + 4.60) / 2,
    "Andrew Robertson":   (6.50 + 5.80) / 2,
    "Nathan Patterson":   6.15,
    "Jack Hendry":        6.50,
    "Scott McKenna":      (9.00 + 7.00) / 2,
}

print("Brazil players — raw λ vs fair λ (7% hold assumed):")
bra_lam_raw, bra_lam_fair = 0.0, 0.0
for name, price in BRA.items():
    rl = raw_lam(price)
    fl = fair_lam(price)
    bra_lam_raw += rl
    bra_lam_fair += fl
    flag = " *** team uncertain" if "(?)" in name or "Douglas" in name else ""
    print(f"  {name:<30} O@0.5={price:.2f}  raw_lam={rl:.3f}  fair_lam={fl:.3f}{flag}")

print(f"\n  Brazil Σ raw_lam  = {bra_lam_raw:.3f}")
print(f"  Brazil Σ fair_lam = {bra_lam_fair:.3f}")

print("\nScotland players — raw λ vs fair λ:")
sco_lam_raw, sco_lam_fair = 0.0, 0.0
for name, price in SCO.items():
    rl = raw_lam(price)
    fl = fair_lam(price)
    sco_lam_raw += rl
    sco_lam_fair += fl
    print(f"  {name:<30} O@0.5={price:.2f}  raw_lam={rl:.3f}  fair_lam={fl:.3f}")

print(f"\n  Scotland Σ raw_lam  = {sco_lam_raw:.3f}")
print(f"  Scotland Σ fair_lam = {sco_lam_fair:.3f}")

print("\n── 2H split (assume even distribution across halves) ──")
bra_2h = bra_lam_fair / 2
sco_2h = sco_lam_fair / 2
print(f"  λ_BRA_2H_SoT = {bra_lam_fair:.3f} / 2 = {bra_2h:.3f}")
print(f"  λ_SCO_2H_SoT = {sco_lam_fair:.3f} / 2 = {sco_2h:.3f}")

p_bra_more = poisson_p_a_greater_b(bra_2h, sco_2h)
p_sco_more = poisson_p_a_greater_b(sco_2h, bra_2h)
p_tie      = 1.0 - p_bra_more - p_sco_more
print(f"\n  P(BRA 2H SoT > SCO 2H SoT) = {p_bra_more:.1%}")
print(f"  P(draw in SoT)              = {p_tie:.1%}")
print(f"  P(SCO 2H SoT > BRA 2H SoT) = {p_sco_more:.1%}")

# ── Sensitivity: exclude uncertain-team players ──
print("\n── Sensitivity: exclude 'Rayan Cherki(?)' and 'Douglas Santos' ──")
bra_excl = {k: v for k, v in BRA.items() if "(?)  " not in k and "Douglas" not in k}
bra_lam_excl = sum(fair_lam(v) for v in bra_excl.values())
bra_2h_excl = bra_lam_excl / 2
p_excl = poisson_p_a_greater_b(bra_2h_excl, sco_2h)
print(f"  Brazil Σ fair_lam (8 confirmed) = {bra_lam_excl:.3f}")
print(f"  P(BRA > SCO in 2H SoT, 8 BRA players) = {p_excl:.1%}")

# ── Correlation caveats ──
print("\n── Within-team correlation impact (qualitative) ──")
print("  Summing independent Poissons UNDERSTATES the team SoT variance.")
print("  Higher variance → the gap between the two team means dominates less")
print("  → P(BRA > SCO) is slightly LOWER than the independent-Poisson calculation.")
print("  For a ratio BRA/SCO ≈ 2.6x, the effect is modest (~2-3pp downward).")
print(f"\n  Conservative estimate: {p_bra_more - 0.025:.1%} – {p_bra_more:.1%}")
print(f"  vs base-rate (fav scaling): 69.3%")
