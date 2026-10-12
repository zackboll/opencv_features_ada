#!/usr/bin/env python3
"""Exact rational conditional ORB certificate; no third-party dependencies.

This certifies inequalities, not an arbitrary C++ math implementation.
See orb-pyramid-levels-arithmetic-r1.md for the explicit preconditions.
"""
from fractions import Fraction as Q
from pathlib import Path
import re
import sys

M = 2**31 - 1
NMAX = M // 2
U = Q(1, 2**23)  # full binary32 spacing: covers directed rounding too
POW_ERROR = Q(1, 2**20)  # assumed absolute error of the DOUBLE pow result
F_LO, F_HI = Q(83, 100), Q(84, 100)
SCALE = Q(5033165, 4194304)  # nearest binary32 1.2
FACTOR = Q(13981013, 16777216)  # nearest binary32 reciprocal


def ceiling(x):
    return -(-x.numerator // x.denominator)


def main():
    assert Q(6, 5) < SCALE < Q(6, 5) * (1 + U)
    assert F_LO < (1 / SCALE) * (1 - U)
    assert (1 / SCALE) * (1 + U) < F_HI
    assert F_LO < FACTOR < F_HI
    assert 2 * NMAX == M - 1
    print("L coefficient_upper L*coefficient ceil(first@max) sum_upper reserve_upper")
    for levels in range(2, 9):
        # pow error plus conversion error to float, including upward rounding.
        power_upper = (F_HI**levels + POW_ERROR) * (1 + U)
        power_lower = (F_LO**levels - POW_ERROR) * (1 - U)
        assert 0 < power_lower < power_upper < 1
        denominator_lower = (1 - power_upper) * (1 - U)
        # N->float, numerator multiply, division: three upward relative errors.
        coefficient = Q(17, 100) * (1 + U)**3 / denominator_lower
        assert coefficient < Q(578, 1000)
        assert levels * coefficient < Q(185, 100)
        # cvRound error <=1 under the qualified monotone rounding paths.
        first_upper = ceiling(coefficient * NMAX + 1)
        sum_upper = ceiling(Q(185, 100) * NMAX + levels - 1)
        reserve_upper = ceiling(Q(185, 100) * NMAX + levels)
        assert first_upper < M
        assert sum_upper < M and reserve_upper < M
        # For N>=3, c*N+1<=N. N=1,2 use integer-valued rounded target.
        assert coefficient * 3 + 1 <= 3
        for n in (1, 2):
            assert coefficient * n + 1 < n + 1
        # Residual in [0,N], each preceding target in [0,N].
        assert 2 * NMAX < M
        subtraction_lower = -Q(85, 100) * NMAX - (levels - 1)
        assert subtraction_lower > -2**31
        print(levels, f"{float(coefficient):.12f}",
              f"{float(levels * coefficient):.12f}", first_upper,
              sum_upper, reserve_upper)
    print("PASS: exact rational conditional certificate; E=8 for Harris reserve")
    print("uniform sum <= ceil(1.85*Nmax+7) =", ceiling(Q(185, 100)*NMAX+7))
    print("uniform reserve <= ceil(1.85*Nmax+8) =", ceiling(Q(185, 100)*NMAX+8))
    print("residual subtraction >=", -ceiling(Q(85, 100)*NMAX+7))
    for argument in sys.argv[1:]:
        text = Path(argument).read_text()
        entries = re.findall(r"L=(\d+) pow=(0x[^\s]+)", text)
        assert len(entries) == 8
        for level, hexadecimal in entries:
            actual = Q.from_float(float.fromhex(hexadecimal))
            assert abs(actual - FACTOR**int(level)) < POW_ERROR
        assert "PASS targets=" in text
        print("PASS: exact rational pow-output check:", argument)


if __name__ == "__main__":
    main()
