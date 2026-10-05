// SPDX-License-Identifier: Apache-2.0
#ifndef OPENCV_FEATURES_RADIUS_LIMITS_HPP
#define OPENCV_FEATURES_RADIUS_LIMITS_HPP
#include <cstddef>
#include <cstdint>
#include <limits>
namespace opencv_features_detail {
// radiusMatch's K=0 batchDistance creates Query.rows x Train.rows CV_32S,
// then CV_32F. Check each allocation's byte arithmetic, not a speculative cap.
constexpr bool radius_layout_fits(std::size_t query, std::size_t train) noexcept {
    return train == 0 || query <= std::numeric_limits<std::size_t>::max() / sizeof(int32_t) / train;
}
constexpr bool radius_count_fits(std::size_t count, std::size_t additional,
                                 std::size_t allocation_limit) noexcept {
    const auto limit = allocation_limit < std::size_t(INT32_MAX) ? allocation_limit : std::size_t(INT32_MAX);
    return count <= limit && additional <= limit - count;
}
}
#endif