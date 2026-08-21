import io
import unittest
from unittest.mock import patch
from tools.konoha_v4.conversation import classify_approval, _read_decision

class ApprovalProtocolTest(unittest.TestCase):
    def test_blank_never_rejects(self):
        for value in (None, "", " ", "\n", "\r\n", "\t"):
            self.assertEqual("pending", classify_approval(value))

    def test_explicit_approval(self):
        for value in ("sí", "si", "aprobar", "apruebo", "aprobado", "continuar", "yes"):
            self.assertEqual("approved", classify_approval(value))

    def test_explicit_rejection(self):
        for value in ("no", "rechazar", "rechazo", "cancelar", "stop", "detener"):
            self.assertEqual("rejected", classify_approval(value))

    def test_feedback_requests_changes(self):
        self.assertEqual(
            "changes_requested",
            classify_approval("reducí el presupuesto y quitá Teachback"),
        )

    def test_ambiguous_ok_stays_pending(self):
        # BLOCK_4 FINDING #17: protocols/approval/approval_policy.md lists
        # "ok" explicitly as ambiguous - it must neither approve the plan
        # nor be treated as free-form requested changes.
        self.assertEqual("pending", classify_approval("ok"))
        self.assertEqual("pending", classify_approval(" OK "))
        self.assertNotEqual("approved", classify_approval("ok"))
        self.assertNotEqual("changes_requested", classify_approval("ok"))

    def test_decision_reads_fresh_single_line(self):
        with patch("builtins.input", return_value="\r\n"):
            self.assertEqual("", _read_decision())

if __name__ == "__main__":
    unittest.main()
