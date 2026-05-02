import importlib.util
from pathlib import Path

from src.circuits.ieee30 import CONFIG as CONFIG_30BUS


def _load_circuit(filename: str):
    path = Path(__file__).parent / "circuits" / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CONFIG


CONFIGS = {
    "4bus":  _load_circuit("4bus.py"),
    "ieee30": CONFIG_30BUS,
}
