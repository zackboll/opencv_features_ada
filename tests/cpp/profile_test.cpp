// SPDX-License-Identifier: Apache-2.0
#include "orb_profile.hpp"
#include "opencv_features_shim.h"
#include "radius_limits.hpp"
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <limits>
#include <cmath>
#include <algorithm>
using namespace opencv_features_detail;
static_assert(sizeof(opencv_features_keypoint) == 28, "C keypoint ABI size");
static_assert(offsetof(opencv_features_keypoint, octave) == 20, "C keypoint ABI offset");
static_assert(offsetof(opencv_features_keypoint, class_id) == 24, "C keypoint ABI offset");
static_assert(parameters_fit(500, 2, 0, 20), "default profile");
static_assert(image_layout_fits(256, 256), "default image");
static_assert(radius_layout_fits(1, 262145), "radius has no KNN packed row limit");
static_assert(radius_count_fits(INT32_MAX - 1, 1, INT32_MAX), "radius exact count bound");
static_assert(!radius_count_fits(INT32_MAX, 1, INT32_MAX), "radius count addition overflow");
static_assert(!radius_count_fits(0, std::size_t(INT32_MAX) + 1, INT32_MAX), "radius ABI count overflow");
static_assert(!radius_count_fits(2, 1, 2), "radius allocation count bound");
static_assert(!radius_layout_fits(std::numeric_limits<std::size_t>::max(), 2), "radius layout overflow");
int main() {
    constexpr auto hi = std::numeric_limits<std::int32_t>::max();
    constexpr auto lo = std::numeric_limits<std::int32_t>::min();
    assert(parameters_fit(1, 2, 0, 0));
    assert(parameters_fit(hi / 2, 4, 1, 255));
    assert(!parameters_fit(0, 2, 0, 20));
    assert(!parameters_fit(hi, 2, 0, 20));
    assert(!parameters_fit(hi / 2 + 1, 2, 0, 20));
    // Mirror the reviewed float distribution at the maximum accepted target.
    // This is empirical compiler evidence in addition to the review bounds.
    const float factor = float(1.0 / double(1.2f));
    float desired = (hi / 2)*(1-factor)/(1-float(std::pow(double(factor),8.0)));
    std::int64_t sum = 0;
    for (int level = 0; level < levels - 1; ++level) {
        const auto count = std::int64_t(std::lrint(desired));
        assert(count > 0 && count * 2 <= hi);
        if (level == 0) assert(count * levels <= hi);
        sum += count;
        desired *= factor;
    }
    assert(sum < hi / 2 && (hi / 2 - sum) * 2 <= hi);
    assert(!parameters_fit(500, 1, 0, 20));
    assert(!parameters_fit(500, 5, 0, 20));
    assert(!parameters_fit(500, 2, 2, 20));
    assert(!parameters_fit(500, 2, 0, -1));
    assert(!parameters_fit(500, 2, 0, 256));
    assert(image_layout_fits(2, 2));
    assert(image_layout_fits(1080, 1920));
    assert(image_layout_fits(2160, 3840));
    assert(!image_layout_fits(1, 256));
    assert(!image_layout_fits(256, 1));
    assert(!image_layout_fits(0, 0));
    assert(!image_layout_fits(lo, hi));
    assert(!image_layout_fits(hi, lo));
    assert(!image_layout_fits(hi, hi));
    assert(!image_layout_fits(hi, 2));
    assert(!image_layout_fits(2, hi));
    // Find and verify the exact admitted boundary for a fixed row count.
    std::int32_t low = 2, high = hi;
    while (std::int64_t(high) - low > 1) {
        const auto mid = std::int32_t(std::int64_t(low) + (std::int64_t(high) - low) / 2);
        if (image_layout_fits(1080, mid)) low = mid; else high = mid;
    }
    assert(image_layout_fits(1080, low));
    assert(!image_layout_fits(1080, high));
    for (int count = 2; count <= 16; ++count) {
        for (float scale : {1.1f, 1.2f, 1.5f, 2.0f}) {
            const auto cap = std::int32_t(native_int_max / (2 * count));
            assert(parameters_fit(cap, 2, 0, 20, scale, count));
            if (!(scale == 1.2f && count == 8))
                assert(!parameters_fit(cap + 1, 2, 0, 20, scale, count));
            const auto target = scale == 1.2f && count == 8 ? hi / 2 : cap;
            const float f = float(1.0 / double(scale));
            float share = target * (1-f) / (1-float(std::pow(double(f), double(count))));
            std::int64_t total = 0;
            for (int i = 0; i < count - 1; ++i) {
                const auto n = std::int64_t(std::lrint(share));
                assert(n >= 0 && n * 2 <= hi && n * count <= hi);
                total += n;
                assert(total <= hi);
                share *= f;
            }
            assert(std::max(std::int64_t(target) - total, std::int64_t(0)) * 2 <= hi);
            // Exact layout frontier, independent of native cvRound helpers.
            const auto rows = std::max(2, int(std::pow(double(scale), count-1) / 2) + 1);
            std::int32_t a = rows, b = hi;
            if (image_layout_fits(a, a, scale, count)) {
                while (std::int64_t(b) - a > 1) {
                    const auto mid = std::int32_t(std::int64_t(a) + (std::int64_t(b) - a) / 2);
                    if (image_layout_fits(rows, mid, scale, count)) a = mid; else b = mid;
                }
                assert(image_layout_fits(rows, a, scale, count));
                assert(!image_layout_fits(rows, b, scale, count));
            }
            assert(!image_layout_fits(hi, hi, scale, count));
        }
    }
    // Exact upper-level half-integer tie for scale=2, levels=4.
    assert(!image_layout_fits(4, 256, 2.0f, 4));
    assert(image_layout_fits(5, 256, 2.0f, 4));
    for (int count : {0, -1, 1, 17, hi}) {
        assert(!parameters_fit(500, 2, 0, 20, 1.2f, count));
        assert(!image_layout_fits(256, 256, 1.2f, count));
    }
    for (float scale : {0.0f, -1.0f, 1.0f, std::nextafter(1.1f, 0.0f),
                        std::nextafter(2.0f, 3.0f), std::numeric_limits<float>::quiet_NaN(),
                        std::numeric_limits<float>::infinity(), -std::numeric_limits<float>::infinity()}) {
        assert(!parameters_fit(500, 2, 0, 20, scale, 8));
        assert(!image_layout_fits(256, 256, scale, 8));
    }
    std::cout << "PASS: configured profile target/layout boundaries and compiled distribution\n";
    std::cout << "PASS: fixed-profile parameter/layout and C ABI layout tests\n";
}
