# ══════════════════════════════════════════════════════════════════════
# FILE: test_quantum.py
# PURPOSE: Comprehensive pytest test suite for the quantum layer.
#          Tests every public class and method, provides a mock
#          BitStreamResult factory for downstream team members, and
#          validates round-trip integrity of the byte↔pixel pipeline.
# AUTHOR: Quantum Layer Team — Part 1 of 4
# ══════════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from circuit_library import QuantumCircuitLibrary
from pixel_converter import PixelConverter
from quantum_rng import BitStreamResult, QuantumRNG
from statistical_validator import StatisticalValidator


# ══════════════════════════════════════════════════════════════════════
# MOCK BITSTREAM FACTORY
# ══════════════════════════════════════════════════════════════════════
# Exported at module level so other Parts can do:
#     from test_quantum import create_mock_bitstream
# ══════════════════════════════════════════════════════════════════════

def create_mock_bitstream(
    n_bytes: int = 1024,
    circuit_type: str = 'hadamard',
) -> BitStreamResult:
    """Create a realistic mock BitStreamResult without real quantum circuits.

    Uses ``os.urandom`` to stand in for quantum randomness so that
    Parts 2 (Crypto), 3 (Artist), and 4 (Frontend) can develop and
    test against the real dataclass shape without needing Qiskit
    running.

    Args:
        n_bytes: Number of random bytes to generate.
        circuit_type: Simulated circuit type label.

    Returns:
        A fully populated :class:`BitStreamResult`.
    """
    raw_bytes = os.urandom(n_bytes)

    # Unpack bytes into flat bit list
    bits: list[int] = []
    for byte in raw_bytes:
        for j in range(7, -1, -1):
            bits.append((byte >> j) & 1)

    # Compute realistic entropy and bias
    p1 = sum(bits) / len(bits) if bits else 0.5
    p0 = 1.0 - p1
    entropy = -p0 * math.log2(p0 + 1e-12) - p1 * math.log2(p1 + 1e-12)

    now = datetime.now(timezone.utc).isoformat()
    job_hash = hashlib.sha256(now.encode()).hexdigest()[:12]

    # Build a plausible raw_counts dict (simulated)
    raw_counts: dict[str, int] = {}
    n_shots = n_bytes  # 8 qubits → 1 byte per shot
    for i in range(0, len(bits) - 7, 8):
        key = ''.join(str(b) for b in bits[i:i+8])
        raw_counts[key] = raw_counts.get(key, 0) + 1

    return BitStreamResult(
        bits=bits,
        bytes_data=raw_bytes,
        job_id=f"MOCK-{job_hash}",
        circuit_type=circuit_type,
        backend='mock_urandom',
        n_qubits=8,
        n_shots=n_shots,
        timestamp=now,
        raw_counts=raw_counts,
        theta=None,
        entropy_estimate=round(entropy, 6),
        bias=round(p1, 6),
    )


# ══════════════════════════════════════════════════════════════════════
# HELPER: Mock Qiskit execution for QuantumRNG tests
# ══════════════════════════════════════════════════════════════════════

def _mock_run_result(n_qubits: int = 8, n_shots: int = 100) -> MagicMock:
    """Create a mock Qiskit job result with realistic counts."""
    counts: dict[str, int] = {}
    rng = np.random.RandomState(42)
    for _ in range(n_shots):
        bitstring = ''.join(str(rng.randint(0, 2)) for _ in range(n_qubits))
        counts[bitstring] = counts.get(bitstring, 0) + 1

    mock_result = MagicMock()
    mock_result.get_counts.return_value = counts

    mock_job = MagicMock()
    mock_job.result.return_value = mock_result
    mock_job.job_id.return_value = 'SIM-mock12345'
    return mock_job


# ══════════════════════════════════════════════════════════════════════
# TESTS: QuantumCircuitLibrary
# ══════════════════════════════════════════════════════════════════════

