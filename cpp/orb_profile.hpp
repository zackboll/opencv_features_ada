// SPDX-License-Identifier: Apache-2.0
#ifndef OPENCV_FEATURES_ORB_PROFILE_HPP
#define OPENCV_FEATURES_ORB_PROFILE_HPP
#include <cstdint>
#include <cmath>
#include <limits>

namespace opencv_features_detail {
constexpr std::int64_t native_int_max = std::numeric_limits<std::int32_t>::max();
constexpr int levels = 8;
constexpr int border = 32; // max(edgeThreshold=31, patch radius, Harris radius)+1

inline bool pyramid_fits(float scale, std::int32_t count) noexcept {
    return std::isfinite(scale) && scale >= 1.1f && scale <= 2.0f &&
           count >= 2 && count <= 16;
}

inline bool parameters_fit(std::int32_t maximum_features, std::int32_t tuple,
                           std::int32_t score, std::int32_t threshold,
                           float scale, std::int32_t count) noexcept;

constexpr bool parameters_fit(std::int32_t maximum_features, std::int32_t tuple,
                              std::int32_t score, std::int32_t threshold) noexcept {
    // All three reviewed tags reserve nfeaturesPerLevel[0]*2 even for FAST;
    // Harris also retains 2*featuresNum. See docs/orb-source-review.md.
    return maximum_features > 0 && maximum_features <= native_int_max / 2 &&
           tuple >= 2 && tuple <= 4 && (score == 0 || score == 1) &&
           threshold >= 0 && threshold <= 255;
}

// Conservative fixed-profile envelope, not OpenCV's exact acceptance set.
// Eight levels, firstLevel=0 and scale>1 imply every level is no larger
// than the source. Stacking all padded levels vertically bounds the packed
// buffer height; aligned width bounds its stride. This covers signed native
// packed-plane offsets and the default fixed-radius row-offset products.
// It also bounds the sum of eight level pixel counts (FAST candidates),
// including response ties: the requested feature target is NOT a count bound.
// int64 arithmetic remains safe for all int32 inputs, including malformed
// raw ABI inputs. Division avoids multiplying the two large bounds.
constexpr bool image_layout_fits(std::int32_t rows, std::int32_t columns) noexcept {
    if (rows < 2 || columns < 2) return false;
    const std::int64_t width = (std::int64_t(columns) + 2 * border + 15) & ~std::int64_t(15);
    const std::int64_t height = levels * (std::int64_t(rows) + 2 * border);
    return width <= native_int_max && height <= native_int_max &&
           width <= native_int_max / height;
}

inline bool parameters_fit(std::int32_t maximum_features, std::int32_t tuple,
                           std::int32_t score, std::int32_t threshold,
                           float scale, std::int32_t count) noexcept {
    if (!parameters_fit(maximum_features, tuple, score, threshold) ||
        !pyramid_fits(scale, count)) return false;
    // Retain the independently reviewed legacy target acceptance. Otherwise
    // each rounded geometric share is < 2*N, so both firstShare*L and the
    // sum of L shares fit. Doubling also fits because L >= 2. The generous
    // factor two absorbs binary32 arithmetic and integer rounding margins.
    return (scale == 1.2f && count == levels) ||
           maximum_features <= native_int_max / (2 * std::int64_t(count));
}

inline bool image_layout_fits(std::int32_t rows, std::int32_t columns,
                              float scale, std::int32_t count) noexcept {
    if (rows < 2 || columns < 2 || !pyramid_fits(scale, count)) return false;
    const std::int64_t width = (std::int64_t(columns) + 2 * border + 15) & ~std::int64_t(15);
    const std::int64_t height = std::int64_t(count) * (std::int64_t(rows) + 2 * border);
    if (width > native_int_max || height > native_int_max ||
        width > native_int_max / height) return false;
    // 4.1/4.4 divide by the float scale; later versions multiply by its
    // float reciprocal. Strictly above the half-integer tie ensures cvRound
    // cannot produce zero in either implementation. Check every level before
    // OpenCV allocates or invokes resize, including masks and blank images.
    for (int level = 0; level < count; ++level) {
        const float power = float(std::pow(double(scale), double(level)));
        const float inverse = 1.0f / power;
        if (!(float(rows) / power > 0.5f && float(columns) / power > 0.5f &&
              float(rows) * inverse > 0.5f && float(columns) * inverse > 0.5f)) return false;
    }
    return true;
}
} // namespace opencv_features_detail
#endif
