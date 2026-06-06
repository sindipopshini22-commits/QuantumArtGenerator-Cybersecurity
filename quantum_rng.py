# ══════════════════════════════════════════════════════════════════════
# FILE: quantum_rng.py
# PURPOSE: Main interface for quantum random number generation.
#          Defines the BitStreamResult dataclass — the single contract
#          object consumed by every other module in the project — and
#          exposes QuantumRNG, the high-level API for generating
#          cryptographic-grade random bitstreams from Qiskit circuits.
# AUTHOR: Quantum Layer Team — Part 1 of 4
# ══════════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import logging
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from math import ceil

import numpy as np
from qiskit import transpile

from backend_manager import BackendManager
from circuit_library import QuantumCircuitLibrary
from pixel_converter import PixelConverter

# ── Logging configuration ────────────────────────────────────────────
_LOG_FORMAT = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'

logger = logging.getLogger('quantum_rng')
logger.setLevel(logging.DEBUG)

# File handler — persistent log for audit trail
_fh = logging.FileHandler('quantum_rng.log', encoding='utf-8')
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter(_LOG_FORMAT))
logger.addHandler(_fh)

# Console handler — INFO and above
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter(_LOG_FORMAT))
logger.addHandler(_ch)


# ══════════════════════════════════════════════════════════════════════
# THE TEAM CONTRACT — every other part receives ONLY this object.
# ══════════════════════════════════════════════════════════════════════

@dataclass
class BitStreamResult:
    """Standardised output of every quantum random generation job.

    This dataclass is the *only* object that crosses module boundaries.
    Parts 2 (Crypto), 3 (Artist), and 4 (Frontend) all consume it
    directly.  Treat the field names as a public API — do not rename
    without coordinating with the full team.

    Attributes:
        bits: Raw flat bit array, e.g. ``[1, 0, 1, 1, 0, ...]``.
        bytes_data: The same bits packed into a ``bytes`` object.
        job_id: IBM job ID, or ``'SIM-<md5>'`` for simulator runs.
        circuit_type: Which circuit topology produced the bits.
        backend: Backend name string (e.g. ``'aer_simulator'``).
        n_qubits: Number of qubits used in the generating circuit.
        n_shots: Number of measurement shots executed.
        timestamp: UTC ISO-8601 timestamp of generation.
        raw_counts: Raw Qiskit counts dict, e.g. ``{'0110': 42}``.
        theta: Rotation angle for parameterized circuits, else *None*.
        entropy_estimate: Quick Shannon entropy computed at generation.
        bias: P(1) across all bits — ideal is 0.5000.
    """
    bits: list[int]
    bytes_data: bytes
    job_id: str
    circuit_type: str
    backend: str
    n_qubits: int
    n_shots: int
    timestamp: str
    raw_counts: dict
    theta: float | None
    entropy_estimate: float
    bias: float


# ══════════════════════════════════════════════════════════════════════
# QuantumRNG — high-level generation API
# ══════════════════════════════════════════════════════════════════════

