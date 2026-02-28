"""Unit tests for calculator.py — these pass only when bugs are fixed."""

import pytest
from calculator import add, subtract, multiply, divide


def test_add_returns_correct_value():
    assert add(3, 4) == 7


def test_add_with_negatives():
    assert add(-2, 5) == 3


def test_subtract_returns_correct_value():
    assert subtract(10, 4) == 6


def test_subtract_negative_result():
    assert subtract(3, 8) == -5


def test_multiply_returns_correct_value():
    assert multiply(3, 4) == 12


def test_multiply_by_zero():
    assert multiply(5, 0) == 0


def test_divide_returns_correct_value():
    assert divide(10, 2) == 5.0


def test_divide_by_zero_raises():
    with pytest.raises((ValueError, ZeroDivisionError)):
        divide(5, 0)
