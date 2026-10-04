// SPDX-License-Identifier: Apache-2.0
#ifndef OPENCV_FEATURES_BUILDING
#define OPENCV_FEATURES_BUILDING
#endif
#include "opencv_features_shim.h"
#include "orb_profile.hpp"
#include "opencv_core_module_bridge.hpp"
#include <opencv2/core/version.hpp>
#if CV_VERSION_MAJOR == 4
# include <opencv2/features2d.hpp>
#elif CV_VERSION_MAJOR == 5
# include <opencv2/features.hpp>
#else
# error "Review Features compatibility before using another OpenCV major version"
#endif
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdio>
#include <limits>
#include <memory>
#include <new>
#include <stdexcept>
#include <type_traits>
#include <vector>

static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559,
              "The ABI requires IEEE binary32 float");
static_assert(sizeof(int) == 4, "OpenCV native integer contract requires 32-bit int");
static_assert(std::is_standard_layout<opencv_features_keypoint>::value,
              "C keypoint must have a standard layout");
static_assert(sizeof(opencv_features_keypoint) == 28, "Unexpected C keypoint ABI");
static_assert(alignof(opencv_features_keypoint) == 4, "Unexpected keypoint alignment");
static_assert(offsetof(opencv_features_keypoint, x) == 0 &&
              offsetof(opencv_features_keypoint, y) == 4 &&
              offsetof(opencv_features_keypoint, size) == 8 &&
              offsetof(opencv_features_keypoint, angle) == 12 &&
              offsetof(opencv_features_keypoint, response) == 16 &&
              offsetof(opencv_features_keypoint, octave) == 20 &&
              offsetof(opencv_features_keypoint, class_id) == 24, "Unexpected keypoint offsets");

struct opencv_features_orb_handle { cv::Ptr<cv::ORB> detector; };
struct opencv_features_result_handle {
    std::vector<opencv_features_keypoint> points;
    cv::Mat descriptors; // private temporary, never an application-owned wrapper
};
struct opencv_features_match_result_handle {
    std::vector<opencv_features_descriptor_match> matches;
};
struct opencv_features_knn2_result_handle {
    std::vector<opencv_features_knn2_match> matches;
};
static_assert(std::is_standard_layout<opencv_features_knn2_match>::value,
              "C KNN2 match must have a standard layout");
static_assert(std::is_standard_layout<opencv_features_descriptor_match>::value,
              "C descriptor match must have a standard layout");