class TestQuantumCircuitLibrary:
    """Tests for circuit construction and dispatch."""

    def setup_method(self) -> None:
        self.lib = QuantumCircuitLibrary()

    def test_hadamard_circuit_structure(self) -> None:
        """Hadamard circuit should have H gates on all qubits."""
        qc = self.lib.hadamard(4)
        # Count H gates in the circuit
        h_count = sum(
            1 for inst in qc.data if inst.operation.name == 'h'
        )
        assert h_count == 4, f"Expected 4 H gates, got {h_count}"
        assert qc.num_qubits == 4
        assert qc.num_clbits == 4

    def test_bell_circuit_structure(self) -> None:
        """Bell circuit should have 1 H gate + (n-1) CNOT gates."""
        qc = self.lib.bell_pairs(4)
        h_count = sum(1 for inst in qc.data if inst.operation.name == 'h')
        cx_count = sum(1 for inst in qc.data if inst.operation.name == 'cx')
        assert h_count == 1, f"Expected 1 H gate, got {h_count}"
        assert cx_count == 3, f"Expected 3 CX gates, got {cx_count}"

    def test_ghz_circuit_structure(self) -> None:
        """GHZ circuit should have 1 H gate + (n-1) CNOTs from qubit 0."""
        qc = self.lib.ghz_state(5)
        h_count = sum(1 for inst in qc.data if inst.operation.name == 'h')
        cx_count = sum(1 for inst in qc.data if inst.operation.name == 'cx')
        assert h_count == 1
        assert cx_count == 4
        # Verify all CNOTs originate from qubit 0
        for inst in qc.data:
            if inst.operation.name == 'cx':
                control_qubit = inst.qubits[0]
                assert control_qubit == qc.qubits[0], (
                    "GHZ CNOTs must all originate from qubit 0"
                )

    def test_parameterized_valid_theta(self) -> None:
        """Parameterized circuit with valid theta should have Ry gates."""
        qc = self.lib.parameterized_ry(4, theta=math.pi / 2)
        ry_count = sum(1 for inst in qc.data if inst.operation.name == 'ry')
        assert ry_count == 4, f"Expected 4 Ry gates, got {ry_count}"

    def test_parameterized_invalid_theta(self) -> None:
        """Parameterized circuit with theta outside [0, π] must raise."""
        with pytest.raises(ValueError, match="theta must be in"):
            self.lib.parameterized_ry(4, theta=-1.0)
        with pytest.raises(ValueError, match="theta must be in"):
            self.lib.parameterized_ry(4, theta=4.0)

    def test_dispatcher_all_types(self) -> None:
        """get_circuit should return valid circuits for all 5 types."""
        for ct in ('hadamard', 'bell', 'ghz', 'hardware_noise'):
            qc = self.lib.get_circuit(ct, 4)
            assert qc.num_qubits == 4
        qc = self.lib.get_circuit('parameterized', 4, theta=math.pi / 2)
        assert qc.num_qubits == 4

    def test_dispatcher_unknown_type(self) -> None:
        """get_circuit with an invalid name must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown circuit_type"):
            self.lib.get_circuit('nonexistent', 4)


# ══════════════════════════════════════════════════════════════════════
# TESTS: BitStreamResult
# ══════════════════════════════════════════════════════════════════════

class TestBitStreamResult:
    """Tests for the BitStreamResult dataclass."""

    def test_dataclass_creation(self) -> None:
        """All fields should populate correctly."""
        bs = create_mock_bitstream(64)
        assert len(bs.bits) == 64 * 8
        assert len(bs.bytes_data) == 64
        assert bs.job_id.startswith('MOCK-')
        assert bs.circuit_type == 'hadamard'
        assert bs.backend == 'mock_urandom'
        assert bs.n_qubits == 8
        assert bs.timestamp is not None

    def test_entropy_range(self) -> None:
        """Entropy estimate must be in [0.0, 1.0]."""
        bs = create_mock_bitstream(1024)
        assert 0.0 <= bs.entropy_estimate <= 1.0

    def test_bias_range(self) -> None:
        """Bias must be in [0.0, 1.0]."""
        bs = create_mock_bitstream(1024)
        assert 0.0 <= bs.bias <= 1.0


# ══════════════════════════════════════════════════════════════════════
# TESTS: QuantumRNG (mocked backend)
# ══════════════════════════════════════════════════════════════════════

class TestQuantumRNG:
    """Tests for the QuantumRNG generation methods."""

    def _patch_backend_and_run(
        self, n_bits: int = 256, circuit_type: str = 'hadamard',
        theta: float | None = None,
    ) -> BitStreamResult:
        """Helper: run generate_bitstream with a mocked backend."""
        rng = QuantumRNG()

        # Mock the backend manager to return a fake simulator
        mock_backend = MagicMock()
        mock_backend.name = 'aer_simulator'

        n_qubits = 8
        shots_needed = math.ceil(n_bits / n_qubits * 1.10)
        mock_job = _mock_run_result(n_qubits, max(shots_needed, 100))
        mock_backend.run.return_value = mock_job

        with patch.object(rng._backend_mgr, 'get_active_backend',
                          return_value=(mock_backend, 'aer_simulator')):
            with patch('quantum_rng.transpile', side_effect=lambda qc, _: qc):
                return rng.generate_bitstream(
                    n_bits=n_bits,
                    circuit_type=circuit_type,
                    theta=theta,
                )

    def test_generate_bitstream_returns_correct_length(self) -> None:
        """Result bits list should have exactly n_bits elements."""
        result = self._patch_backend_and_run(n_bits=256)
        assert len(result.bits) == 256

    def test_generate_bitstream_exact_n_bits(self) -> None:
        """Test with an odd number of bits to verify trimming."""
        result = self._patch_backend_and_run(n_bits=100)
        assert len(result.bits) == 100

    def test_generate_bitstream_job_id_format_simulator(self) -> None:
        """Simulator job IDs must start with 'SIM-'."""
        result = self._patch_backend_and_run(n_bits=64)
        assert result.job_id.startswith('SIM-'), (
            f"Expected 'SIM-' prefix, got '{result.job_id}'"
        )

    def test_key_bytes_wrapper(self) -> None:
        """generate_key_bytes(n) should request n*8 bits internally."""
        rng = QuantumRNG()

        mock_backend = MagicMock()
        mock_backend.name = 'aer_simulator'
        mock_job = _mock_run_result(8, 200)
        mock_backend.run.return_value = mock_job

        with patch.object(rng._backend_mgr, 'get_active_backend',
                          return_value=(mock_backend, 'aer_simulator')):
            with patch('quantum_rng.transpile', side_effect=lambda qc, _: qc):
                result = rng.generate_key_bytes(n_bytes=32)

        assert len(result.bits) == 32 * 8

    def test_circuit_types_all_work(self) -> None:
        """All circuit types should produce a result without crashing."""
        for ct in ('hadamard', 'bell', 'ghz', 'hardware_noise'):
            result = self._patch_backend_and_run(
                n_bits=64, circuit_type=ct
            )
            assert result.circuit_type == ct

        result = self._patch_backend_and_run(
            n_bits=64, circuit_type='parameterized', theta=math.pi / 2
        )
        assert result.circuit_type == 'parameterized'


# ══════════════════════════════════════════════════════════════════════
# TESTS: PixelConverter
# ══════════════════════════════════════════════════════════════════════

class TestPixelConverter:
    """Tests for byte↔pixel conversion and roundtrip integrity."""

    def test_rgb_shape(self) -> None:
        """64×64 RGB array should be shape (64, 64, 3)."""
        data = os.urandom(64 * 64 * 3)
        arr = PixelConverter.to_array(data, 64, 64, 'RGB')
        assert arr.shape == (64, 64, 3)

    def test_grayscale_shape(self) -> None:
        """32×32 grayscale array should be shape (32, 32)."""
        data = os.urandom(32 * 32)
        arr = PixelConverter.to_array(data, 32, 32, 'L')
        assert arr.shape == (32, 32)

    def test_rgba_shape(self) -> None:
        """16×16 RGBA array should be shape (16, 16, 4)."""
        data = os.urandom(16 * 16 * 4)
        arr = PixelConverter.to_array(data, 16, 16, 'RGBA')
        assert arr.shape == (16, 16, 4)

    def test_roundtrip_rgb(self) -> None:
        """bytes → PIL image → bytes must be lossless for RGB."""
        original = os.urandom(32 * 32 * 3)
        img = PixelConverter.to_pil_image(original, 32, 32, 'RGB')
        recovered = PixelConverter.from_image(img)
        assert original == recovered

    def test_roundtrip_grayscale(self) -> None:
        """bytes → PIL image → bytes must be lossless for grayscale."""
        original = os.urandom(32 * 32)
        img = PixelConverter.to_pil_image(original, 32, 32, 'L')
        recovered = PixelConverter.from_image(img)
        assert original == recovered

    def test_verify_roundtrip_returns_true(self) -> None:
        """verify_roundtrip should return True for valid data."""
        data = os.urandom(16 * 16 * 3)
        assert PixelConverter.verify_roundtrip(data, 16, 16, 'RGB') is True

    def test_from_image_wrong_size(self) -> None:
        """Insufficient bytes should raise ValueError."""
        too_small = os.urandom(10)
        with pytest.raises(ValueError, match="Need .* bytes"):
            PixelConverter.to_array(too_small, 64, 64, 'RGB')


# ══════════════════════════════════════════════════════════════════════
# TESTS: StatisticalValidator
# ══════════════════════════════════════════════════════════════════════

class TestStatisticalValidator:
    """Tests for statistical analysis and comparison framework."""

    def test_entropy_perfect_random(self) -> None:
        """os.urandom bits should have entropy ≈ 1.0."""
        bs = create_mock_bitstream(2048)
        report = StatisticalValidator.full_analysis(bs)
        assert report['shannon_entropy'] > 0.99, (
            f"Expected entropy > 0.99, got {report['shannon_entropy']}"
        )

    def test_entropy_all_zeros(self) -> None:
        """A constant-zero stream should have entropy ≈ 0.0."""
        fake = BitStreamResult(
            bits=[0] * 10000,
            bytes_data=b'\x00' * 1250,
            job_id='TEST-zeros',
            circuit_type='test',
            backend='test',
            n_qubits=8,
            n_shots=1250,
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_counts={'00000000': 1250},
            theta=None,
            entropy_estimate=0.0,
            bias=0.0,
        )
        report = StatisticalValidator.full_analysis(fake)
        assert report['shannon_entropy'] < 0.01, (
            f"Expected entropy < 0.01 for all-zeros, got {report['shannon_entropy']}"
        )

    def test_grade_assignment(self) -> None:
        """Near-perfect random input should receive A+ or A grade."""
        bs = create_mock_bitstream(2048)
        report = StatisticalValidator.full_analysis(bs)
        assert report['grade'].startswith('A'), (
            f"Expected grade A+ or A, got {report['grade']}"
        )

    def test_compare_sources_returns_four(self) -> None:
        """compare_sources should return exactly 4 analysis dicts."""
        bs = create_mock_bitstream(1024)
        results = StatisticalValidator.compare_sources(bs)
        assert len(results) == 4
        assert results[0]['label'] == 'quantum'

    def test_quantum_best_entropy(self) -> None:
        """Quantum (mock) entropy should be ≥ LCG entropy."""
        bs = create_mock_bitstream(2048)
        results = StatisticalValidator.compare_sources(bs)
        quantum_ent = results[0]['shannon_entropy']
        lcg_ent = results[3]['shannon_entropy']  # LCG is last
        assert quantum_ent >= lcg_ent - 0.01, (
            f"Quantum entropy {quantum_ent} should be ≥ LCG entropy {lcg_ent}"
        )


# ══════════════════════════════════════════════════════════════════════
# Standalone runner
# ══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
