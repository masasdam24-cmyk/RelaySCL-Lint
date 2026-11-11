# RelaySCL-Lint

**Lightweight, offline checks for IEC 61850 SCL configurations with a focus on GOOSE.**

RelaySCL-Lint finds common configuration inconsistencies in `.scd`, `.cid`, `.icd`, and other SCL XML files, with readable diagnostic codes. It is intended for protection-and-control engineers, integrators, students, and open-source tooling workflows.

> **Scope:** This is **not** an IEC 61850 conformance certificate, complete SCL XSD validator, or network/GOOSE traffic analyzer. Passing checks does **not** prove interoperability or configuration correctness. Do not rely on this tool as the sole basis for safety-critical commissioning decisions.

## Features (v0.1.0)

- Standard-library-only Python 3.10+ CLI, no network access or third-party packages.
- Handles both namespace-qualified and namespace-free SCL XML.
- Checks GSEControl -> DataSet references within LN0; catches duplicate GSEControl and DataSet names.
- Checks `confRev` for positive-integer form.
- Correlates `Communication/ConnectedAP/GSE` entries to GSEControl entries (IED, AP, logical device, control-block name).
- Checks GOOSE multicast MAC-Address, APPID, VLAN-ID, and VLAN-PRIORITY formats.
- Emits text or JSON diagnostics suitable for CI; nonzero exit status for errors.
- Provides synthetic test examples and automated tests.

## Quick start

```bash
python relayscl_lint.py examples/valid.scd
python relayscl_lint.py examples/broken.scd
python relayscl_lint.py --format json examples/valid.scd
python relayscl_lint.py --strict your-file.cid
```

Exit status: `0` = no errors; `1` = error findings (or warnings with `--strict`). `--strict` does not treat informational notes as failures.

Run the automated tests:

```bash
python -m unittest discover -s tests -v
```

## What gets checked

| Diagnostics | Rule family |
|---|---|
| `SCL001`, `SCL010-011`, `XML001/003` | XML / root / IED structural checks |
| `GSE001-007` | GSEControl, DataSet references, duplicates, confRev |
| `COM001-014` | Communication mapping, address format, network fields |

Notes: A missing `Communication` section is **informational** (common in partial ICD files). Missing mappings are **informational** because some SCL documents are intentionally partial. The GSEControl `appID` attribute is a GOOSE identifier and is **not** automatically treated as equal to the network `APPID` value in a `P` element.

## Development roadmap

- v0.2: configurable severity levels and filtering, optional CSV/HTML report.
- v0.3: cross-file comparisons for configurations and clearer mapping diagnostics.
- v0.4: optional full XSD-based validation, when supporting schemas are available under suitable licenses.
- v1.0: documented CI integrations and real-world, permission-cleared test corpus.

## Privacy and security

- Files are processed locally; the program has **no telemetry**.
- No real IED configurations are included. Test fixtures are fictional.
- Do not commit confidential terminal configurations, passwords, network addresses, or customer data.
- XML input is capped at 20 MiB for a basic resource bound; treat untrusted files cautiously.

## Contributing

Bug reports, reproducible minimal **sanitized** SCL files, documentation improvements, and pull requests are welcome. Please include the exact diagnostic code and the expected result. Use the included examples as a starting point.

## License

MIT. See [LICENSE](LICENSE).
