"""Tests for timecode module."""

from fractions import Fraction
import pytest
from deepworld.core.timecode import Timecode


class TestTimecodeConstruction:
    def test_from_smpte_24fps(self):
        tc = Timecode.from_smpte(1, 0, 0, 0, Fraction(24, 1))
        assert tc.total_frames == 86400
        assert tc.to_smpte_string() == "01:00:00:00"

    def test_from_smpte_23976(self):
        tc = Timecode.from_smpte(0, 0, 10, 0, Fraction(24000, 1001))
        assert tc.to_smpte_string() == "00:00:10:00"

    def test_from_string(self):
        tc = Timecode.from_string("01:00:00:00", Fraction(24, 1))
        assert tc.total_frames == 86400

    def test_from_string_drop_frame(self):
        tc = Timecode.from_string("01:00:00;00", Fraction(30000, 1001), drop_frame=True)
        assert tc is not None

    def test_from_seconds(self):
        tc = Timecode.from_seconds(5.0, Fraction(24, 1))
        assert tc.total_frames == 120

    def test_from_rational(self):
        tc = Timecode.from_rational("1001/24000s", Fraction(24000, 1001))
        assert tc.total_frames == 1

    def test_from_rational_seconds(self):
        tc = Timecode.from_rational("30s", Fraction(24, 1))
        assert tc.total_frames == 720

    def test_from_srt_time(self):
        tc = Timecode.from_srt_time("00:00:05,000", Fraction(25, 1))
        assert tc.total_frames == 125

    def test_invalid_framerate(self):
        with pytest.raises(ValueError):
            Timecode(0, Fraction(0, 1))

    def test_invalid_smpte_string(self):
        with pytest.raises(ValueError):
            Timecode.from_string("not-a-timecode", Fraction(24, 1))


class TestTimecodeProperties:
    def test_hh_mm_ss_ff(self):
        tc = Timecode.from_smpte(2, 30, 15, 12, Fraction(24, 1))
        assert tc.hh == 2
        assert tc.mm == 30
        assert tc.ss == 15
        assert tc.ff == 12

    def test_seconds_property(self):
        tc = Timecode.from_smpte(0, 0, 30, 0, Fraction(24, 1))
        assert abs(tc.seconds - 30.0) < 0.01

    def test_duration_property(self):
        tc = Timecode.from_smpte(0, 0, 1, 0, Fraction(24, 1))
        assert abs(tc.seconds - 1.0) < 0.01


class TestTimecodeArithmetic:
    def test_add(self):
        a = Timecode(100, Fraction(24, 1))
        b = Timecode(50, Fraction(24, 1))
        c = a + b
        assert c.total_frames == 150

    def test_sub(self):
        a = Timecode(100, Fraction(24, 1))
        b = Timecode(50, Fraction(24, 1))
        c = a - b
        assert c.total_frames == 50

    def test_neg(self):
        tc = Timecode(100, Fraction(24, 1))
        neg = -tc
        assert neg.total_frames == -100

    def test_ordering(self):
        a = Timecode(100, Fraction(24, 1))
        b = Timecode(200, Fraction(24, 1))
        assert a < b
        assert b > a
        assert a <= Timecode(100, Fraction(24, 1))

    def test_equality(self):
        a = Timecode(100, Fraction(24, 1))
        b = Timecode(100, Fraction(24, 1))
        assert a == b

    def test_hash(self):
        a = Timecode(100, Fraction(24, 1))
        b = Timecode(100, Fraction(24, 1))
        assert hash(a) == hash(b)


class TestTimecodeFormatting:
    def test_smpte_string_non_drop(self):
        tc = Timecode.from_smpte(0, 0, 0, 5, Fraction(24, 1))
        assert tc.to_smpte_string() == "00:00:00:05"

    def test_fractional_string(self):
        tc = Timecode(1, Fraction(24000, 1001))
        s = tc.to_fractional_string()
        assert "/" in s and s.endswith("s")

    def test_to_seconds_string(self):
        tc = Timecode.from_smpte(0, 0, 5, 0, Fraction(24, 1))
        assert float(tc.to_seconds_string()) == pytest.approx(5.0, abs=0.1)
