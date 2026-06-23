"""Q4: P(Austria more corners than Argentina) from team-total corner ladders."""
import sys
sys.path.insert(0, ".")
from forecasting import compute as c

def am_to_prob(o):
    o = float(o)
    return 100.0/(o+100.0) if o > 0 else (-o)/(-o+100.0)

# Home (Argentina) total corners ladder: line -> (over_american, under_american)
arg = {
    2.5: (-850, 490),
    3.5: (-320, 225),
    4.5: (-144, 108),
    5.5: (122, -166),
    6.5: (230, -330),
    7.5: (400, -650),
    8.5: (600, -1300),
}
# Away (Austria) total corners ladder
aut = {
    2.5: (-180, 132),
    3.5: (130, -176),
    4.5: (290, -430),
    5.5: (540, -1100),
    6.5: (890, -3000),
}

def devig_ladder(ladder):
    lines, povers = [], []
    for line, (ov, un) in ladder.items():
        po = c.devig_two_way(am_to_prob(ov), am_to_prob(un))
        lines.append(int(line))   # P(>= ceil) ~ P(over line) since line is .5
        povers.append(po)
    return lines, povers

arg_lines, arg_p = devig_ladder(arg)
aut_lines, aut_p = devig_ladder(aut)

# thresholds: over X.5 == P(>= X+1)
arg_thr = [l+1 for l in arg_lines]
aut_thr = [l+1 for l in aut_lines]

mu_arg = c.fit_poisson_mean_from_ladder(arg_thr, arg_p)
mu_aut = c.fit_poisson_mean_from_ladder(aut_thr, aut_p)

print("Argentina corner ladder (de-vigged P over):")
for line, p in zip(arg.keys(), arg_p):
    print(f"  over {line}: {p:.3f}")
print(f"  -> fitted Poisson mean: {mu_arg:.2f}")

print("\nAustria corner ladder (de-vigged P over):")
for line, p in zip(aut.keys(), aut_p):
    print(f"  over {line}: {p:.3f}")
print(f"  -> fitted Poisson mean: {mu_aut:.2f}")

p_aut_more = c.poisson_p_a_greater_b(mu_aut, mu_arg)
p_arg_more = c.poisson_p_a_greater_b(mu_arg, mu_aut)
p_tie = 1 - p_aut_more - p_arg_more
print(f"\nP(Austria more corners) = {p_aut_more:.3f} ({p_aut_more*100:.0f}%)")
print(f"P(Argentina more corners) = {p_arg_more:.3f} ({p_arg_more*100:.0f}%)")
print(f"P(equal corners) = {p_tie:.3f}")

# Cross-check vs "Most Corners in Each Half" market: ARG +165, AUT +1100
# (each-half, not full match, but directional sanity)
print("\nCross-check 'Most Corners in Each Half': ARG +165 (38%), AUT +1100 (8%) -> ARG dominates, consistent")
