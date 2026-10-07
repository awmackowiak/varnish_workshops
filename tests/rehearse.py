"""Rehearse checkpoint VCLs, then restore the original file, active VCL and health."""

import os
import re
import shlex
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

from lab_tests import B1, B2, fresh, request

ROOT = Path(__file__).resolve().parents[1]
VCL = ROOT / "varnish/vcl/default.vcl"
COMPOSE = shlex.split(os.environ.get("COMPOSE", "podman-compose"))
CREATED = []


def run(args, expected=0):
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=90)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    if result.returncode != expected:
        raise RuntimeError("%r exited %s, expected %s" % (args, result.returncode, expected))
    return result.stdout


def admin(*args):
    return run(COMPOSE + ["exec", "-T", "varnish", "varnishadm", *args])


def load(text):
    VCL.write_text(text)
    # Own the name before starting either CLI operation, including interruptions.
    name = "rehearsal_" + uuid.uuid4().hex
    CREATED.append(name)
    admin("vcl.load", name, "/etc/varnish/default.vcl")
    admin("vcl.use", name)


def wait_ready():
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if request(fresh("/nocache"))[0] == 200:
            return
        time.sleep(0.2)
    raise RuntimeError("Varnish did not become ready")


def main():
    # Capture state before mutation. A file edit might not be the currently active VCL.
    original = VCL.read_bytes()
    active = next(line.split()[3] for line in admin("vcl.list").splitlines()
                  if line.split() and line.split()[0] == "active")
    health = {base: request("/healthz", base=base)[0] for base in (B1, B2)}
    if any(status not in (200, 503) for status in health.values()):
        raise RuntimeError("unexpected initial backend health")
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        for base in health:
            if request("/health/up", method="POST", base=base)[0] != 200:
                raise RuntimeError("cannot make backend healthy")
        for number, checkpoint in enumerate((
            "01-backend", "02-routing", "03-cache", "04-ttl-vary",
            "05-grace", "06-purge", "07-director",
        ), 1):
            print("\nCheckpoint %s" % checkpoint, flush=True)
            load((ROOT / "solutions" / (checkpoint + ".vcl")).read_text())
            wait_ready()
            run(["./verify.sh", str(number)])

        final = (ROOT / "solutions/07-director.vcl").read_text()
        load(final)
        wait_ready()
        run(["./verify.sh"])

        # Model an untrusted caller without depending on host-specific container IPs.
        denied = re.sub(r"acl purge \{[^}]*\}", 'acl purge { "192.0.2.1"; }', final, count=1)
        load(denied)
        wait_ready()
        run([sys.executable, "tests/lab_tests.py", "PurgeDeniedTests"])

        load(final)
        wait_ready()
        url = fresh("/test1")
        before = request(url, {"Host": "example.com"})
        if before[0] != 200:
            raise RuntimeError("valid routing checkpoint did not respond")
        VCL.write_text(final + '\nsub vcl_synth { set resp.StatusCode = 200; }\n')
        result = subprocess.run(["make", "reload", "COMPOSE=" + shlex.join(COMPOSE)],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 or "StatusCode" not in result.stdout + result.stderr:
            raise RuntimeError("invalid VCL did not fail compilation as expected")
        if request(url, {"Host": "example.com"})[0] != 200:
            raise RuntimeError("failed reload disrupted the previously active VCL")
        print("PASS failed VCL compilation leaves active routing available", flush=True)

        faults = (
            ("b1", "TroubleshootingTests.test_static_is_cacheable_after_repair"),
            ("b2", "TroubleshootingTests.test_both_backends_are_in_the_pool"),
            ("b3", "TroubleshootingTests.test_user_agent_does_not_fragment_default_hash"),
        )
        for name, contract in faults:
            print("\nExpected failure: %s" % name, flush=True)
            load((ROOT / "broken" / (name + ".vcl")).read_text())
            wait_ready()
            run([sys.executable, "tests/lab_tests.py", contract], expected=1)
            load(final)
            wait_ready()
            run([sys.executable, "tests/lab_tests.py", contract])
        print("\nPASS all checkpoints, authorization, safe reload and deliberate faults", flush=True)
    finally:
        errors = []
        try:
            VCL.write_bytes(original)
        except OSError as error:
            errors.append(error)
        try:
            admin("vcl.use", active)
        except Exception as error:
            errors.append(error)
        for base, status in health.items():
            path = "/health/up" if status == 200 else "/health/down"
            try:
                if request(path, method="POST", base=base)[0] != 200:
                    raise RuntimeError("failed to restore backend health at " + base)
            except Exception as error:
                errors.append(error)
        try:
            existing = {line.split()[3] for line in admin("vcl.list").splitlines() if line.split()}
        except Exception as error:
            errors.append(error)
            existing = set(CREATED)
        for name in CREATED:
            if name not in existing:
                continue
            try:
                admin("vcl.discard", name)
            except Exception as error:
                errors.append(error)
        if errors:
            raise RuntimeError("rehearsal cleanup errors: " + "; ".join(map(str, errors)))
        print("Restored original VCL file, active configuration and backend health; discarded rehearsal VCLs", flush=True)


if __name__ == "__main__":
    main()
