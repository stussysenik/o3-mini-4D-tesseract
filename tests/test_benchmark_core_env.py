from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import benchmark_core


class LocalEnvLoadingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_paths = benchmark_core.LOCAL_ENV_PATHS
        benchmark_core.local_env_values.cache_clear()
        for name in ("TB_TEST_ONLY", "TB_TEST_QUOTED"):
            os.environ.pop(name, None)

    def tearDown(self) -> None:
        benchmark_core.LOCAL_ENV_PATHS = self.original_paths
        benchmark_core.local_env_values.cache_clear()
        for name in ("TB_TEST_ONLY", "TB_TEST_QUOTED"):
            os.environ.pop(name, None)

    def test_env_local_overrides_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env_path = root / ".env"
            env_local_path = root / ".env.local"
            env_path.write_text("TB_TEST_ONLY=from-env\n", encoding="utf-8")
            env_local_path.write_text("TB_TEST_ONLY=from-env-local\n", encoding="utf-8")

            benchmark_core.LOCAL_ENV_PATHS = (env_local_path, env_path)
            benchmark_core.local_env_values.cache_clear()

            self.assertEqual(benchmark_core.read_env("TB_TEST_ONLY"), "from-env-local")

    def test_process_env_overrides_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env_local_path = root / ".env.local"
            env_local_path.write_text("TB_TEST_ONLY=from-env-local\n", encoding="utf-8")

            benchmark_core.LOCAL_ENV_PATHS = (env_local_path, root / ".env")
            benchmark_core.local_env_values.cache_clear()
            os.environ["TB_TEST_ONLY"] = "from-process"

            self.assertEqual(benchmark_core.read_env("TB_TEST_ONLY"), "from-process")

    def test_quoted_values_are_decoded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env_local_path = root / ".env.local"
            env_local_path.write_text('export TB_TEST_QUOTED="hello\\nworld"\n', encoding="utf-8")

            benchmark_core.LOCAL_ENV_PATHS = (env_local_path, root / ".env")
            benchmark_core.local_env_values.cache_clear()

            self.assertEqual(benchmark_core.read_env("TB_TEST_QUOTED"), "hello\nworld")


if __name__ == "__main__":
    unittest.main()
