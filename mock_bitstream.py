"""
Mock BitStreamResult — Part 4 development stub.
Replace with real Part 1 output at hour 14.

All Part 4 modules import from here during standalone development.
"""
import os
import hashlib
import struct
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BitStreamResult:
    bits: list          # Raw 0s and 1s
    bytes_data: bytes   # Packed bytes  (named bytes_data to avoid shadowing builtin)
    job_id: str
    circuit_type: str   # hadamard / bell / ghz / parameterized
    n_bits: int
    timestamp: str      # ISO UTC
    backend: str = "aer_simulator"
    n_qubits: int = 8
    n_shots: int = 4096
    raw_counts: dict = field(default_factory=dict)


def generate_mock_bitstream(
    n_bits: int = 32768,
    circuit_type: str = "hadamard",
    seed: Optional[int] = None,
) -> BitStreamResult:
    """
    Generate a mock BitStreamResult using os.urandom (cryptographic quality).
    Produces the same interface as Part 1's real QRNG.
    """
    if seed is not None:
        import random
        rng = random.Random(seed)
        raw = bytes([rng.randint(0, 255) for _ in range((n_bits + 7) // 8)])
    else:
        raw = os.urandom((n_bits + 7) // 8)

    bits = []
    for byte in raw:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    bits = bits[:n_bits]

    job_id = "SIM-" + hashlib.sha256(raw[:16]).hexdigest()[:12].upper()
    timestamp = datetime.now(timezone.utc).isoformat()

    return BitStreamResult(
        bits=bits,
        bytes_data=raw[:n_bits // 8],
        job_id=job_id,
        circuit_type=circuit_type,
        n_bits=n_bits,
        timestamp=timestamp,
    )
