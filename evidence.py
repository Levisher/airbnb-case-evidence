"""Shared helpers for every study: intervals, the results file each study writes, and one chart style."""
import csv, math, pathlib, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

NAVY, BLUE, RED, GREY, INK = '#1A2B4C', '#8FB4D9', '#B3261E', '#D0D0D0', '#333333'
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Aptos', 'Helvetica', 'Arial', 'DejaVu Sans'], 'font.size': 9,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#888888', 'axes.labelcolor': INK,
                     'xtick.color': INK, 'ytick.color': INK, 'axes.grid': False})


def wilson(k, n, z=1.96):
    """Wilson 95% interval for k successes in n trials, as shares."""
    if n == 0:
        return float('nan'), float('nan')
    p = k / n; d = 1 + z * z / n; c = (p + z * z / 2 / n) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / 4 / n / n) / d
    return c - h, c + h


def here(file):
    return pathlib.Path(file).resolve().parent


def save(file, results):
    """Write <script>_results.csv beside the script. reproduce.py compares it with figures.csv."""
    p = here(file) / (pathlib.Path(file).stem + '_results.csv')
    with open(p, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['figure_id', 'value'])
        for k, v in results.items():
            w.writerow([k, repr(round(float(v), 6))])
    for k, v in results.items():
        print(f'{k:42s} {float(v):,.4f}')


def titled(fig, title, subtitle=None):
    fig.text(0.02, 0.97, title, fontsize=13, fontweight='bold', color=NAVY, va='top', ha='left')
    if subtitle:
        fig.text(0.02, 0.905, subtitle, fontsize=9.5, color=INK, va='top', ha='left')


def callout(ax, text, x, y, ha='left', va='top', transform=None):
    ax.text(x, y, text, color=RED, fontsize=9.5, fontweight='bold', ha=ha, va=va, transform=transform or ax.transAxes, linespacing=1.25)


def finish(fig, file, name):
    fig.canvas.draw(); r = fig.canvas.get_renderer(); w = fig.get_window_extent().width
    for t in fig.texts:
        e = t.get_window_extent(r)
        if e.x1 > w * .985:
            t.set_fontsize(t.get_fontsize() * (w * .965) / e.x1)
    fig.savefig(here(file) / name, dpi=200)
    plt.close(fig)


def filing_lines():
    """Reads the one copy of filing_lines.csv at the repo root and returns a line lookup and the terms of the equation for one Airbnb period."""
    import pandas as pd
    L = pd.read_csv(pathlib.Path(__file__).resolve().parent / 'filing_lines.csv')
    g = lambda c, l, p: float(L[(L.company == c) & (L.line == l) & (L.period == p)].value.iloc[0])

    def terms(p):
        n, gbv, rev, cogs, ops, sbc, m, e = [g('Airbnb', k, p) for k in ('nights', 'gbv', 'rev', 'cogs', 'ops', 'sbc_ops', 'bp', 'ebitda')]
        v = cogs + ops - sbc
        return dict(N=n, G=gbv / n, t=rev / gbv, V=v / n, M=m, F=rev - v - m - e, E=e, rev=rev, gbv=gbv, v=v)
    return g, terms
