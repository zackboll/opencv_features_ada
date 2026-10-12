// SPDX-License-Identifier: Apache-2.0
// Research only: exact upstream expressions and real OpenCV cvRound/ORB.
#include <opencv2/core.hpp>
#include <opencv2/core/ocl.hpp>
#include <opencv2/core/version.hpp>
#if CV_VERSION_MAJOR == 4
#include <opencv2/features2d.hpp>
#else
#include <opencv2/features.hpp>
#endif
#include <algorithm>
#include <cassert>
#include <cfenv>
#include <cfloat>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <set>

static_assert(sizeof(int) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24);
static_assert(DBL_MANT_DIG == 53 && std::numeric_limits<float>::is_iec559);
constexpr int maximum = INT32_MAX / 2;

void check(int nfeatures, int nlevels) {
    const double scaleFactor = 1.2f;
    float factor = (float)(1.0 / scaleFactor);
    float ndesiredFeaturesPerScale = nfeatures*(1 - factor)/
        (1 - (float)std::pow((double)factor, (double)nlevels));
    assert(std::isfinite(ndesiredFeaturesPerScale) && ndesiredFeaturesPerScale >= 0);
    std::int64_t sumFeatures = 0;
    int first = nfeatures;
    int previous = nfeatures;
    for (int level = 0; level < nlevels - 1; ++level) {
        const int target = cvRound(ndesiredFeaturesPerScale);
        assert(target >= 0 && target <= previous && target <= nfeatures);
        if (level == 0) first = target;
        sumFeatures += target;  // wider shadow detects overflow before native int
        assert(sumFeatures <= INT32_MAX);
        assert(std::int64_t(target) * 2 <= INT32_MAX);
        previous = target;
        const float old = ndesiredFeaturesPerScale;
        ndesiredFeaturesPerScale *= factor;
        assert(ndesiredFeaturesPerScale >= 0 && ndesiredFeaturesPerScale <= old);
    }
    const auto difference = std::int64_t(nfeatures) - sumFeatures;
    assert(difference >= INT32_MIN && difference <= INT32_MAX);
    const auto residual = std::max(difference, std::int64_t(0));
    assert(residual <= nfeatures && residual * 2 <= INT32_MAX);
    assert(std::int64_t(first) * nlevels <= INT32_MAX);
    if (nlevels > 1) {
        assert(std::int64_t(first) * nlevels * 100 <= 185LL*nfeatures + 800);
        assert(sumFeatures * 100 <= 185LL*nfeatures + 700);
    }
}

int main() {
    assert(std::fesetround(FE_TONEAREST) == 0);
    cv::ocl::setUseOpenCL(false);
    std::cout << "OpenCV=" << CV_VERSION << " compiler=" << __VERSION__
              << " FLT_EVAL_METHOD=" << FLT_EVAL_METHOD
              << " rounding=" << std::fegetround() << '\n';
#ifdef __GLIBCXX__
    std::cout << "libstdc++=" << __GLIBCXX__ << '\n';
#endif
    const double scaleFactor = 1.2f;
    const float factor = float(1.0 / scaleFactor);
    assert(factor > .83f && factor < .84f);
    std::cout << std::hexfloat << "scale=" << scaleFactor << " factor=" << factor << '\n';
    for (int l = 1; l <= 8; ++l) {
        // Volatile arguments prevent treating the evidence as constant folding.
        volatile double base = factor, exponent = l;
        const double actual = std::pow(base, exponent);
        long double reference = 1;
        for (int k = 0; k < l; ++k) reference *= (long double)factor;
        assert(std::fabs((long double)actual - reference) < std::ldexp(1.L, -20));
        std::cout << "L=" << l << " pow=" << actual << '\n';
    }
    std::set<int> targets;
    auto add = [&](std::int64_t n) { if (n >= 1 && n <= maximum) targets.insert(int(n)); };
    for (int n = 1; n <= 4096; ++n) add(n);
    for (int p = 0; p <= 30; ++p)
        for (int delta = -257; delta <= 257; ++delta) add((1LL << p) + delta);
    // Neighborhoods around binary32 spacing changes and conversion midpoints.
    for (int p = 24; p <= 29; ++p) {
        const int spacing = 1 << (p - 23);
        for (int k = 0; k < 1024; ++k)
            for (int d = -1; d <= 1; ++d)
                add((1LL << p) + std::int64_t(k)*spacing + spacing/2 + d);
    }
    for (int d = 0; d <= 8192; ++d) add(std::int64_t(maximum) - d);
    // Candidates close to share rounding boundaries, using the actual coefficient.
    for (int l = 2; l <= 8; ++l) {
        const double c = (1-factor)/(1-float(std::pow(double(factor), double(l))));
        for (int k = 0; k < 4096; ++k) {
            const auto n = std::int64_t((k + .5) / c);
            for (int d = -2; d <= 2; ++d) add(n+d);
        }
    }
    std::mt19937_64 random(0x0112026);
    for (int i = 0; i < 100000; ++i) add(1 + random() % maximum);
    for (int n : targets) for (int l = 1; l <= 8; ++l) check(n,l);
    cv::Mat image(256, 256, CV_8UC1), descriptors;
    for (int r = 0; r < image.rows; ++r)
        for (int c = 0; c < image.cols; ++c)
            image.at<unsigned char>(r,c) = (r*37+c*17+((r/16+c/16)%2)*83+r*c%251)%256;
    for (int l = 1; l <= 8; ++l) {
        auto orb = cv::ORB::create(500, 1.2f, l, 31, 0, 2, cv::ORB::HARRIS_SCORE, 31, 20);
        assert(orb->getNLevels() == l);
        std::vector<cv::KeyPoint> points;
        orb->detectAndCompute(image, cv::noArray(), points, descriptors, false);
        assert(!points.empty() && descriptors.rows == int(points.size()));
        assert(descriptors.cols == 32 && descriptors.type() == CV_8UC1);
        for (const auto& point : points) assert(point.octave >= 0 && point.octave < l);
    }
    std::cout << "PASS targets=" << targets.size() << " levels=8 native extractions=8\n";
}
