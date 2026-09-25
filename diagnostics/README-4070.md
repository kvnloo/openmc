# OpenMC #4070: native baseline diagnostic

AI-assisted test preparation. Production sources are unchanged from
`1d75981dbf3fd78962e516c12b550d034f2e7daa`.

The diagnostic creates synthetic, non-fissile one-group cross sections and runs
three small fixed-source problems at density multipliers 1, 0.5, and 2. It checks
`total = absorption + scatter` using scores from the same track-length tally.
These are not physical hydrogen data or a reactor design calculation. No
criticality, CAD/DAGMC, GPU, MPI, or external nuclear data are required.

Read `diagnostic-results/native/receipt.json`, not only the workflow color:
- `pass`: all three closure checks passed.
- `physics_assertion_failed`: the unit-density control passed but at least one
  changed-density case violated the closure relation.
- `native_not_run` or `probe_setup_or_execution_error`: environment/test failure,
  not a reproduction of the upstream issue.
Build failure before the receipt is produced is likewise infrastructure failure.

The code records every score and its flux-normalized value. There is no
production patch or expected-failure override. Native results were unavailable
when this branch was prepared; local Python syntax, YAML and shell syntax passed.
The blob uploaded for the native script exactly matches the syntax-checked local
file (Git blob `8a4e12162df2245a0b14a85f0636b9856ac9e9e8`).

This disposable branch replaces inherited workflows with one read-only CPU job
to avoid triggering unrelated integration or publishing jobs. It does not alter
the fork default branch or upstream. The job has a 20-minute limit and uploads
logs, resolved dependency versions, inputs, statepoints and the JSON receipt.

Sources:
- https://github.com/openmc-dev/openmc/issues/4070
- https://github.com/openmc-dev/openmc/blob/1d75981dbf3fd78962e516c12b550d034f2e7daa/src/tallies/tally_scoring.cpp
- https://github.com/openmc-dev/openmc/blob/1d75981dbf3fd78962e516c12b550d034f2e7daa/src/mgxs.cpp
- https://docs.openmc.org/en/stable/methods/tallies.html
