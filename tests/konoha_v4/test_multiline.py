import io, unittest
from unittest.mock import patch
from tools.konoha_v4.conversation import _yes

class UXTest(unittest.TestCase):
    def test_natural_approval(self):
        for value in ("sí","si","dale","aprobado"):
            self.assertTrue(_yes(value))
        self.assertFalse(_yes("quizás"))

    def test_ambiguous_ok_is_not_approval(self):
        # BLOCK_4 FINDING #17: "ok" is explicitly ambiguous per
        # protocols/approval/approval_policy.md - it must not satisfy _yes().
        self.assertFalse(_yes("ok"))

if __name__ == "__main__":
    unittest.main()
