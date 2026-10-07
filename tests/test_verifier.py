"""The verifier must not report success for an exercise it never ran."""

import subprocess
import os
import socket
import unittest
from pathlib import Path


class VerifierCLITests(unittest.TestCase):
    def test_unknown_selector_fails_before_contacting_lab(self):
        script = Path(__file__).resolve().parents[1] / "verify.sh"
        result = subprocess.run([str(script), "unknown"], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)
        self.assertNotIn("failed=0", result.stdout)

    def test_valid_selector_fails_when_lab_is_unreachable(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            base = "http://127.0.0.1:%s" % sock.getsockname()[1]
            script = Path(__file__).resolve().parents[1] / "verify.sh"
            result = subprocess.run(["bash", str(script), "1"],
                                    env=dict(os.environ, V=base),
                                    capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAILED", result.stderr)

    def test_manual_activities_and_extra_arguments_are_rejected(self):
        script = Path(__file__).resolve().parents[1] / "verify.sh"
        for args in (("8",), ("10",), ("1", "2")):
            with self.subTest(args=args):
                result = subprocess.run(["bash", str(script), *args],
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Usage:", result.stderr)
