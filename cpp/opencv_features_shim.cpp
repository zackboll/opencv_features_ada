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
#include <cmath>
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

struct opencv_features_orb_handle { cv::Ptr<cv::ORB> detector; };
struct opencv_features_result_handle {
    std::vector<opencv_features_keypoint> points;
    cv::Mat descriptors; // private temporary, never an application-owned wrapper
};

namespace {
thread_local char error_text[1024] = "";
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
    auto result = std::make_unique<opencv_features_result_handle>();
    std::vector<cv::KeyPoint> keypoints;
    handle->detector->detectAndCompute(image, mask, keypoints, result->descriptors, false);
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
        *output = handle->descriptors; // retain storage in the actual Core-owned header
    });
}
void opencv_features_result_destroy(opencv_features_result_handle *handle) {
    try { delete handle; } catch (...) {}
}
} // extern C