namespace {
thread_local char error_text[1024] = "";
#ifdef OPENCV_FEATURES_TEST_HOOKS
// Dedicated test builds only. No control symbol exists in the production shim.
thread_local int failure_stage = 0, failure_kind = 0;
void checkpoint(int stage) {
    if (stage != failure_stage) return;
    const int kind = failure_kind;
    failure_stage = failure_kind = 0; // one-shot, including after exceptions
    switch (kind) {
    case 1: throw std::invalid_argument("injected invalid argument");
    case 2: throw cv::Exception(cv::Error::StsError, "injected native exception",
                              "checkpoint", __FILE__, __LINE__);
    case 3: throw std::bad_alloc();
    case 4: throw std::runtime_error("injected standard exception");
    default: throw 0; // exercise the unknown-exception barrier, no memory corruption
    }
}
#else
void checkpoint(int) noexcept {}
#endif
void require(bool condition, const char *message) {
    if (!condition) throw std::invalid_argument(message);
}
void error(const char *message) noexcept {
    std::snprintf(error_text, sizeof(error_text), "%s", message ? message : "unknown error");
}
template<class Function>
opencv_features_status guarded(Function &&function) noexcept {
    error_text[0] = '\0';
    try { function(); return OPENCV_FEATURES_OK; }
    catch (const std::invalid_argument &e) { error(e.what()); return OPENCV_FEATURES_INVALID_ARGUMENT; }
    catch (const cv::Exception &e) { error(e.what()); return OPENCV_FEATURES_NATIVE_ERROR; }
    catch (const std::bad_alloc &e) { error(e.what()); return OPENCV_FEATURES_ALLOCATION_ERROR; }
    catch (const std::exception &e) { error(e.what()); return OPENCV_FEATURES_INTERNAL_ERROR; }
    catch (...) { error("unknown C++ exception"); return OPENCV_FEATURES_INTERNAL_ERROR; }
}
const cv::Mat &input(const opencv_core_mat_handle *handle) {
    require(handle != nullptr, "null Core input handle");
    const cv::Mat *mat = nullptr;
    require(opencv_core_module_input_mat(handle, &mat) == OPENCV_CORE_OK && mat != nullptr,
            "Core rejected the input handle");
    require(!mat->empty() && mat->dims == 2 && mat->type() == CV_8UC1,
            "ORB requires a nonempty two-dimensional UInt8 C1 image");
    return *mat;
}
const cv::Mat &descriptors(const opencv_core_mat_handle *handle) {
    require(handle != nullptr, "null descriptor Core input handle");
    const cv::Mat *mat = nullptr;
    require(opencv_core_module_input_mat(handle, &mat) == OPENCV_CORE_OK && mat != nullptr,
            "Core rejected descriptor input handle");
    require(mat->empty() || (mat->dims == 2 && mat->type() == CV_8UC1 &&
            mat->cols == 32 && mat->rows > 0), "expected 2-D UInt8 C1 Nx32 ORB descriptors");
    return *mat;
}
bool finite_keypoint(const cv::KeyPoint &p, const cv::Mat &image) noexcept {
    return std::isfinite(p.pt.x) && std::isfinite(p.pt.y) &&
           std::isfinite(p.size) && std::isfinite(p.angle) && std::isfinite(p.response) &&
           p.pt.x >= 0 && p.pt.y >= 0 && p.pt.x < image.cols && p.pt.y < image.rows &&
           p.size > 0 && p.octave >= 0 && p.octave < opencv_features_detail::levels;
}
void extract(opencv_features_orb_handle *handle, const opencv_core_mat_handle *image_handle,
             const opencv_core_mat_handle *mask_handle,
             opencv_features_result_handle **out_result, int32_t *out_count) {
    require(out_result != nullptr && out_count != nullptr, "null extraction output");
    require(handle != nullptr && !handle->detector.empty(), "null or unready ORB detector");
    const cv::Mat &source = input(image_handle);
    require(opencv_features_detail::image_layout_fits(source.rows, source.cols),
            "image is outside the fixed-profile ORB arithmetic envelope");
    cv::Mat mask;
    if (mask_handle != nullptr) {
        const cv::Mat &selection = input(mask_handle);
        require(selection.size() == source.size(), "mask geometry does not match image");
        mask = selection.clone();
    }
    const cv::Mat image = source.clone(); // isolated ROI, no retained input header
    checkpoint(2);
    auto result = std::make_unique<opencv_features_result_handle>();
    std::vector<cv::KeyPoint> keypoints;
    handle->detector->detectAndCompute(image, mask, keypoints, result->descriptors, false);
    checkpoint(3);
    require(keypoints.size() <= std::size_t(std::numeric_limits<int32_t>::max()),
            "native keypoint count is not representable");
    if (keypoints.empty()) {
        require(result->descriptors.empty(), "unexpected descriptors without keypoints");
        result->descriptors.release();
    } else {
        require(result->descriptors.dims == 2 && result->descriptors.type() == CV_8UC1 &&
                result->descriptors.rows == static_cast<int>(keypoints.size()) &&
                result->descriptors.cols == 32,
                "native ORB descriptor/keypoint pairing is inconsistent");
    }
    result->points.reserve(keypoints.size());
    checkpoint(4);
    for (const cv::KeyPoint &point : keypoints) {
        require(finite_keypoint(point, image), "invalid native ORB keypoint");
        result->points.push_back({point.pt.x, point.pt.y, point.size, point.angle,
                                  point.response, point.octave, point.class_id});
    }
    *out_count = static_cast<int32_t>(result->points.size());
    *out_result = result.release(); // publish only a complete, validated result
}
} // namespace

