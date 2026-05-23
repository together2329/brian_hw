#!/usr/bin/env python3
"""Minimal smoke test — no template required."""
import sys


def test_basic_math():
    assert 1 + 1 == 2, "basic arithmetic failed"


def test_string_ops():
    assert "hello".upper() == "HELLO"
    assert len("abc") == 3


def test_list_ops():
    lst = [1, 2, 3]
    lst.append(4)
    assert lst == [1, 2, 3, 4]


if __name__ == "__main__":
    test_basic_math()
    test_string_ops()
    test_list_ops()
    print("ALL TESTS PASSED")
    sys.exit(0)
