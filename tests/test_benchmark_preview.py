from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from benchmark_core import ROOT, relative_path
from benchmark_preview import (
    preview_url,
    resolve_result_generated_root,
    resolve_showcase_root,
)


class PreviewResolutionTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def test_resolve_result_generated_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_root = Path(temp_dir)
            generated_root = temp_root / "executions" / "output" / "alpha" / "run-1" / "generated"
            generated_root.mkdir(parents=True, exist_ok=True)
            (generated_root / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
            result_path = temp_root / "executions" / "results" / "alpha" / "run-1.json"
            self._write_json(
                result_path,
                {
                    "result_id": "alpha--run-1",
                    "output_root": relative_path(generated_root.parent),
                },
            )

            resolved = resolve_result_generated_root(relative_path(result_path))

            self.assertEqual(resolved, generated_root)

    def test_resolve_showcase_root_from_comparison(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_root = Path(temp_dir)
            site_root = temp_root / "showcase" / "site" / "comparison-1"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
            comparison_path = temp_root / "showcase" / "comparisons" / "comparison-1.json"
            self._write_json(
                comparison_path,
                {
                    "comparison_id": "comparison--20260401T000000Z--comparison-1",
                    "site_root": relative_path(site_root),
                },
            )

            resolved = resolve_showcase_root(relative_path(comparison_path))

            self.assertEqual(resolved, site_root)

    def test_preview_url_normalizes_wildcard_host(self) -> None:
        self.assertEqual(preview_url("0.0.0.0", 4173), "http://127.0.0.1:4173/")


if __name__ == "__main__":
    unittest.main()
