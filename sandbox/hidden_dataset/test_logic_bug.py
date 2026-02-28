import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from logic_bug import count_down


def test_count_down_decrements(monkeypatch):
    """count_down(5) should print 5, 4, 3, 2, 1 and stop."""
    calls = []

    def fake_print(n):
        calls.append(n)
        if len(calls) > 20:
            raise RuntimeError("Infinite loop detected: n is not decreasing")

    monkeypatch.setattr("builtins.print", fake_print)
    count_down(5)
    assert calls == [5, 4, 3, 2, 1], f"Expected [5,4,3,2,1] but got {calls}"


def test_count_down_single(monkeypatch):
    """count_down(1) should print just 1."""
    calls = []

    def fake_print(n):
        calls.append(n)
        if len(calls) > 10:
            raise RuntimeError("Infinite loop detected")

    monkeypatch.setattr("builtins.print", fake_print)
    count_down(1)
    assert calls == [1]


def test_count_down_zero(monkeypatch):
    """count_down(0) should print nothing."""
    calls = []
    monkeypatch.setattr("builtins.print", lambda n: calls.append(n))
    count_down(0)
    assert calls == []
