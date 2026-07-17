import io, unittest
from unittest.mock import patch
from tools.konoha_v4.conversation import _yes

class UXTest(unittest.TestCase):
    def test_natural_approval(self):
        for value in ("sí","si","ok","dale","aprobado"):
            self.assertTrue(_yes(value))
        self.assertFalse(_yes("quizás"))

if __name__ == "__main__":
    unittest.main()
