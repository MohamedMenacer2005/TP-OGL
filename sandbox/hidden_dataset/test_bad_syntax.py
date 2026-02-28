import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bad_syntax import calculate_sum


def test_calculate_sum_positive():
    assert calculate_sum(2, 3) == 5


def test_calculate_sum_zeros():
    assert calculate_sum(0, 0) == 0


def test_calculate_sum_negative():
    assert calculate_sum(-1, -4) == -5


def test_calculate_sum_mixed():
    assert calculate_sum(10, -3) == 7
