// SPDX-License-Identifier: Apache-2.0
// Research-only numerical/environment supplement; pair with the preserved R1 probe.
#include <opencv2/core.hpp>
#include <opencv2/core/version.hpp>
#include <cfenv>
#include <cfloat>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>

static void require(bool condition) {
    if (!condition) throw std::runtime_error("R2 numerical premise failed");
}

int main() {
    require(sizeof(int) == 4 && sizeof(std::size_t) == 8);
    require(FLT_RADIX == 2 && FLT_MANT_DIG == 24 && DBL_MANT_DIG == 53);
    require(FLT_EVAL_METHOD == 0 && std::numeric_limits<float>::is_iec559);
#ifdef __FAST_MATH__
    throw std::runtime_error("fast-math configuration is not qualified");
#endif
    require(std::fesetround(FE_TONEAREST) == 0);
    require(std::fegetround() == FE_TONEAREST);
    std::cout << "compiler=" << __VERSION__ << " FLT_EVAL_METHOD=" << FLT_EVAL_METHOD
              << " rounding=" << std::fegetround() << " OpenCV=" << CV_VERSION << '\n';
#ifdef _LIBCPP_VERSION
    std::cout << "libc++=" << _LIBCPP_VERSION << '\n';
#endif
#ifdef __GLIBCXX__
    std::cout << "libstdc++=" << __GLIBCXX__ << '\n';
#endif
#if defined(__SSE2__) && defined(__GNUC__)
    std::cout << "cvRound path candidate=SSE2 (verify native build/header overrides)\n";
#else
    std::cout << "cvRound path requires native header/preprocessor inspection\n";
#endif
    const double scale = 1.2f;
    const float factor = float(1.0/scale);
    require(scale == 0x1.333334p+0 && factor == 0x1.aaaaaap-1f);
    std::cout << std::hexfloat << "INPUT scale " << scale << " factor " << factor << '\n';
    for (int level = 1; level <= 8; ++level) {
        volatile double base = factor, exponent = level;
        std::cout << "POWER factor " << level << ' ' << std::pow(base, exponent) << '\n';
    }
    for (int level = 0; level < 8; ++level) {
        volatile double base = scale, exponent = level;
        const double power = std::pow(base, exponent);
        const float stored = float(power);
        require(stored >= 1 && stored < 4);
        std::cout << "POWER scale " << level << ' ' << power << '\n';
        for (int dimension : {2, 3, 31, 255, 4096, 1048575}) {
            volatile float numerator = float(dimension);
            const float old_expression = numerator/stored;
            const float inverse = 1.f/stored;
            const float new_expression = numerator*inverse;
            require(cvRound(old_expression) >= 1 && cvRound(old_expression) <= dimension);
            require(cvRound(new_expression) >= 1 && cvRound(new_expression) <= dimension);
        }
    }
    // Exact half-integral binary32 inputs, neighbors, and large in-range values.
    float previous = -1;
    int previous_integer = -1;
    for (float midpoint : {0.f, .5f, 1.5f, 2.5f, 127.5f, 4095.5f,
                           8388607.5f, 16777216.f, 536870912.f, 1073741824.f}) {
        for (float value : {std::nextafter(midpoint, -INFINITY), midpoint,
                            std::nextafter(midpoint, INFINITY)}) {
            if (value < 0) continue;
            const int rounded = cvRound(value);
            require(rounded >= 0 && std::fabs(double(rounded)-double(value)) <= 1);
            require(value >= previous && rounded >= previous_integer);
            std::cout << "ROUND " << value << ' ' << rounded << '\n';
            previous = value;
            previous_integer = rounded;
        }
    }
    for (int n : {1, 2, 3, 4096, 16777215, 16777216, 16777217, INT32_MAX/2}) {
        volatile int source = n;
        const float converted = float(source);
        require(std::fabs(double(converted)-n) <= double(n)*0x1p-23);
        std::cout << "CONVERT " << n << ' ' << converted << '\n';
    }
    std::cout << "PASS R2 numerical boundaries\nBUILD_INFORMATION\n" << cv::getBuildInformation();
}