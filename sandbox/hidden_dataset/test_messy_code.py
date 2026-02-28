import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from messy_code import f


def test_f_returns_true_in_range():
    assert f(50) is True


def test_f_returns_true_boundary_low():
    assert f(1) is True


def test_f_returns_true_boundary_high():
    assert f(99) is True


def test_f_returns_false_for_zero():
    assert f(0) is False


def test_f_returns_false_for_negative():
    assert f(-5) is False


def test_f_returns_false_above_100():
    assert f(100) is False


def test_f_returns_false_far_above():
    assert f(200) is False
