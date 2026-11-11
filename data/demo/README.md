# Synthetic demonstration data

All demo schemes, AMC names, benchmark indices and NAV/return histories are fictional.
`services/demo_data.py` uses NumPy seed 20261111 to generate 24 schemes in Equity, Hybrid
and Debt and three Total Return Index series. The fixed end date is 30 Oct 2026.

The generator includes strong/weak benchmark-relative behaviour, active/passive tracking
differences, a synthetic stress episode, inconsistent returns, an intentionally short-history
fund and an intentionally incomplete-history fund. These do not reconstruct real performance.
Optional expense ratios and AUM are unavailable, rather than invented.

The demo database is generated on first launch and is excluded from Git. To export all
synthetic observations and calculated research tables, run `python -m scripts.export_demo`.
The demo and uploaded datasets use different databases and cannot silently replace each other.
