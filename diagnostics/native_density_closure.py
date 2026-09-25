"""AI-assisted native regression probe for openmc-dev/openmc#4070.

Run from a source-built OpenMC environment at
1d75981dbf3fd78962e516c12b550d034f2e7daa.
Synthetic non-fissile, one-group data: NOT physical hydrogen cross sections.
No external nuclear-data download, CAD/DAGMC, GPU, or criticality calculation.
A failing physics assertion is not interchangeable with a setup/build failure.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import traceback

import h5py


def run_case(openmc, root: Path, density: float) -> dict:
    directory = root / f'density_{density:g}'
    directory.mkdir(parents=True, exist_ok=True)
    openmc.reset_auto_ids()
    groups = openmc.mgxs.EnergyGroups([0., 20.e6])
    xs = openmc.XSdata('H1', groups)
    # Synthetic microscopic data, not physical H1 nuclear data. A unit
    # number density below gives unit base macroscopic total cross section.
    xs.atomic_weight_ratio = 1.0
    xs.order = 0
    xs.set_total([1.0])
    xs.set_absorption([0.5])
    xs.set_scatter_matrix([[[0.5]]])
    library = openmc.MGXSLibrary(groups)
    library.add_xsdata(xs)
    data_path = directory / 'synthetic_mgxs.h5'
    library.export_to_hdf5(data_path)

    material = openmc.Material(name='synthetic_nonfissile')
    material.add_nuclide('H1', 1.0)
    material.set_density('atom/b-cm', 1.0)
    materials = openmc.Materials([material])
    materials.cross_sections = str(data_path)
    sphere = openmc.Sphere(r=5., boundary_type='vacuum')
    cell = openmc.Cell(fill=material, region=-sphere)
    # At this source pin, MG density_gpcc() returns number density. Match
    # that denominator explicitly; do not label this input as g/cm3.
    cell.density = density

    settings = openmc.Settings()
    settings.energy_mode = 'multi-group'
    settings.run_mode = 'fixed source'
    settings.batches = 4
    settings.particles = 250
    settings.seed = 5234070
    settings.temperature = {'default': 294.0}
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Point((0., 0., 0.)),
        energy=openmc.stats.Discrete([1.e6], [1.0]),
    )
    tally = openmc.Tally(name='density_closure')
    tally.filters = [openmc.CellFilter(cell)]
    tally.estimator = 'tracklength'
    tally.scores = ['flux', 'total', 'absorption', 'scatter', 'nu-scatter']
    model = openmc.Model(openmc.Geometry([cell]), materials, settings,
                         openmc.Tallies([tally]))
    statepoint = model.run(cwd=directory, output=False, threads=1)
    with h5py.File(directory / 'summary.h5') as summary:
        base_number_density = float(
            summary[f'materials/material {material.id}/atom_density'][()]
        )
    native_multiplier = density / base_number_density
    if not math.isclose(base_number_density, 1.0, rel_tol=1.e-12):
        raise RuntimeError(f'Native base number density is not unity: {base_number_density}')
    if not math.isclose(native_multiplier, density, rel_tol=1.e-12):
        raise RuntimeError(f'Native multiplier differs from intended input: {native_multiplier}')
    with openmc.StatePoint(statepoint) as sp:
        result = sp.get_tally(name='density_closure')
        values = {score: float(result.get_values(scores=[score]).ravel()[0])
                  for score in tally.scores}
    if not all(math.isfinite(v) and v > 0. for v in values.values()):
        raise RuntimeError(f'Invalid probe setup or empty tally: {values}')
    sigma = {score: values[score]/values['flux'] for score in tally.scores if score != 'flux'}
    closure_error = abs(sigma['total']-sigma['absorption']-sigma['scatter'])/sigma['total']
    return {'cell_density_input': density,
            'base_number_density_atom_b_cm': base_number_density,
            'density_multiplier': native_multiplier,
            'means': values, 'scores_per_flux': sigma,
            'relative_closure_error': closure_error,
            'closure_passed': closure_error < 1.e-10}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else 'openmc-4070-results').resolve()
    root.mkdir(parents=True, exist_ok=True)
    receipt = {'source_pin': '1d75981dbf3fd78962e516c12b550d034f2e7daa',
               'status': 'not_started', 'cases': []}
    try:
        import openmc
        receipt['openmc_version'] = openmc.__version__
        receipt['openmc_module'] = openmc.__file__
        for density in (1.0, 0.5, 2.0):
            case = run_case(openmc, root, density)
            receipt['cases'].append(case)
            print(json.dumps(case), flush=True)
        if not receipt['cases'][0]['closure_passed']:
            raise RuntimeError('Unit-density control failed; not a clean #4070 reproduction')
        receipt['status'] = ('pass' if all(c['closure_passed'] for c in receipt['cases'])
                             else 'physics_assertion_failed')
        code = 0 if receipt['status'] == 'pass' else 1
    except ImportError as exc:
        receipt.update(status='native_not_run', error=str(exc))
        code = 2
    except Exception as exc:
        receipt.update(status='probe_setup_or_execution_error', error=str(exc),
                       traceback=traceback.format_exc())
        code = 2
    (root/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2), flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
