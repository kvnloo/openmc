from pathlib import Path

import openmc
import pytest


@pytest.fixture(scope='session')
def dagmc_legacy_path():
    """Path to the canonical legacy DAGMC regression geometry."""
    return (Path(__file__).resolve().parents[2]
            / 'regression_tests' / 'dagmc' / 'legacy' / 'dagmc.h5m')


@pytest.fixture
def dagmc_legacy_universe(dagmc_legacy_path):
    """Fresh DAGMCUniverse backed by the shared legacy test geometry."""
    return openmc.DAGMCUniverse(dagmc_legacy_path)
