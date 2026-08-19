"""Re-export engine vocabulary for critic spelling checks."""

from __future__ import annotations

from app.engine.harmony_vocab import pitch_classes_for_symbol as expected_pitch_classes

__all__ = ["expected_pitch_classes"]
