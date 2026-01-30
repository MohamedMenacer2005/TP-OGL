import os
import sys


def bad_func(x, y):
    z = x + y
    return z


a = 5
b = 10
result = bad_func(a, b)
print(result)
