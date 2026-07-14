import os
import unittest
from unittest.mock import patch

from tools.hokage_orchestrator.run_conversational_hokage import (
    build_parser,
)


class SelectedLocalModelContractTests(unittest.TestCase):
    def test_environment_selects_canonical_shell_model(self):
        with patch.dict(
            os.environ,
            {"KONOHA_LOCAL_MODEL": "qwen2.5-coder:3b"},
            clear=False,
        ):
            args = build_parser().parse_args([])
        self.assertEqual(
            args.local_model,
            "qwen2.5-coder:3b",
        )

    def test_explicit_argument_overrides_environment(self):
        with patch.dict(
            os.environ,
            {"KONOHA_LOCAL_MODEL": "qwen2.5-coder:3b"},
            clear=False,
        ):
            args = build_parser().parse_args(
                ["--local-model", "llama3.2:3b"]
            )
        self.assertEqual(
            args.local_model,
            "llama3.2:3b",
        )


if __name__ == "__main__":
    unittest.main()
