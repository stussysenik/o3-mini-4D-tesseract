.PHONY: test validate catalog readme showcase-index integrity

test:
	python3 -m unittest discover -s tests -v

catalog:
	python3 benchmark_admin.py build-catalog

readme:
	python3 benchmark_ledger.py build-readme

showcase-index:
	python3 benchmark_showcase.py build-index

preview-gpt54-medium:
	python3 benchmark_preview.py serve-result --result executions/results/gpt-5.4/20260401T204500Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium.json

validate:
	python3 benchmark_generate.py validate
	python3 benchmark_execute.py validate
	python3 benchmark_showcase.py validate
	python3 benchmark_admin.py build-catalog --check
	python3 benchmark_ledger.py build-readme --check
	python3 benchmark_ledger.py validate

integrity: test validate
