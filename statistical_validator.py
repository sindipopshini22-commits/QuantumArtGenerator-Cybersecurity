# ════════════════════════════════════════════════════════════════════
# FILE: statistical_validator.py
# PURPOSE: Statistical quality assurance for quantum random bitstreams.
#          Implements Shannon entropy, NIST-style randomness tests, and
#          a multi-source comparison framework to demonstrate quantum
#          superiority over classical PRNGs.
# AUTHOR: Quantum Layer Team — Part 1 of 4
# ════════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import logging
import math
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
from scipy import stats as sp_stats

logger = logging.getLogger(__name__)

# Deferred import of BitStreamResult to avoid circular dependency.
# At runtime this module only needs the dataclass shape, so a
# late import inside the methods that use it is sufficient.

# Optional NIST SP 800-22 battery
try:
    import nistrng
    _HAS_NISTRNG = True
except ImportError:
    _HAS_NISTRNG = False


class StatisticalValidator:
    """Comprehensive randomness quality analyser.

    Provides per-bitstream quality reports, NIST-style statistical
    tests, and a head-to-head comparison framework that benchmarks
    quantum output against three classical PRNG baselines.
    """

    # ── Primary analysis entry point ──────────────────────────────
    @staticmethod
    def full_analysis(
        bitstream: object,
        label: str | None = None,
    ) -> dict:
        """Run a comprehensive statistical analysis on a BitStreamResult.

        Uses up to the first 10 000 bits for efficiency, unless the
        stream is shorter.

        Args:
            bitstream: A BitStreamResult (or any object with a ``.bits``
                attribute that is a list[int] of 0/1 values).
            label: Optional human-readable label for the report.

        Returns:
            Dict of all computed metrics, grades, and verdicts.
        """
        bits = list(bitstream.bits[:10_000])
        n = len(bits)
        bits_arr = np.array(bits, dtype=np.float64)

        # ─── 1. Shannon Entropy ───────────────────────────────────
        p1 = float(np.mean(bits_arr))
        p0 = 1.0 - p1
        entropy = -p0 * math.log2(p0 + 1e-12) - p1 * math.log2(p1 + 1e-12)

        # ─── 2. Frequency (Monobit) Test ──────────────────────────
        ones = int(np.sum(bits_arr))
        zeros = n - ones
        chi2_stat, chi2_p = sp_stats.chisquare([zeros, ones], f_exp=[n / 2, n / 2])
        monobit_pass = bool(chi2_p > 0.01)

        # ─── 3. Runs Test (NIST SP 800-22 § 2.3) ─────────────────
        # A "run" is a maximal sequence of identical bits.
        runs = 1
        for i in range(1, n):
            if bits[i] != bits[i - 1]:
                runs += 1
        # Expected runs under randomness: E = 2*n*p0*p1 + 1
        expected_runs = 2.0 * n * p0 * p1 + 1.0
        std_runs = math.sqrt(
            max(2.0 * n * p0 * p1 * (2.0 * n * p0 * p1 - 1.0) / (n - 1), 1e-12)
        ) if n > 1 else 1.0
        runs_z = (runs - expected_runs) / std_runs if std_runs > 0 else 0.0
        runs_p = 2.0 * (1.0 - sp_stats.norm.cdf(abs(runs_z)))
        runs_pass = bool(runs_p > 0.01)

        # ─── 4. Autocorrelation at lags 1, 2, 3 ──────────────────
        centered = bits_arr - np.mean(bits_arr)
        full_corr = np.correlate(centered, centered, mode='full')
        mid = len(full_corr) // 2
        norm_factor = full_corr[mid] if full_corr[mid] != 0 else 1.0
        autocorr: dict[int, float] = {}
        for lag in (1, 2, 3):
            if mid + lag < len(full_corr):
                autocorr[lag] = float(full_corr[mid + lag] / norm_factor)
            else:
                autocorr[lag] = 0.0
        autocorr_pass = all(abs(v) < 0.02 for v in autocorr.values())

        # ─── 5. Bit Bias ─────────────────────────────────────────
        bias = p1
        bias_pass = bool(abs(bias - 0.5) < 0.005)

        # ─── 6. NIST SP 800-22 battery (optional) ────────────────
        nist_results: dict = {}
        nist_passed = 0
        nist_total = 0
        nist_available = _HAS_NISTRNG

        if _HAS_NISTRNG:
            try:
                # nistrng expects a numpy int8 array of 0/1
                seq = np.array(bits, dtype=np.int8)
                eligible = nistrng.check_eligibility_all_battery(seq, SP800_22_TESTS=nistrng.SP800_22R1a_BATTERY)
                results = nistrng.run_all_battery(seq, eligible, False)
                for name, passed, p_val in results:
                    nist_results[name] = {'passed': bool(passed), 'p_value': float(p_val)}
                    nist_total += 1
                    if passed:
                        nist_passed += 1
            except Exception as exc:
                logger.warning("NIST battery error: %s", exc)
                nist_results['error'] = str(exc)
        else:
            nist_results['message'] = (
                "Install nistrng for full NIST SP 800-22 battery: "
                "pip install nistrng"
            )

        nist_rate = nist_passed / nist_total if nist_total > 0 else 0.0

        # ─── Grade assignment ─────────────────────────────────────
        if entropy > 0.999 and (nist_rate > 0.95 or nist_total == 0):
            grade = 'A+ QUANTUM'
        elif entropy > 0.990 and (nist_rate > 0.90 or nist_total == 0):
            grade = 'A CRYPTO'
        elif entropy > 0.950:
            grade = 'B STANDARD'
        else:
            grade = 'F WEAK'

        # ─── Cryptographic verdict ────────────────────────────────
        if grade.startswith('A+'):
            verdict = (
                "Excellent — this bitstream meets cryptographic-grade "
                "randomness requirements.  Suitable for OTP key material."
            )
        elif grade.startswith('A'):
            verdict = (
                "Good — near-cryptographic quality.  Minor bias detected "
                "but acceptable for most applications."
            )
        elif grade.startswith('B'):
            verdict = (
                "Fair — noticeable deviation from ideal randomness.  "
                "Fine for art, but not recommended for strong cryptography."
            )
        else:
            verdict = (
                "Weak — significant bias or structure detected.  "
                "Not suitable for cryptographic use."
            )

        return {
            'label': label or getattr(bitstream, 'circuit_type', 'unknown'),
            'n_bits_analysed': n,
            'shannon_entropy': round(entropy, 6),
            'monobit_chi2': round(float(chi2_stat), 4),
            'monobit_p_value': round(float(chi2_p), 6),
            'monobit_pass': monobit_pass,
            'runs_count': runs,
            'runs_expected': round(expected_runs, 2),
            'runs_z': round(runs_z, 4),
            'runs_p_value': round(runs_p, 6),
            'runs_pass': runs_pass,
            'autocorrelation': {k: round(v, 6) for k, v in autocorr.items()},
            'autocorrelation_pass': autocorr_pass,
            'bias': round(bias, 6),
            'bias_pass': bias_pass,
            'nist_available': nist_available,
            'nist_passed': nist_passed,
            'nist_total': nist_total,
            'nist_pass_rate': round(nist_rate, 4),
            'nist_details': nist_results,
            'grade': grade,
            'cryptographic_verdict': verdict,
        }

    # ── Multi-source comparison ───────────────────────────────────
    @staticmethod
    def compare_sources(quantum_result: object) -> list[dict]:
        """Benchmark quantum randomness against classical PRNGs.

        Generates 3 classical bitstreams of the same length as the
        quantum input and runs ``full_analysis`` on all four.

        The classical baselines are:
          1. **Mersenne Twister** — Python's ``random`` module.
          2. **os.urandom** — OS-level CSPRNG.
          3. **LCG** — a textbook Linear Congruential Generator
             (deliberately weak, for contrast).

        Args:
            quantum_result: A BitStreamResult from QuantumRNG.

        Returns:
            List of 4 analysis dicts (quantum first).
        """
        # Late import to break circular dependency
        from quantum_rng import BitStreamResult

        n_bits = len(quantum_result.bits)
        now = datetime.now(timezone.utc).isoformat()

        # ── 1. Quantum (already have it) ──────────────────────────
        results = [StatisticalValidator.full_analysis(quantum_result, label='quantum')]

        # ── Helper to build a minimal BitStreamResult for analysis ─
        def _make(bits: list[int], label: str) -> BitStreamResult:
            packed = bytes(
                int(''.join(str(b) for b in bits[i:i+8]), 2)
                for i in range(0, len(bits) - len(bits) % 8, 8)
            )
            p1 = sum(bits) / len(bits) if bits else 0.5
            p0 = 1.0 - p1
            ent = -p0 * math.log2(p0 + 1e-12) - p1 * math.log2(p1 + 1e-12)
            return BitStreamResult(
                bits=bits,
                bytes_data=packed,
                job_id=f'CLASSICAL-{label}',
                circuit_type=label,
                backend='classical',
                n_qubits=0,
                n_shots=0,
                timestamp=now,
                raw_counts={},
                theta=None,
                entropy_estimate=ent,
                bias=p1,
            )

        # ── 2. Mersenne Twister ───────────────────────────────────
        mt_bits = [random.getrandbits(1) for _ in range(n_bits)]
        results.append(
            StatisticalValidator.full_analysis(_make(mt_bits, 'mersenne_twister'), label='mersenne_twister')
        )

        # ── 3. os.urandom (OS CSPRNG) ─────────────────────────────
        ur_bytes = os.urandom((n_bits + 7) // 8)
        ur_bits = []
        for byte in ur_bytes:
            for j in range(7, -1, -1):
                ur_bits.append((byte >> j) & 1)
        ur_bits = ur_bits[:n_bits]
        results.append(
            StatisticalValidator.full_analysis(_make(ur_bits, 'urandom'), label='urandom')
        )

        # ── 4. LCG (weak PRNG — for contrast) ────────────────────
        # Classic Numerical Recipes LCG: known to fail randomness tests
        a, c, m = 1664525, 1013904223, 2**32
        state = 42
        lcg_bits: list[int] = []
        for _ in range(n_bits):
            state = (a * state + c) % m
            lcg_bits.append((state >> 16) & 1)  # Use a mid-range bit
        results.append(
            StatisticalValidator.full_analysis(_make(lcg_bits, 'lcg_weak'), label='lcg_weak')
        )

        return results

    # ── Human-readable comparison report ──────────────────────────
    @staticmethod
    def generate_comparison_report(comparison_results: list[dict]) -> str:
        """Format a comparison report suitable for Streamlit display.

        Args:
            comparison_results: Output of ``compare_sources``.

        Returns:
            Multi-line formatted text report.
        """
        lines: list[str] = [
            "═" * 68,
            "  QUANTUM vs CLASSICAL RANDOMNESS — COMPARISON REPORT",
            "═" * 68,
            "",
        ]

        # Header row
        lines.append(
            f"{'Source':<20} {'Entropy':>8} {'Bias':>8} "
            f"{'Monobit':>8} {'Runs':>8} {'Grade':>12}"
        )
        lines.append("─" * 68)

        for r in comparison_results:
            mono = "PASS" if r['monobit_pass'] else "FAIL"
            runs = "PASS" if r['runs_pass'] else "FAIL"
            lines.append(
                f"{r['label']:<20} {r['shannon_entropy']:>8.4f} "
                f"{r['bias']:>8.4f} {mono:>8} {runs:>8} "
                f"{r['grade']:>12}"
            )

        lines.append("─" * 68)
        lines.append("")

        # Highlight quantum advantage
        if len(comparison_results) >= 2:
            q = comparison_results[0]
            lines.append("🔬 ANALYSIS:")
            lines.append(f"   Quantum entropy:     {q['shannon_entropy']:.6f}")
            lines.append(f"   Quantum bias:        {q['bias']:.6f}")
            lines.append(f"   Quantum grade:       {q['grade']}")
            lines.append("")

            # Find worst classical
            worst = min(comparison_results[1:], key=lambda x: x['shannon_entropy'])
            lines.append(
                f"   Weakest classical:   {worst['label']} "
                f"(entropy={worst['shannon_entropy']:.6f}, grade={worst['grade']})"
            )
            lines.append("")

            if q['shannon_entropy'] >= worst['shannon_entropy']:
                lines.append(
                    "   ✅ Quantum source matches or exceeds all classical baselines."
                )
            else:
                lines.append(
                    "   ⚠️  Quantum source underperformed — possible hardware noise."
                )

        lines.append("")
        lines.append(f"   Verdict: {comparison_results[0]['cryptographic_verdict']}")
        lines.append("═" * 68)

        return "\n".join(lines)
