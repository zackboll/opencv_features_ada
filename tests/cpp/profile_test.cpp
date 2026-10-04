// SPDX-License-Identifier: Apache-2.0
#include "orb_profile.hpp"
#include "opencv_features_shim.h"
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <limits>
using namespace opencv_features_detail;
static_assert(sizeof(opencv_features_keypoint) == 28, "C keypoint ABI size");
static_assert(offsetof(opencv_features_keypoint, octave) == 20, "C keypoint ABI offset");
static_assert(offsetof(opencv_features_keypoint, class_id) == 24, "C keypoint ABI offset");
static_assert(parameters_fit(500, 2, 0, 20), "default profile");
static_assert(image_layout_fits(256, 256), "default image");
int main() {
    constexpr auto hi = std::numeric_limits<std::int32_t>::max();
    constexpr auto lo = std::numeric_limits<std::int32_t>::min();
    assert(parameters_fit(1, 2, 0, 0));
    assert(parameters_fit(hi / 2, 4, 1, 255));
    assert(!parameters_fit(0, 2, 0, 20));
    assert(!parameters_fit(hi, 2, 0, 20));
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
    std::cout << "PASS: fixed-profile parameter/layout and C ABI layout tests\n";
}
