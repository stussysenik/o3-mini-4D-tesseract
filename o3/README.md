# o3 Track

This directory contains the `o3` benchmark track.

- `archive/o3-mini-4d-tesseract/`: untouched import of the original forked repository, preserved as the historical baseline.
- `runs/*.json`: timestamped run records created by `python benchmark_ledger.py create-run --model o3 ...`.

Use this track for the browser-native `o3` experiments that will target the shared WebGPU / WASM benchmark manifest.

