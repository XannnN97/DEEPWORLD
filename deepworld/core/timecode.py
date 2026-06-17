"""
Timecode — frame-based immutable timecode with SMPTE string support,
drop-frame compensation, and FCPXML rational string parsing.
"""

from __future__ import annotations

import re
from fractions import Fraction
from functools import total_ordering


_PARSE_SMPTE = re.compile(r"^(\d{1,2})[:;](\d{2})[:;](\d{2})[:;](\d{2})$")
_PARSE_RATIONAL = re.compile(r"^(\d+)/(\d+)s$")
_PARSE_SECONDS = re.compile(r"^([\d.]+)s$")
_PARSE_SRT_TIME = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")


@total_ordering
class Timecode:
    """Immutable timecode backed by total frame count.

    SMPTE notation (for display) uses the nominal integer framerate,
    while actual frame count and real-time math use the exact rational framerate.
    """

    def __init__(self, frames: int, framerate: Fraction, drop_frame: bool = False):
        if framerate.numerator < 1 or framerate.denominator < 1:
            raise ValueError(f"Invalid framerate: {framerate}")
        self._frames = int(frames)
        self.framerate = framerate
        self.drop_frame = drop_frame

    @property
    def nominal_fps(self) -> int:
        """SMPTE display uses the rounded integer framerate (24 for 23.976, 30 for 29.97)."""
        return max(1, int(round(self.framerate.numerator / self.framerate.denominator)))

    # ── Constructors ────────────────────────────────────────────

    @classmethod
    def from_smpte(
        cls,
        hh: int,
        mm: int,
        ss: int,
        ff: int,
        framerate: Fraction,
        drop_frame: bool = False,
    ) -> Timecode:
        nominal = max(1, int(round(framerate.numerator / framerate.denominator)))
        total = (hh * 3600 + mm * 60 + ss) * nominal + ff
        if drop_frame:
            total = cls._drop_frame_add(total, framerate)
        return cls(total, framerate, drop_frame)

    @classmethod
    def from_seconds(
        cls,
        seconds: float | Fraction,
        framerate: Fraction,
        drop_frame: bool = False,
    ) -> Timecode:
        frames = int(round(float(seconds) * framerate.numerator / framerate.denominator))
        return cls(frames, framerate, drop_frame)

    @classmethod
    def from_string(cls, smpte_str: str, framerate: Fraction, drop_frame: bool = False) -> Timecode:
        """Parse '01:00:00:00' or '01:00:00;00' (drop-frame semicolon)."""
        m = _PARSE_SMPTE.match(smpte_str.strip())
        if not m:
            raise ValueError(f"Cannot parse SMPTE timecode: {smpte_str!r}")
        hh, mm, ss, ff = int(m[1]), int(m[2]), int(m[3]), int(m[4])
        return cls.from_smpte(hh, mm, ss, ff, framerate, drop_frame)

    @classmethod
    def from_rational(cls, rational_str: str, framerate: Fraction) -> Timecode:
        s = rational_str.strip()
        m = _PARSE_RATIONAL.match(s)
        if m:
            seconds = Fraction(int(m[1]), int(m[2]))
        else:
            m = _PARSE_SECONDS.match(s)
            if m:
                seconds = Fraction(float(m[1])).limit_denominator(1000000)
            else:
                raise ValueError(f"Cannot parse rational timecode: {rational_str!r}")
        frames = int(round(seconds * framerate))
        return cls(frames, framerate, False)

    @classmethod
    def from_srt_time(cls, srt_str: str, framerate: Fraction = Fraction(25, 1)) -> Timecode:
        m = _PARSE_SRT_TIME.match(srt_str.strip())
        if not m:
            raise ValueError(f"Cannot parse SRT time: {srt_str!r}")
        hh, mm, ss, ms = int(m[1]), int(m[2]), int(m[3]), int(m[4])
        total_seconds = Fraction(hh * 3600 + mm * 60 + ss) + Fraction(ms, 1000)
        frames = int(round(total_seconds * framerate.numerator / framerate.denominator))
        return cls(frames, framerate, False)

    # ── Properties ──────────────────────────────────────────────

    @property
    def total_frames(self) -> int:
        return self._frames

    def _drop_frame_adjusted(self) -> int:
        if not self.drop_frame:
            return self._frames
        return self._frames + self._drop_frame_skip(self._frames, self.framerate)

    @property
    def hh(self) -> int:
        n = self._drop_frame_adjusted()
        nominal = self.nominal_fps
        total_sec = n // nominal
        return total_sec // 3600

    @property
    def mm(self) -> int:
        n = self._drop_frame_adjusted()
        nominal = self.nominal_fps
        total_sec = n // nominal
        return (total_sec % 3600) // 60

    @property
    def ss(self) -> int:
        n = self._drop_frame_adjusted()
        nominal = self.nominal_fps
        total_sec = n // nominal
        return total_sec % 60

    @property
    def ff(self) -> int:
        n = self._drop_frame_adjusted()
        nominal = self.nominal_fps
        return n % nominal

    @property
    def seconds(self) -> float:
        return self._frames * self.framerate.denominator / self.framerate.numerator

    # ── Formatting ──────────────────────────────────────────────

    def to_smpte_string(self, separator: str | None = None) -> str:
        """Return 'HH:MM:SS:FF' (non-drop) or 'HH:MM:SS;FF' (drop-frame)."""
        sep = separator or (";" if self.drop_frame else ":")
        return f"{self.hh:02d}:{self.mm:02d}:{self.ss:02d}{sep}{self.ff:02d}"

    def to_seconds_string(self) -> str:
        """Decimal seconds for SRT output."""
        return f"{self.seconds:.3f}"

    def to_fractional_string(self) -> str:
        """FCPXML-style '1001/24000s'."""
        total_sec = Fraction(self._frames * self.framerate.denominator, self.framerate.numerator)
        return f"{total_sec.numerator}/{total_sec.denominator}s"

    # ── Arithmetic ──────────────────────────────────────────────

    def __add__(self, other: Timecode) -> Timecode:
        if not isinstance(other, Timecode):
            return NotImplemented
        # Result takes the higher framerate resolution
        return Timecode(self._frames + other._frames, self.framerate, self.drop_frame)

    def __sub__(self, other: Timecode) -> Timecode:
        if not isinstance(other, Timecode):
            return NotImplemented
        return Timecode(self._frames - other._frames, self.framerate, self.drop_frame)

    def __neg__(self) -> Timecode:
        return Timecode(-self._frames, self.framerate, self.drop_frame)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timecode):
            return NotImplemented
        return self._frames == other._frames

    def __lt__(self, other: Timecode) -> bool:
        if not isinstance(other, Timecode):
            return NotImplemented
        return self._frames < other._frames

    def __hash__(self) -> int:
        return hash((self._frames, self.framerate, self.drop_frame))

    def __repr__(self) -> str:
        return f"Timecode({self.to_smpte_string()}, {float(self.framerate):.4f}fps)"

    def __str__(self) -> str:
        return self.to_smpte_string()

    # ── Drop-frame helpers ──────────────────────────────────────

    @staticmethod
    def _drop_frame_skip(frames: int, framerate: Fraction) -> int:
        """Number of frame numbers skipped in drop-frame for a given frame count.

        SMPTE drop-frame: 2 frames are dropped at the start of each minute
        except minutes 0, 10, 20, 30, 40, 50.
        Only applies to 29.97fps (30000/1001) and 59.94fps (60000/1001).
        """
        fps_f = float(framerate)
        if abs(fps_f - 29.97) > 1 and abs(fps_f - 59.94) > 1 and abs(fps_f - 30000 / 1001) > 1 and abs(fps_f - 60000 / 1001) > 1:
            return 0
        fps = int(round(fps_f))
        ten_minutes = fps * 600
        one_minute = fps * 60
        # Number of ten-minute and one-minute blocks
        ten_blocks = frames // ten_minutes
        remainder = frames % ten_minutes
        one_blocks = remainder // one_minute
        # 2 frames dropped per minute except every 10th minute
        return ten_blocks * (9 * 2) + max(0, one_blocks - 1) * 2

    @staticmethod
    def _drop_frame_add(frames: int, framerate: Fraction) -> int:
        """Reverse of _drop_frame_skip: add back frames that drop-frame skips.

        Used when constructing from SMPTE string — the string already has the
        compensation applied, so we need to reverse it to get real frame count.
        """
        fps_f = float(framerate)
        if abs(fps_f - 29.97) > 1 and abs(fps_f - 59.94) > 1 and abs(fps_f - 30000 / 1001) > 1 and abs(fps_f - 60000 / 1001) > 1:
            return 0
        fps = int(round(fps_f))
        ten_minutes_frames = fps * 600
        one_minute_frames = fps * 60
        # Approximate: estimate, then iterate
        estimate = frames
        while True:
            skipped = Timecode._drop_frame_skip(estimate, framerate)
            if estimate - skipped >= frames:
                break
            estimate += 1
        return estimate - frames
