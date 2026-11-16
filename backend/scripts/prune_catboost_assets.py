import importlib.util
import sys
from pathlib import Path
from shutil import rmtree


def main():
    scipy_spec = importlib.util.find_spec("scipy")
    if scipy_spec is None or scipy_spec.origin is None:
        raise RuntimeError("SciPy must be installed before pruning its unused modules")

    pandas_spec = importlib.util.find_spec("pandas")
    if pandas_spec is None or pandas_spec.origin is None:
        raise RuntimeError("Pandas must be installed before pruning its unused tests")

    pandas_tests = Path(pandas_spec.origin).parent / "tests"
    if pandas_tests.is_dir():
        rmtree(pandas_tests)

    scipy_root = Path(scipy_spec.origin).parent
    # CatBoost inference needs scipy.sparse; the other top-level namespaces
    # are not imported by the backend runtime.
    for package in (
        "cluster",
        "constants",
        "datasets",
        "differentiate",
        "fft",
        "fftpack",
        "integrate",
        "interpolate",
        "io",
        "linalg",
        "misc",
        "ndimage",
        "odr",
        "optimize",
        "signal",
        "spatial",
        "special",
        "stats",
    ):
        package_path = scipy_root / package
        if package_path.is_dir():
            rmtree(package_path)

    jupyter_root = Path(sys.prefix) / "share" / "jupyter"
    for extension in ("nbextensions", "labextensions"):
        widget = jupyter_root / extension / "catboost-widget"
        if widget.is_dir():
            rmtree(widget)


if __name__ == "__main__":
    main()