extern "C" {
#ifdef OPENCV_FEATURES_TEST_HOOKS
void opencv_features_test_fail(int stage, int kind) {
    failure_stage = stage;
    failure_kind = kind;
}
#endif
const char *opencv_features_last_error(void) { return error_text; }
const char *opencv_features_native_version(void) { return CV_VERSION; }
const char *opencv_features_native_backend(void) {
#if CV_VERSION_MAJOR == 4
    return "features2d";
#else
    return "features";
#endif
}
opencv_features_status opencv_features_orb_create(
    int32_t maximum_features, int32_t tuple, int32_t score, int32_t fast_threshold,
    opencv_features_orb_handle **out_handle) {
    if (out_handle != nullptr) *out_handle = nullptr;
    return guarded([&] {
        require(out_handle != nullptr, "null detector output");
        require(opencv_features_detail::parameters_fit(maximum_features, tuple, score, fast_threshold),
                "ORB configuration is outside the supported profile");
        checkpoint(1);
        auto result = std::make_unique<opencv_features_orb_handle>();
        result->detector = cv::ORB::create(maximum_features, 1.2f, 8, 31, 0, tuple,
                            score == 0 ? cv::ORB::HARRIS_SCORE : cv::ORB::FAST_SCORE, 31,
                            fast_threshold);
        require(!result->detector.empty(), "native ORB factory returned no detector");
        *out_handle = result.release();
    });
}
void opencv_features_orb_destroy(opencv_features_orb_handle *handle) {
    try { delete handle; } catch (...) {} // never throw from Ada finalization
}
opencv_features_status opencv_features_orb_extract(
    opencv_features_orb_handle *handle, const opencv_core_mat_handle *image,
    opencv_features_result_handle **out_result, int32_t *out_count) {
    if (out_result != nullptr) *out_result = nullptr;
    if (out_count != nullptr) *out_count = 0;
    return guarded([&] { extract(handle, image, nullptr, out_result, out_count); });
}
opencv_features_status opencv_features_orb_extract_masked(
    opencv_features_orb_handle *handle, const opencv_core_mat_handle *image,
    const opencv_core_mat_handle *mask,
    opencv_features_result_handle **out_result, int32_t *out_count) {
    if (out_result != nullptr) *out_result = nullptr;
    if (out_count != nullptr) *out_count = 0;
    return guarded([&] {
        require(mask != nullptr, "masked extraction requires a mask handle");
        extract(handle, image, mask, out_result, out_count);
    });
}
opencv_features_status opencv_features_result_point(
    const opencv_features_result_handle *handle, int32_t index,
    opencv_features_keypoint *out_point) {
    if (out_point != nullptr) *out_point = {};
    return guarded([&] {
        require(handle != nullptr && out_point != nullptr, "null keypoint argument");
        require(index >= 0 && std::size_t(index) < handle->points.size(), "keypoint index out of range");
        checkpoint(5);
        *out_point = handle->points[std::size_t(index)];
    });
}
opencv_features_status opencv_features_result_descriptors(
    const opencv_features_result_handle *handle, opencv_core_mat_handle *destination) {
    return guarded([&] {
        require(handle != nullptr && destination != nullptr, "null descriptor argument");
        cv::Mat *output = nullptr;
        require(opencv_core_module_output_mat(destination, &output) == OPENCV_CORE_OK && output != nullptr,
                "Core rejected descriptor output (external views are not rebindable)");
        checkpoint(6);
        *output = handle->descriptors; // retain storage in the actual Core-owned header
    });
}
void opencv_features_result_destroy(opencv_features_result_handle *handle) {
    try { delete handle; } catch (...) {}
}
opencv_features_status opencv_features_bf_match(
    const opencv_core_mat_handle *query_handle, const opencv_core_mat_handle *train_handle,
    int32_t norm, int32_t mode,
    opencv_features_match_result_handle **out_result, int32_t *out_count) {
    if (out_result != nullptr) *out_result = nullptr;
    if (out_count != nullptr) *out_count = 0;
    return guarded([&] {
        require(out_result != nullptr && out_count != nullptr, "null match output");
        require(norm == OPENCV_FEATURES_HAMMING || norm == OPENCV_FEATURES_HAMMING2,
                "invalid binary descriptor norm selector");
        require(mode == OPENCV_FEATURES_NEAREST || mode == OPENCV_FEATURES_MUTUAL_NEAREST,
                "invalid matching mode selector");
        const cv::Mat &query = descriptors(query_handle), &train = descriptors(train_handle);
        // BFMatcher packs train rows in 18 bits; reverse batchDistance does not.
        require(train.empty() || train.rows < (1 << 18), "train descriptor rows must be <= 262143");
        checkpoint(7);
        auto result = std::make_unique<opencv_features_match_result_handle>();
        std::vector<cv::DMatch> native;
        if (!query.empty() && !train.empty()) {
            auto matcher = cv::BFMatcher::create(norm == OPENCV_FEATURES_HAMMING ?
                            cv::NORM_HAMMING : cv::NORM_HAMMING2,
                            mode == OPENCV_FEATURES_MUTUAL_NEAREST);
            require(!matcher.empty(), "native matcher factory returned no matcher");
            matcher->match(query, train, native);
        }
        checkpoint(8);
        require(native.size() <= std::size_t(std::numeric_limits<int32_t>::max()),
                "native match count is not representable");
        const auto expected = query.empty() || train.empty() ? std::size_t(0) : std::size_t(query.rows);
        require(mode == OPENCV_FEATURES_NEAREST ? native.size() == expected : native.size() <= expected,
                "invalid native match count");
        std::sort(native.begin(), native.end(), [](const cv::DMatch &a, const cv::DMatch &b) {
            return a.queryIdx < b.queryIdx;
        });
        const int maximum = norm == OPENCV_FEATURES_HAMMING ? 256 : 128;
        int previous = -1;
        // Cross-check guarantees train uniqueness as well as query uniqueness.
        std::vector<unsigned char> seen(mode == OPENCV_FEATURES_MUTUAL_NEAREST && !train.empty() ?
                                       std::size_t(train.rows) : 0, 0);
        for (const auto &match : native) {
            require(match.imgIdx == 0 && match.queryIdx >= 0 && match.queryIdx < query.rows &&
                    match.trainIdx >= 0 && match.trainIdx < train.rows &&
                    match.queryIdx > previous && std::isfinite(match.distance) &&
                    match.distance >= 0 && match.distance <= maximum &&
                    std::trunc(match.distance) == match.distance, "invalid native binary match");
            previous = match.queryIdx;
            if (!seen.empty()) {
                require(!seen[std::size_t(match.trainIdx)], "duplicate mutual-nearest train index");
                seen[std::size_t(match.trainIdx)] = 1;
            }
        }
        result->matches.reserve(native.size());
        for (const auto &match : native)
            result->matches.push_back({match.queryIdx, match.trainIdx, static_cast<int32_t>(match.distance)});
        checkpoint(9); // RAII cleans validated storage if publication fails
        *out_count = static_cast<int32_t>(result->matches.size());
        *out_result = result.release();
    });
}
opencv_features_status opencv_features_match_result_get(
    const opencv_features_match_result_handle *handle, int32_t index,
    opencv_features_descriptor_match *out_match) {
    if (out_match != nullptr) *out_match = {};
    return guarded([&] {
        require(handle != nullptr && out_match != nullptr, "null match result argument");
        require(index >= 0 && std::size_t(index) < handle->matches.size(), "match index out of range");
        checkpoint(10);
        *out_match = handle->matches[std::size_t(index)];
    });
}
void opencv_features_match_result_destroy(opencv_features_match_result_handle *handle) {
    try { delete handle; } catch (...) {}
}
opencv_features_status opencv_features_bf_knn2(
    const opencv_core_mat_handle *query_handle, const opencv_core_mat_handle *train_handle,
    int32_t norm, opencv_features_knn2_result_handle **out_result, int32_t *out_count) {
    if (out_result != nullptr) *out_result = nullptr;
    if (out_count != nullptr) *out_count = 0;
    return guarded([&] {
        require(out_result != nullptr && out_count != nullptr, "null KNN2 output");
        require(norm == OPENCV_FEATURES_HAMMING || norm == OPENCV_FEATURES_HAMMING2,
                "invalid binary descriptor norm selector");
        const cv::Mat &query = descriptors(query_handle), &train = descriptors(train_handle);
        require(train.empty() || train.rows < (1 << 18), "train descriptor rows must be <= 262143");
        require(query.empty() || train.empty() || train.rows >= 2, "KNN2 requires two train rows");
        checkpoint(11); // before matcher construction, including owned empty allocation
        auto result = std::make_unique<opencv_features_knn2_result_handle>();
        std::vector<std::vector<cv::DMatch>> native;
        if (!query.empty() && !train.empty()) {
            auto matcher = cv::BFMatcher::create(norm == OPENCV_FEATURES_HAMMING ?
                            cv::NORM_HAMMING : cv::NORM_HAMMING2, false);
            require(!matcher.empty(), "native matcher factory returned no matcher");
            matcher->knnMatch(query, train, native, 2);
        }
        checkpoint(12);
        const auto expected = query.empty() || train.empty() ? std::size_t(0) : std::size_t(query.rows);
        require(native.size() == expected && native.size() <= std::size_t(INT32_MAX),
                "invalid native KNN2 count");
        const int maximum = norm == OPENCV_FEATURES_HAMMING ? 256 : 128;
        result->matches.reserve(native.size());
        for (std::size_t i = 0; i < native.size(); ++i) {
            const auto &pair = native[i];
            require(pair.size() == 2, "native KNN2 bucket must contain two neighbors");
            for (const auto &match : pair) {
                require(match.imgIdx == 0 && match.queryIdx == static_cast<int>(i) &&
                        match.trainIdx >= 0 && match.trainIdx < train.rows &&
                        std::isfinite(match.distance) && match.distance >= 0 &&
                        match.distance <= maximum && std::trunc(match.distance) == match.distance,
                        "invalid native KNN2 neighbor");
            }
            require(pair[0].trainIdx != pair[1].trainIdx && pair[0].distance <= pair[1].distance,
                    "invalid native KNN2 pair ordering or uniqueness");
            result->matches.push_back({static_cast<int32_t>(i), pair[0].trainIdx,
                static_cast<int32_t>(pair[0].distance), pair[1].trainIdx,
                static_cast<int32_t>(pair[1].distance)});
        }
        checkpoint(13); // no outputs published until all validation/allocation succeeds
        *out_count = static_cast<int32_t>(result->matches.size());
        *out_result = result.release();
    });
}
opencv_features_status opencv_features_knn2_result_get(
    const opencv_features_knn2_result_handle *handle, int32_t index,
    opencv_features_knn2_match *out_match) {
    if (out_match != nullptr) *out_match = {};
    return guarded([&] {
        require(handle != nullptr && out_match != nullptr, "null KNN2 result argument");
        require(index >= 0 && std::size_t(index) < handle->matches.size(), "KNN2 index out of range");
        checkpoint(14);
        *out_match = handle->matches[std::size_t(index)];
    });
}
void opencv_features_knn2_result_destroy(opencv_features_knn2_result_handle *handle) {
    try { delete handle; } catch (...) {}
}
} // extern C
