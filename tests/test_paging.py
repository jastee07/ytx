from __future__ import annotations

from ytx.utils.paging import clamp_page_size


class TestClampPageSize:
    def test_normal_value(self):
        assert clamp_page_size(25) == 25

    def test_zero_returns_one(self):
        assert clamp_page_size(0) == 1

    def test_negative_returns_one(self):
        assert clamp_page_size(-5) == 1

    def test_above_max_clamped(self):
        assert clamp_page_size(100) == 50

    def test_at_max_returns_max(self):
        assert clamp_page_size(50) == 50

    def test_custom_max_page_size(self):
        assert clamp_page_size(30, max_page_size=20) == 20

    def test_one_is_valid(self):
        assert clamp_page_size(1) == 1
