# Tests

This directory holds the repository's Python test suite.

## Coverage
- `test_benchmark_core_env.py`: `.env` and `.env.local` loading rules.
- `test_benchmark_execute.py`: request payloads, provenance helpers, response parsing, and cost normalization.
- `test_benchmark_execute_response_ingestion.py`: response ingestion and generated artifact materialization.
- `test_benchmark_showcase.py`: side-by-side comparison resolution, code diff behavior, and variant-aware showcase labeling.

## Run
```bash
python3 -m unittest discover -s tests -v
```

## Intent
- Keep regression coverage close to the CLI surfaces that mutate benchmark artifacts.
- Prefer fixture-driven tests for parsing and provenance rules.
- Treat generated JSON and showcase outputs as contract surfaces, not incidental byproducts.
