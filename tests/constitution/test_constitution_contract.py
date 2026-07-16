import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "core" / "laws" / "CONSTITUTIONAL_REGISTRY.json"
LAWS = ROOT / "core" / "laws" / "KONOHA_LAWS.md"
AUTHORITY = ROOT / "docs" / "architecture" / "authority_and_role_boundaries.md"


class ConstitutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_single_supreme_repository_authority(self):
        self.assertEqual(
            self.registry["supreme_authority"],
            "core/laws/KONOHA_LAWS.md",
        )
        constitution_docs = [
            row for row in self.registry["documents"]
            if row["document_type"] == "constitution"
        ]
        self.assertEqual(len(constitution_docs), 1)
        self.assertEqual(constitution_docs[0]["authority_level"], 1)

    def test_every_registered_document_exists(self):
        for row in self.registry["documents"]:
            with self.subTest(path=row["path"]):
                self.assertTrue((ROOT / row["path"]).is_file())

    def test_role_policy_paths_exist(self):
        for row in self.registry["roles"]:
            policy_path = row["policy_path"]
            if policy_path is None:
                continue
            with self.subTest(role=row["role"]):
                self.assertTrue((ROOT / policy_path).is_file())

    def test_no_role_self_authorizes_or_self_approves(self):
        for row in self.registry["roles"]:
            with self.subTest(role=row["role"]):
                self.assertFalse(row["may_self_approve"])
                self.assertFalse(row["may_modify_own_policy"])

    def test_hokage_decides_but_does_not_execute(self):
        hokage = next(
            row for row in self.registry["roles"]
            if row["role"] == "hokage"
        )
        self.assertTrue(hokage["may_decide_strategy"])
        self.assertFalse(hokage["may_execute"])

    def test_workers_execute_but_do_not_decide_strategy(self):
        worker = next(
            row for row in self.registry["roles"]
            if row["role"] == "worker"
        )
        self.assertTrue(worker["may_execute"])
        self.assertFalse(worker["may_decide_strategy"])
        self.assertFalse(worker["may_review_own_work"])

    def test_shikamaru_cannot_approve_doctrine(self):
        shikamaru = next(
            row for row in self.registry["roles"]
            if row["role"] == "shikamaru"
        )
        self.assertFalse(shikamaru["may_approve_doctrine"])
        self.assertFalse(shikamaru["may_execute"])

    def test_providers_do_not_decide_strategy(self):
        for role in ("provider_adapter", "provider_model"):
            row = next(
                item for item in self.registry["roles"]
                if item["role"] == role
            )
            self.assertFalse(row["may_decide_strategy"])
            self.assertFalse(row["may_self_approve"])

    def test_constitutional_invariants_are_true(self):
        for name, value in self.registry["invariants"].items():
            with self.subTest(invariant=name):
                self.assertIs(value, True)

    def test_laws_1_through_23_exist_once(self):
        text = LAWS.read_text(encoding="utf-8")
        for number in range(1, 24):
            count = len(re.findall(
                rf"^## Law {number}:",
                text,
                flags=re.MULTILINE,
            ))
            self.assertEqual(count, 1, f"Law {number} count={count}")

    def test_authority_graph_declares_lower_layers_cannot_expand(self):
        text = AUTHORITY.read_text(encoding="utf-8").lower()
        self.assertIn(
            "a lower layer may restrict behavior further but may not expand authority",
            text,
        )


if __name__ == "__main__":
    unittest.main()
