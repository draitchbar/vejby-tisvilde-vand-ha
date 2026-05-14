"""Root conftest: install HA stubs and expose the integration as vejby_tisvilde_vand."""
# Tell pytest not to collect integration source files as test modules
collect_ignore = [
    "__init__.py", "api.py", "sensor.py", "config_flow.py",
    "const.py", "models.py", "date_ranges.py", "http_client.py",
]
import importlib.machinery
import importlib.util
import os
import sys
import types
from unittest.mock import MagicMock

root = os.path.dirname(os.path.dirname(__file__))  # project root (parent of tests/)
tests_dir = os.path.dirname(__file__)

# Add tests/ to sys.path so `from helpers import ...` works in test files
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

# ---------------------------------------------------------------------------
# 1. Install HA + external stubs BEFORE any integration module is imported
# ---------------------------------------------------------------------------
# Proper stub base classes so multi-inheritance works
class _DataUpdateCoordinator:
    def __init__(self, *a, **kw): pass
    def __class_getitem__(cls, item): return cls

class _CoordinatorEntity:
    def __init__(self, coordinator, *a, **kw):
        self.coordinator = coordinator
    def __class_getitem__(cls, item): return cls

class _SensorEntity:
    pass

class _UpdateFailed(Exception):
    pass

_coord_stub = types.ModuleType("homeassistant.helpers.update_coordinator")
_coord_stub.DataUpdateCoordinator = _DataUpdateCoordinator
_coord_stub.CoordinatorEntity = _CoordinatorEntity
_coord_stub.UpdateFailed = _UpdateFailed

_sensor_stub = types.ModuleType("homeassistant.components.sensor")
_sensor_stub.SensorEntity = _SensorEntity
_sensor_stub.SensorDeviceClass = MagicMock()
_sensor_stub.SensorStateClass = MagicMock()

_ha = MagicMock()

for mod, stub in [
    ("homeassistant.helpers.update_coordinator", _coord_stub),
    ("homeassistant.components.sensor", _sensor_stub),
]:
    sys.modules.setdefault(mod, stub)

_dt_util_stub = types.ModuleType("homeassistant.util.dt")
_dt_util_stub.now = MagicMock()
_dt_util_stub.start_of_local_day = MagicMock()

_util_stub = types.ModuleType("homeassistant.util")
_util_stub.dt = _dt_util_stub

sys.modules.setdefault("homeassistant.util", _util_stub)
sys.modules.setdefault("homeassistant.util.dt", _dt_util_stub)

for mod in [
    "homeassistant",
    "homeassistant.helpers",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.components",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.aiohttp_client",
]:
    sys.modules.setdefault(mod, _ha)

sys.modules.setdefault("async_timeout", MagicMock())
sys.modules.setdefault("aiohttp", MagicMock())
sys.modules.setdefault("voluptuous", MagicMock())

# ---------------------------------------------------------------------------
# 2. Register and load the integration as the vejby_tisvilde_vand package
# ---------------------------------------------------------------------------
PKG = "vejby_tisvilde_vand"


def _load_submodule(name: str, filename: str):
    """Load a .py file as vejby_tisvilde_vand.<name>."""
    full_name = f"{PKG}.{name}"
    if full_name in sys.modules:
        return sys.modules[full_name]
    loader = importlib.machinery.SourceFileLoader(full_name, os.path.join(root, filename))
    spec = importlib.util.spec_from_loader(full_name, loader)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = PKG
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Create the package stub first (needed so relative imports inside modules resolve)
if PKG not in sys.modules:
    pkg = types.ModuleType(PKG)
    pkg.__path__ = [root]
    pkg.__package__ = PKG
    sys.modules[PKG] = pkg

# Load leaf modules that have no intra-package dependencies first
_load_submodule("const", "const.py")
_load_submodule("models", "models.py")
_load_submodule("date_ranges", "date_ranges.py")
_load_submodule("http_client", "http_client.py")
_load_submodule("api", "api.py")

# Load __init__.py last (depends on api, models, etc.)
_init_loader = importlib.machinery.SourceFileLoader(PKG, os.path.join(root, "__init__.py"))
_init_spec = importlib.util.spec_from_loader(PKG, _init_loader)
_init_mod = importlib.util.module_from_spec(_init_spec)
_init_mod.__path__ = [root]
_init_mod.__package__ = PKG
sys.modules[PKG] = _init_mod
_init_spec.loader.exec_module(_init_mod)

# Load sensor after __init__ (it does `from . import VejbyTisvildeVandDataUpdateCoordinator`)
_load_submodule("sensor", "sensor.py")

# NOTE: we intentionally do NOT add root to sys.path to prevent pytest from
# treating the root (which has __init__.py) as a collectible package.