class QuantumRNG:
    """High-level interface for quantum random bitstream generation.

    Orchestrates :class:`QuantumCircuitLibrary` (circuit construction),
    :class:`BackendManager` (execution backend), and
    :class:`PixelConverter` (byte-to-pixel mapping) into a single
    ``generate_*`` call family.

    Args:
        ibm_token: IBM Quantum API token.  Defaults to the
            ``IBM_QUANTUM_TOKEN`` environment variable.
        prefer_hardware: Default hardware preference for all calls.
    """

    # Fixed qubit count — gives 8 bits per shot (one byte per shot)
    N_QUBITS: int = 8

    def __init__(
        self,
        ibm_token: str | None = None,
        prefer_hardware: bool = False,
    ) -> None:
        self._prefer_hardware = prefer_hardware
        self._backend_mgr = BackendManager(
            ibm_token=ibm_token,
            use_simulator=not prefer_hardware,
        )
        self._circuit_lib = QuantumCircuitLibrary()
        logger.info(
            "QuantumRNG initialised (prefer_hardware=%s)", prefer_hardware
        )

    # ── Core generation method ───────────────────────────────────────

    def generate_bitstream(
        self,
        n_bits: int,
        circuit_type: str = 'hadamard',
        theta: float | None = None,
        prefer_hardware: bool = False,
    ) -> BitStreamResult:
        """Generate a quantum random bitstream.

        Builds the requested circuit, executes it on the best available
        backend, and packages the measurement outcomes into a
        :class:`BitStreamResult`.

        Args:
            n_bits: Number of random bits to produce.
            circuit_type: Circuit topology name.
            theta: Rotation angle (only for ``'parameterized'``).
            prefer_hardware: Override instance-level preference.

        Returns:
            A fully populated :class:`BitStreamResult`.

        Raises:
            ValueError: If *circuit_type* is unknown or *theta* is
                invalid for the parameterized circuit.
        """
        n_qubits = self.N_QUBITS
        # Add 10% buffer to account for rounding/shot quantisation
        shots_needed = ceil(n_bits / n_qubits * 1.10)
        shots_needed = max(shots_needed, 1)

        # 1. Build circuit
        qc = self._circuit_lib.get_circuit(circuit_type, n_qubits, theta=theta)

        # 2. Select backend
        use_hw = prefer_hardware or self._prefer_hardware
        try:
            backend, backend_name = self._backend_mgr.get_active_backend(
                prefer_hardware=use_hw
            )
        except Exception as exc:
            logger.warning(
                "Backend selection failed (%s) — falling back to simulator.", exc
            )
            backend = self._backend_mgr.get_simulator()
            backend_name = 'aer_simulator'

        # 3. Transpile and execute
        try:
            t_qc = transpile(qc, backend)
            job = backend.run(t_qc, shots=shots_needed)
            result = job.result()
            counts: dict = result.get_counts()
        except Exception as exc:
            logger.error(
                "Execution failed on %s: %s — retrying on simulator.",
                backend_name, exc,
            )
            backend = self._backend_mgr.get_simulator()
            backend_name = 'aer_simulator'
            t_qc = transpile(qc, backend)
            job = backend.run(t_qc, shots=shots_needed)
            result = job.result()
            counts = result.get_counts()

        # 4. Convert counts dict → flat bit array
        # Each key is a bitstring like '01101010', each value is its
        # repetition count.  We expand into a flat list of 0s and 1s.
        all_bits: list[int] = []
        for bitstring, count in counts.items():
            bit_row = [int(b) for b in bitstring]
            for _ in range(count):
                all_bits.extend(bit_row)

        # Trim to exactly n_bits
        all_bits = all_bits[:n_bits]

        # 5. Pack bits into bytes (groups of 8)
        byte_list: list[int] = []
        for i in range(0, len(all_bits) - len(all_bits) % 8, 8):
            byte_val = 0
            for j in range(8):
                byte_val = (byte_val << 1) | all_bits[i + j]
            byte_list.append(byte_val)
        bytes_data = bytes(byte_list)

        # 6. Compute job_id
        timestamp = datetime.now(timezone.utc).isoformat()
        if backend_name == 'aer_simulator':
            hash_input = f"{counts}{timestamp}{n_bits}"
            md5 = hashlib.md5(hash_input.encode()).hexdigest()[:12]
            job_id = f"SIM-{md5}"
        else:
            try:
                job_id = job.job_id()
            except Exception:
                job_id = f"HW-{hashlib.md5(str(counts).encode()).hexdigest()[:12]}"

        # 7. Compute quick Shannon entropy estimate
        if len(all_bits) > 0:
            p1 = sum(all_bits) / len(all_bits)
        else:
            p1 = 0.5
        p0 = 1.0 - p1
        entropy_estimate = (
            -p0 * math.log2(p0 + 1e-12) - p1 * math.log2(p1 + 1e-12)
        )

        # 8. Compute bias
        bias = p1

        # 9. Log summary
        logger.info(
            "Generated %d bits | circuit=%s | backend=%s | "
            "job_id=%s | entropy=%.4f | bias=%.4f",
            n_bits, circuit_type, backend_name,
            job_id, entropy_estimate, bias,
        )

        return BitStreamResult(
            bits=all_bits,
            bytes_data=bytes_data,
            job_id=job_id,
            circuit_type=circuit_type,
            backend=backend_name,
            n_qubits=n_qubits,
            n_shots=shots_needed,
            timestamp=timestamp,
            raw_counts=counts,
            theta=theta,
            entropy_estimate=entropy_estimate,
            bias=bias,
        )

    # ── Convenience wrappers ─────────────────────────────────────────

    def generate_key_bytes(
        self,
        n_bytes: int,
        circuit_type: str = 'hadamard',
        theta: float | None = None,
    ) -> BitStreamResult:
        """Generate exactly *n_bytes* of quantum key material.

        Convenience wrapper used by Part 2 (Cryptography) to produce
        OTP keys of a specific byte length.

        Args:
            n_bytes: Number of key bytes needed.
            circuit_type: Circuit topology name.
            theta: Rotation angle (parameterized circuit only).

        Returns:
            A :class:`BitStreamResult` containing ≥ *n_bytes* \u00d7 8 bits.
        """
        return self.generate_bitstream(
            n_bits=n_bytes * 8,
            circuit_type=circuit_type,
            theta=theta,
        )

    def generate_pixel_array(
        self,
        width: int,
        height: int,
        color_mode: str = 'RGB',
        circuit_type: str = 'hadamard',
        theta: float | None = None,
    ) -> tuple[BitStreamResult, np.ndarray]:
        """Generate a pixel array from quantum random bytes.

        This is the primary interface for Part 3 (Artist).  Computes
        the exact number of bytes needed for the requested image
        dimensions, generates them, and reshapes into a NumPy pixel
        array ready for rendering.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.
            color_mode: 'L' (grayscale), 'RGB', or 'RGBA'.
            circuit_type: Circuit topology name.
            theta: Rotation angle (parameterized circuit only).

        Returns:
            Tuple of (*BitStreamResult*, *numpy pixel array*).

        Raises:
            ValueError: If *color_mode* is unsupported.
        """
        channels_map = {'L': 1, 'RGB': 3, 'RGBA': 4}
        if color_mode not in channels_map:
            raise ValueError(
                f"Unsupported color_mode '{color_mode}'. "
                f"Choose from: {', '.join(sorted(channels_map))}"
            )
        channels = channels_map[color_mode]
        n_bytes = width * height * channels

        result = self.generate_key_bytes(
            n_bytes=n_bytes,
            circuit_type=circuit_type,
            theta=theta,
        )

        pixel_array = PixelConverter.to_array(
            result.bytes_data, width, height, color_mode
        )

        return result, pixel_array

    # ── Diagram delegation ───────────────────────────────────────────

    def get_circuit_diagram(self, circuit_type: str) -> str:
        """Return ASCII circuit diagram for the requested topology.

        Delegates to :meth:`QuantumCircuitLibrary.get_circuit_diagram`.

        Args:
            circuit_type: Circuit name string.

        Returns:
            Multi-line ASCII diagram.
        """
        return self._circuit_lib.get_circuit_diagram(circuit_type)
