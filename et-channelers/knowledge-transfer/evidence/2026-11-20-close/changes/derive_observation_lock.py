"""Derive the bounded provider-journal lock from the frozen ordinary controller."""
from pathlib import Path
import argparse
import hashlib

ORIGINAL = "4b31b555c63e2b04bdfa9cb7a8e5349451cf9c37250e040d2bd7b8c729b27a0b"
HELPER = '''@contextmanager
def provider_ledger_lock(path, *, acquire, contention, timeout=12.0):
    """Retry only acquisition of this finite cross-process observation writer."""
    deadline = time.monotonic() + timeout
    delay = 0.04
    with ExitStack() as owned:
        while True:
            try:
                owned.enter_context(acquire(path))
                break
            except contention as error:
                remaining = deadline - time.monotonic()
                if error.kind != 'gpu_owner_busy' or remaining <= 0:
                    raise
                time.sleep(min(remaining, delay))
                delay = min(0.25, delay * 2)
        yield


'''
def derive(source):
    if hashlib.sha256(source).hexdigest() != ORIGINAL:
        raise ValueError("frozen runtime_policy hash mismatch")
    text = source.decode("utf-8").replace("\r\n", "\n")
    previous = "        sys.path.insert(0,str(contract.PUBLIC_PIPE));from gpu_asr import kernel_lock\n        lock=kernel_lock"
    successor = ("        sys.path.insert(0,str(contract.PUBLIC_PIPE));from gpu_asr import AsrError, kernel_lock\n"
                 "        lock=partial(provider_ledger_lock, acquire=kernel_lock, contention=AsrError)")
    if text.count(previous) != 1 or text.count("def first_stop(") != 1:
        raise ValueError("unrecognized provider ledger boundary")
    text = text.replace("import hashlib", "from contextlib import ExitStack, contextmanager\nfrom functools import partial\nimport hashlib", 1)
    return text.replace("def first_stop(", HELPER + "def first_stop(", 1).replace(previous, successor).encode("utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    with args.destination.open("xb") as output:
        output.write(derive(args.source.read_bytes()))
