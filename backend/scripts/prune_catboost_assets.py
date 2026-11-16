"""
FairGig AI — Vercel Bundle Pruner

Previously this script removed unused scipy/pandas sub-modules to shrink the
CatBoost bundle.  As of the current deployment, CatBoost is replaced by a
pure-Python inference artifact (models/cat_model_python.py) so scipy and
pandas are no longer installed at all.  The script is kept as a no-op
placeholder so the vercel.json installCommand doesn't need to change if
future pruning is ever required.
"""


def main():
    print("FairGig AI bundle pruner: no pruning required (catboost not installed).")


if __name__ == "__main__":
    main()
