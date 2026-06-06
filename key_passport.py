"""
key_passport.py — Task 4.8
Standalone passport module re-exporting from visual_cryptanalysis.

This keeps the deliverable list intact (the spec lists key_passport.py
as a separate file) while avoiding code duplication.
"""

from visual_cryptanalysis import generate_key_passport, _get_font  # noqa: F401

__all__ = ["generate_key_passport"]
