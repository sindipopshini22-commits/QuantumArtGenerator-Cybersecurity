# ════════════════════════════════════════════════════════════════════
# FILE: circuit_library.py
# PURPOSE: Quantum circuit factory for Quantum Noise Art project.
#          Builds 5 distinct circuit topologies that produce different
#          randomness profiles — from cryptographic-grade uniform noise
#          to artistically-biased quantum distributions.
# AUTHOR: Quantum Layer Team — Part 1 of 4
# ════════════════════════════════════════════════════════════════════

from __future__ import annotations

import math

from qiskit import QuantumCircuit


class QuantumCircuitLibrary:
    """Factory for all quantum circuit topologies used in the project.

    Each public method returns a fully-measured Qiskit QuantumCircuit
    ready to be transpiled and executed on any backend.  The five
    circuit types produce qualitatively different bit distributions
    that map to distinct visual textures when converted to pixel data.
    """

    # ── Circuit A ─────────────────────────────────────────────────
    @staticmethod
    def hadamard(n_qubits: int) -> QuantumCircuit:
        """Uniform superposition circuit — the cryptographic default.

        Applies a Hadamard gate to every qubit, placing each in an
        equal superposition of |0⟩ and |1⟩.  Measurement collapses
        each qubit independently with P(0) = P(1) = 0.5, yielding
        maximum Shannon entropy (H = 1.0 per bit).

        Args:
            n_qubits: Number of qubits (and classical bits).

        Returns:
            A measured QuantumCircuit.
        """
        qc = QuantumCircuit(n_qubits, n_qubits)
        # Pure superposition — maximum entropy
        for i in range(n_qubits):
            qc.h(i)
        qc.measure(range(n_qubits), range(n_qubits))
        return qc

    # ── Circuit B ─────────────────────────────────────────────────
    @staticmethod
    def bell_pairs(n_qubits: int) -> QuantumCircuit:
        """Chained Bell-pair circuit — spatially correlated noise.

        Creates nearest-neighbour entanglement by applying H on qubit 0
        then cascading CNOT gates: cx(0,1), cx(1,2), …  Adjacent qubits
        become correlated, so neighbouring pixel bytes in the output
        image will show short-range spatial structure — streaks, bands,
        and local texture rather than pure static.

        Args:
            n_qubits: Number of qubits (≥ 2 for meaningful entanglement).

        Returns:
            A measured QuantumCircuit.
        """
        qc = QuantumCircuit(n_qubits, n_qubits)
        qc.h(0)
        # CNOT chain: each qubit entangled with its immediate neighbour.
        # In the resulting image this creates short-range spatial
        # correlations — adjacent pixels share partial information,
        # producing streak-like textures instead of uniform static.
        for i in range(n_qubits - 1):
            qc.cx(i, i + 1)
        qc.measure(range(n_qubits), range(n_qubits))
        return qc

    # ── Circuit C ─────────────────────────────────────────────────
    @staticmethod
    def ghz_state(n_qubits: int) -> QuantumCircuit:
        """Greenberger–Horne–Zeilinger state — global entanglement.

        The GHZ state |GHZ⟩ = (|00…0⟩ + |11…1⟩)/√2 is a maximally
        entangled state where ALL qubits are correlated.  Measurement
        collapses the entire register to either all-zeros or all-ones,
        producing only two possible bitstrings.  In image space this
        creates dramatic large-scale patterns: blocks of pure black
        (0x00) or pure white (0xFF) with no intermediate values.

        Args:
            n_qubits: Number of qubits.

        Returns:
            A measured QuantumCircuit.
        """
        qc = QuantumCircuit(n_qubits, n_qubits)
        # GHZ state: H on qubit 0, then CNOT from qubit 0 to every other.
        # Unlike the Bell chain, the star topology means ALL qubits share
        # the same quantum correlation — measurement is collectively
        # all-zero or all-one, nothing in between.
        qc.h(0)
        for i in range(1, n_qubits):
            qc.cx(0, i)
        qc.measure(range(n_qubits), range(n_qubits))
        return qc

    # ── Circuit D ─────────────────────────────────────────────────
    @staticmethod
    def parameterized_ry(n_qubits: int, theta: float) -> QuantumCircuit:
        """Bias-controlled rotation circuit — tonal palette knob.

        Applies Ry(θ) to each qubit independently.  The probability of
        measuring |1⟩ is sin²(θ/2):

          • θ = π/2  → P(1) = 0.5  (same as Hadamard — uniform)
          • θ < π/2  → P(1) < 0.5  (biased toward 0 — darker images)
          • θ > π/2  → P(1) > 0.5  (biased toward 1 — brighter images)

        This gives the artist direct control over the overall luminance
        "mood" of the generated image, from deep shadows to blown-out
        highlights, all driven by genuine quantum probability.

        Args:
            n_qubits: Number of qubits.
            theta: Rotation angle in radians, must be in [0, π].

        Returns:
            A measured QuantumCircuit.

        Raises:
            ValueError: If theta is outside [0, π].
        """
        if theta is None:
            raise ValueError("theta is required for parameterized_ry circuit.")
        if not (0.0 <= theta <= math.pi):
            raise ValueError(
                f"theta must be in [0, π] (got {theta:.4f}). "
                f"Use θ=π/2 for uniform, θ<π/2 for darker, θ>π/2 for brighter."
            )
        qc = QuantumCircuit(n_qubits, n_qubits)
        for i in range(n_qubits):
            qc.ry(theta, i)
        qc.measure(range(n_qubits), range(n_qubits))
        return qc

    # ── Circuit E ─────────────────────────────────────────────────
    @staticmethod
    def hardware_noise(n_qubits: int) -> QuantumCircuit:
        """Raw hardware noise circuit — the quantum fingerprint.

        Structurally identical to the Hadamard circuit, but intended to
        be run *only* on real IBM quantum hardware without any error
        mitigation.  The artistic value lies in the imperfections.

        Args:
            n_qubits: Number of qubits.

        Returns:
            A measured QuantumCircuit.
        """
        qc = QuantumCircuit(n_qubits, n_qubits)
        # ── HARDWARE NOISE — artistic quantum fingerprint ──────────
        # On real IBM hardware, decoherence, gate errors, and crosstalk
        # introduce measurable bias.  This circuit intentionally has no
        # error mitigation.  The imperfection is the artistic signature
        # of real quantum hardware.
        #
        # When run on a simulator this is functionally identical to
        # hadamard().  The magic only appears on actual QPU silicon
        # where T1/T2 relaxation times, readout errors, and ZZ
        # crosstalk leave a unique device-specific imprint in the
        # output distribution.
        for i in range(n_qubits):
            qc.h(i)
        qc.measure(range(n_qubits), range(n_qubits))
        return qc

    # ── Dispatcher ────────────────────────────────────────────────
    def get_circuit(
        self,
        circuit_type: str,
        n_qubits: int,
        theta: float | None = None,
    ) -> QuantumCircuit:
        """Return a circuit by its string name.

        Args:
            circuit_type: One of 'hadamard', 'bell', 'ghz',
                          'parameterized', 'hardware_noise'.
            n_qubits: Number of qubits.
            theta: Rotation angle (required only for 'parameterized').

        Returns:
            A measured QuantumCircuit.

        Raises:
            ValueError: If *circuit_type* is not recognised.
        """
        dispatch: dict[str, object] = {
            'hadamard': lambda: self.hadamard(n_qubits),
            'bell': lambda: self.bell_pairs(n_qubits),
            'ghz': lambda: self.ghz_state(n_qubits),
            'parameterized': lambda: self.parameterized_ry(n_qubits, theta),
            'hardware_noise': lambda: self.hardware_noise(n_qubits),
        }
        builder = dispatch.get(circuit_type)
        if builder is None:
            valid = ', '.join(sorted(dispatch.keys()))
            raise ValueError(
                f"Unknown circuit_type '{circuit_type}'. "
                f"Valid options: {valid}"
            )
        return builder()

    # ── Diagram helper ────────────────────────────────────────────
    def get_circuit_diagram(
        self, circuit_type: str, n_qubits: int = 4, theta: float | None = None,
    ) -> str:
        """Return an ASCII art diagram of the requested circuit.

        Useful for the Streamlit frontend to visualise circuit topology
        without needing Qiskit installed on the display side.

        Args:
            circuit_type: Circuit name string.
            n_qubits: Number of qubits to draw (default 4 for readability).
            theta: Rotation angle (only for 'parameterized').

        Returns:
            Multi-line ASCII string of the circuit diagram.
        """
        if circuit_type == 'parameterized' and theta is None:
            theta = math.pi / 2  # default for diagram display
        qc = self.get_circuit(circuit_type, n_qubits, theta=theta)
        return qc.draw('text').__str__()

    # ── Human-readable descriptions for UI ────────────────────────
    @staticmethod
    def get_circuit_descriptions() -> dict[str, str]:
        """Return user-friendly descriptions for each circuit type.

        Returns:
            Dict mapping circuit name to a 2-3 sentence description.
        """
        return {
            'hadamard': (
                "Pure Hadamard superposition on every qubit. Produces "
                "maximum-entropy uniform randomness — the gold standard "
                "for cryptographic key generation. Images appear as "
                "pure quantum static with no discernible pattern."
            ),
            'bell': (
                "Chained Bell pairs create nearest-neighbour entanglement. "
                "Adjacent qubits are correlated, producing short-range "
                "spatial texture in the image — streaks and micro-bands "
                "that give the art an organic, flowing quality."
            ),
            'ghz': (
                "Greenberger–Horne–Zeilinger state: global all-or-nothing "
                "entanglement. Every shot collapses to all-zeros or all-ones, "
                "creating bold black-and-white blocks. The most dramatic and "
                "least random of all circuit types."
            ),
            'parameterized': (
                "Ry(θ) rotation on each qubit acts as a brightness knob. "
                "θ = π/2 gives uniform randomness; smaller angles darken the "
                "image; larger angles brighten it. This lets the artist "
                "control the tonal mood while keeping quantum origin."
            ),
            'hardware_noise': (
                "Identical to Hadamard in structure, but designed to run on "
                "real IBM hardware with no error mitigation. Decoherence, "
                "gate errors, and crosstalk leave a unique fingerprint — "
                "the imperfection *is* the art."
            ),
        }
