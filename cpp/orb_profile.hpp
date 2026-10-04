// SPDX-License-Identifier: Apache-2.0
#ifndef OPENCV_FEATURES_ORB_PROFILE_HPP
#define OPENCV_FEATURES_ORB_PROFILE_HPP
#include <cstdint>
#include <limits>

namespace opencv_features_detail {
constexpr std::int64_t native_int_max = std::numeric_limits<std::int32_t>::max();
constexpr int levels = 8;
constexpr int border = 32; // max(edgeThreshold=31, patch radius, Harris radius)+1

constexpr bool parameters_fit(std::int32_t maximum_features, std::int32_t tuple,
                              std::int32_t score, std::int32_t threshold) noexcept {
    return maximum_features > 0 && maximum_features <= native_int_max / 2 &&
           tuple >= 2 && tuple <= 4 && (score == 0 || score == 1) &&
           threshold >= 0 && threshold <= 255;
}

// Conservative fixed-profile envelope, not OpenCV's exact acceptance set.
// Eight levels, firstLevel=0 and scale>1 imply every level is no larger
// than the source. Stacking all padded levels vertically bounds the packed
// buffer height; aligned width bounds its stride. This covers signed native
// packed-plane offsets and the default fixed-radius row-offset products.
// int64 arithmetic remains safe for all int32 inputs, including malformed
// raw ABI inputs. Division avoids multiplying the two large bounds.
constexpr bool image_layout_fits(std::int32_t rows, std::int32_t columns) noexcept {
    if (rows < 2 || columns < 2) return false;
    const std::int64_t width = (std::int64_t(columns) + 2 * border + 15) & ~std::int64_t(15);
    const std::int64_t height = levels * (std::int64_t(rows) + 2 * border);
    return width <= native_int_max && height <= native_int_max &&
           width <= native_int_max / height;
}
} // namespace opencv_features_detail
#endif
