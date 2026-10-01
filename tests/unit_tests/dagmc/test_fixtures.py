from pathlib import Path
import shutil


def test_legacy_path_is_canonical(dagmc_legacy_path):
    expected = (
        Path(__file__).resolve().parents[2]
        / 'regression_tests' / 'dagmc' / 'legacy' / 'dagmc.h5m'
    )
    assert dagmc_legacy_path == expected
    assert dagmc_legacy_path.is_file()


def test_legacy_path_from_tmpdir(run_in_tmpdir, dagmc_legacy_path):
    assert dagmc_legacy_path.is_absolute()
    assert dagmc_legacy_path.is_file()


def test_legacy_geometry_copy(run_in_tmpdir, dagmc_legacy_path):
    destination = Path('dagmc.h5m')
    shutil.copyfile(dagmc_legacy_path, destination)

    assert not destination.samefile(dagmc_legacy_path)
    assert destination.read_bytes() == dagmc_legacy_path.read_bytes()
