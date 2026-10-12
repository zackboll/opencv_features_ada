#!/usr/bin/env python3
"""R2 independent, coarse absolute-error proof; does not import the R1 checker."""
from fractions import Fraction as F
from pathlib import Path
import re
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def review():
    unit = F(1, 2**23)
    error = F(1, 2**20)
    maximum = (2**31 - 1) // 2
    scale = F(5033165, 2**22)
    factor = F(13981013, 2**24)
    # The double reciprocal error (half spacing here) cannot cross the float
    # nearest-rounding cell. This checks the two-rounding computation, not only
    # the exact reciprocal rounded straight to binary32.
    reciprocal = 1 / scale
    require(factor - F(1, 2**25) < reciprocal - F(1, 2**54), 'lower reciprocal cell')
    require(reciprocal + F(1, 2**54) < factor + F(1, 2**25), 'upper reciprocal cell')
    require(F(83, 100) < factor < F(84, 100), 'factor envelope')
    require((1 + unit)**3 < 1 + error, 'three roundings fit one coarse budget')
    # Independent rational majorants, deliberately coarser than R1 coefficients.
    majorants = [F(x, 1000) for x in (580, 420, 340, 295, 265, 245, 230)]
    for level, majorant in enumerate(majorants, 2):
        power = F(84, 100)**level
        # double pow <= power+e; float cast adds <u because result is <1.
        require(power + error < 1, 'power remains below one')
        require(error + unit < 2 * error, 'pow and float conversion budget')
        # Denominator rounding absolute error <u; total uncertainty <3e.
        denominator = 1 - power - 3 * error
        require(denominator > 0, 'positive denominator')
        # Cross multiplication, without calculating R1's coefficient formula.
        require(F(17, 100) * (1 + error) < majorant * denominator,
                'coarse share majorant')
        require(level * majorant <= F(46, 25), 'uniform 1.84 slope')
        require(majorant <= F(29, 50), 'uniform .58 first-share slope')
        print(f'L={level} independent share slope < {majorant}; L*slope <= 46/25')
    # N>=3: .58N+1 <=N; N=1,2: integer target <N+1 hence <=N.
    require(F(29, 50)*3+1 <= 3, 'all N>=3')
    for n in (1, 2):
        require(F(29, 50)*n+1 < n+1, 'small integer N')
    # Lower normality bound through all seven possible recurrence stores.
    require(F(16, 100)*(1-unit)**3 * (F(83, 100)*(1-unit))**7 > F(1, 25),
            'no underflow in the shares')
    reserve = F(37, 20)*maximum + 8
    total = F(37, 20)*maximum + 7
    require(reserve == F(39728447611, 20), 'exact maximum reserve')
    require(reserve.numerator // reserve.denominator == 1986422380, 'integer floor')
    require(total.numerator // total.denominator == 1986422379, 'sum floor')
    require(reserve < 2**31 - 1, 'reserve representable')
    require(-F(17, 20)*maximum-7 > -2**31, 'residual subtraction')
    require(2*maximum == 2147483646, 'all doubled targets')
    print('PASS independent rational inequalities; reserve exact=', reserve,
          'floor=', reserve.numerator // reserve.denominator)


def check_log(path):
    text = Path(path).read_text()
    scale = F(5033165, 2**22)
    factor = F(13981013, 2**24)
    for kind, base, levels in [('factor', factor, range(1, 9)),
                               ('scale', scale, range(0, 8))]:
        entries = re.findall(rf'POWER {kind} (\d+) (0x\S+)', text)
        require([int(n) for n, _ in entries] == list(levels), 'complete power inventory')
        for n, hexadecimal in entries:
            observed = F.from_float(float.fromhex(hexadecimal))
            reference = base**int(n)
            absolute_error = abs(observed-reference)
            require(absolute_error <= F(1, 2**20), 'power exceeds qualification envelope')
            # Image-bound premise: scale >=1, and largest stored scale <4.
            if kind == 'scale':
                require((int(n) == 0 and observed == 1) or (1 < observed < 4),
                        'pyramid scale envelope')
            print(kind, n, 'reference=', reference, 'absolute_error=', absolute_error)
    require('PASS R2 numerical boundaries' in text, 'probe did not complete')
    print('PASS exact fixed-input output review:', path)


if __name__ == '__main__':
    review()
    for filename in sys.argv[1:]:
        check_log(filename)