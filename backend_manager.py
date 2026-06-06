# ════════════════════════════════════════════════════════════════════
# FILE: backend_manager.py
# PURPOSE: Manages Qiskit execution backends — local Aer simulator
#          and (optionally) real IBM Quantum hardware.  Handles
#          authentication, backend selection, health checks, and
#          graceful fallback so that the rest of the system never
#          crashes due to a hardware outage.
# AUTHOR: Quantum Layer Team — Part 1 of 4
# ════════════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
import os

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Optional IBM Quantum Runtime — system must work without it.
try:
    from qiskit_ibm_runtime import QiskitRuntimeService
    _HAS_IBM_RUNTIME = True
except ImportError:
    _HAS_IBM_RUNTIME = False

logger = logging.getLogger(__name__)


class BackendManager:
    """Centralised manager for quantum execution backends.

    Supports two modes:
      1. **Simulator-only** (default) — uses Qiskit Aer locally.
      2. **IBM Quantum hardware** — requires a valid IBM token.

    The manager guarantees that a usable backend is always available:
    if hardware is requested but unreachable, it silently falls back
    to the simulator and logs a warning.

    Args:
        ibm_token: IBM Quantum API token.  Falls back to the
            ``IBM_QUANTUM_TOKEN`` environment variable when *None*.
        use_simulator: When *True* (default), always prefer the
            local simulator regardless of token availability.
    """

    def __init__(
        self,
        ibm_token: str | None = None,
        use_simulator: bool = True,
    ) -> None:
        self._use_simulator = use_simulator
        self._service: QiskitRuntimeService | None = None

        # Resolve token: explicit arg → env var → None
        token = ibm_token or os.getenv('IBM_QUANTUM_TOKEN', None)

        if token and _HAS_IBM_RUNTIME:
            try:
                self._service = QiskitRuntimeService(
                    channel='ibm_quantum', token=token
                )
                logger.info(
                    "IBM Quantum Runtime initialised (channel=ibm_quantum)."
                )
            except Exception as exc:
                logger.error("Failed to initialise IBM Runtime: %s", exc)
                self._service = None
        elif token and not _HAS_IBM_RUNTIME:
            logger.warning(
                "IBM token provided but qiskit-ibm-runtime is not installed. "
                "Install with: pip install qiskit-ibm-runtime"
            )
        else:
            logger.info(
                "No IBM token — running in simulator-only mode. "
                "Set IBM_QUANTUM_TOKEN env var to enable hardware."
            )

    # ── Simulator ─────────────────────────────────────────────────
    @staticmethod
    def get_simulator() -> AerSimulator:
        """Return a fresh Aer simulator instance.

        Uses 'automatic' method selection so Aer picks the best
        simulation strategy for the circuit size.

        Returns:
            An AerSimulator backend.
        """
        return AerSimulator(method='automatic')

    # ── Hardware ──────────────────────────────────────────────────
    def get_best_hardware_backend(self) -> object | None:
        """Query IBM Quantum for the least-busy operational backend.

        Returns:
            A backend instance, or *None* if hardware is unavailable.
        """
        if self._service is None:
            logger.warning("No IBM Runtime service — cannot query hardware.")
            return None
        try:
            backend = self._service.least_busy(
                operational=True, simulator=False
            )
            logger.info("Selected hardware backend: %s", backend.name)
            return backend
        except Exception as exc:
            logger.error("Hardware backend query failed: %s", exc)
            return None

    # ── Unified accessor ──────────────────────────────────────────
    def get_active_backend(
        self, prefer_hardware: bool = False
    ) -> tuple[object, str]:
        """Return the backend to use for the next job.

        Args:
            prefer_hardware: If *True*, attempt hardware first.

        Returns:
            Tuple of (*backend_object*, *backend_name_string*).
        """
        if prefer_hardware and not self._use_simulator:
            hw = self.get_best_hardware_backend()
            if hw is not None:
                return hw, hw.name
            logger.warning(
                "Hardware requested but unavailable — falling back to simulator."
            )
        sim = self.get_simulator()
        return sim, 'aer_simulator'

    # ── Queue estimation ──────────────────────────────────────────
    @staticmethod
    def estimate_queue_time(backend: object) -> str:
        """Estimate the wait time for a backend's job queue.

        Args:
            backend: A Qiskit backend object.

        Returns:
            A human-readable time estimate string.
        """
        try:
            status = backend.status()
            pending = getattr(status, 'pending_jobs', 0)
            if pending == 0:
                return "No queue — immediate execution"
            elif pending <= 5:
                return "~2 minutes"
            elif pending <= 20:
                return "~10 minutes"
            elif pending <= 50:
                return "~30 minutes"
            else:
                return f"~{pending * 2} minutes ({pending} jobs ahead)"
        except Exception:
            return "Unknown"

    # ── Credit cost estimator ─────────────────────────────────────
    @staticmethod
    def check_credit_cost(n_qubits: int, n_shots: int) -> dict:
        """Estimate IBM Quantum credit cost for a job.

        The formula is approximate: *n_qubits × n_shots / 1000*.

        Args:
            n_qubits: Number of qubits in the circuit.
            n_shots: Number of measurement shots.

        Returns:
            Dict with 'estimated_credits', 'warning' flag, and 'message'.
        """
        credits = round(n_qubits * n_shots / 1000, 2)
        warning = credits > 10
        message = (
            f"Estimated cost: {credits} credits "
            f"({n_qubits} qubits × {n_shots} shots)."
        )
        if warning:
            message += (
                " ⚠ This exceeds 10 credits — consider reducing shots "
                "or switching to the simulator."
            )
        return {
            'estimated_credits': credits,
            'warning': warning,
            'message': message,
        }

    # ── Health check ──────────────────────────────────────────────
    def health_check(self) -> dict:
        """Run a quick diagnostic on all available backends.

        Executes a trivial 1-qubit Hadamard circuit on the simulator
        and optionally pings the IBM service.

        Returns:
            Dict with 'simulator_ok', 'hardware_ok',
            'hardware_backend', and 'message' fields.
        """
        result: dict = {
            'simulator_ok': False,
            'hardware_ok': False,
            'hardware_backend': None,
            'message': '',
        }
        messages: list[str] = []

        # -- Simulator test --
        try:
            sim = self.get_simulator()
            qc = QuantumCircuit(1, 1)
            qc.h(0)
            qc.measure(0, 0)
            t_qc = transpile(qc, sim)
            job = sim.run(t_qc, shots=100)
            counts = job.result().get_counts()
            if '0' in counts or '1' in counts:
                result['simulator_ok'] = True
                messages.append("✓ Simulator OK")
            else:
                messages.append("✗ Simulator returned unexpected counts")
        except Exception as exc:
            messages.append(f"✗ Simulator FAILED: {exc}")
            logger.error("Health-check simulator failure: %s", exc)

        # -- Hardware test --
        if self._service is not None:
            try:
                hw = self.get_best_hardware_backend()
                if hw is not None:
                    result['hardware_ok'] = True
                    result['hardware_backend'] = hw.name
                    messages.append(f"✓ Hardware available: {hw.name}")
                else:
                    messages.append("✗ No operational hardware backend found")
            except Exception as exc:
                messages.append(f"✗ Hardware check FAILED: {exc}")
                logger.error("Health-check hardware failure: %s", exc)
        else:
            messages.append(
                "⊘ Hardware not configured (no IBM token or runtime)"
            )

        result['message'] = ' | '.join(messages)
        return result
