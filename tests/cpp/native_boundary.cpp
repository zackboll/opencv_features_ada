// Linux qualification driver. Core's actual C factory owns every wrapper.
#include "opencv_features_shim.h"
#include "opencv_core_shim.h"
#include "opencv_core_module_bridge.hpp"
#include <opencv2/core/ocl.hpp>
#include <iostream>
#include <memory>
#include <stdexcept>

#ifdef OPENCV_FEATURES_TEST_HOOKS
extern "C" void opencv_features_test_fail(int stage, int kind);
#endif

namespace {
void check(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
using Mat = std::unique_ptr<opencv_core_mat_handle, decltype(&opencv_core_mat_destroy)>;
Mat matrix(int rows, int columns, int depth = OPENCV_CORE_DEPTH_UINT8) {
    opencv_core_mat_handle* handle = nullptr;
    check(opencv_core_mat_create_2d(rows, columns, depth, 1, &handle) == OPENCV_CORE_OK,
          "Core factory failed");
    return Mat(handle, opencv_core_mat_destroy);
}
void fill(opencv_core_mat_handle* handle, bool texture, unsigned char value = 0) {
    // Resolution is scoped to this call; no borrowed native header escapes.
    cv::Mat* image = nullptr;
    check(opencv_core_module_output_mat(handle, &image) == OPENCV_CORE_OK, "Core output resolver");
    for (int r = 0; r < image->rows; ++r)
        for (int c = 0; c < image->cols; ++c)
            image->at<unsigned char>(r, c) = texture ?
                static_cast<unsigned char>((r*37+c*17+((r/16+c/16)%2)*83+(r*c)%251)%256) : value;
}
void schema(const opencv_core_mat_handle* handle, int count) {
    const cv::Mat* image = nullptr;
    check(opencv_core_module_input_mat(handle, &image) == OPENCV_CORE_OK, "Core input resolver");
    check(count == 0 ? image->empty() :
          image->rows == count && image->cols == 32 && image->type() == CV_8UC1,
          "descriptor schema");
}
void run() {
    auto image = matrix(256, 256), mask = matrix(256, 256), blank = matrix(256, 256);
    auto wrong = matrix(256, 256, OPENCV_CORE_DEPTH_FLOAT32), small = matrix(128, 128);
    auto output = matrix(2, 2);
    fill(image.get(), true); fill(mask.get(), false, 255); fill(blank.get(), false);
    using Detector = std::unique_ptr<opencv_features_orb_handle, decltype(&opencv_features_orb_destroy)>;
    using Result = std::unique_ptr<opencv_features_result_handle, decltype(&opencv_features_result_destroy)>;
    opencv_features_orb_handle* detector = nullptr;
    check(opencv_features_orb_create(500, 2, 0, 20, &detector) == 0, "create");
    Detector owned(detector, opencv_features_orb_destroy);
    check(opencv_features_orb_create(500, 2, 0, 20, nullptr) == 1, "null create output");
    const int configs[][4] = {{0,2,0,20},{INT32_MAX/2+1,2,0,20},{500,1,0,20},
                             {500,2,2,20},{500,2,0,-1},{500,2,0,256}};
    for (const auto& config : configs) {
        auto sentinel = detector; // live, only output storage; never fake/dangling
        check(opencv_features_orb_create(config[0],config[1],config[2],config[3],&sentinel) == 1 &&
              sentinel == nullptr, "failed create outputs");
    }
    opencv_features_orb_destroy(nullptr);
    opencv_features_result_handle* raw = nullptr;
    int32_t count = -1;
    check(opencv_features_orb_extract(detector,image.get(),&raw,&count) == 0, "sentinel result");
    Result live_sentinel(raw,opencv_features_result_destroy);
    raw = live_sentinel.get();
    auto failure = [&](int32_t status) {
        check(status == 1 && raw == nullptr && count == 0, "failed extraction outputs");
        raw = live_sentinel.get(); // verify null initialization from a live non-null sentinel
        count = -1;
    };
    failure(opencv_features_orb_extract(nullptr, image.get(), &raw, &count));
    failure(opencv_features_orb_extract(detector, nullptr, &raw, &count));
    check(opencv_features_orb_extract(detector, image.get(), nullptr, &count) == 1 && count == 0,
          "null result output");
    check(opencv_features_orb_extract(detector, image.get(), &raw, nullptr) == 1 && raw == nullptr,
          "null count output");
    failure(opencv_features_orb_extract_masked(detector, image.get(), nullptr, &raw, &count));
    failure(opencv_features_orb_extract(detector, wrong.get(), &raw, &count));
    failure(opencv_features_orb_extract_masked(detector, image.get(), wrong.get(), &raw, &count));
    failure(opencv_features_orb_extract_masked(detector, image.get(), small.get(), &raw, &count));
    raw = nullptr;

#ifdef OPENCV_FEATURES_TEST_HOOKS
    // Exercise every exception category at the detector allocation checkpoint.
    const int statuses[] = {1, 2, 3, 4, 4};
    for (int kind = 1; kind <= 5; ++kind) {
        auto sentinel = detector;
        opencv_features_test_fail(1, kind);
        check(opencv_features_orb_create(500,2,0,20,&sentinel) == statuses[kind-1] &&
              sentinel == nullptr, "injected creation barrier");
    }
    // Allocation-category exceptions before staging, after native extraction,
    // and after point reserve. These test cleanup, not allocator exhaustion.
    for (int stage : {2, 3, 4}) {
        count = -1;
        opencv_features_test_fail(stage, 3);
        check(opencv_features_orb_extract(detector,image.get(),&raw,&count) == 3 &&
              raw == nullptr && count == 0, "injected extraction atomicity");
    }
#endif
    for (int mode = 0; mode < 3; ++mode) {
        const auto status = mode == 1 ?
            opencv_features_orb_extract_masked(detector,image.get(),mask.get(),&raw,&count) :
            opencv_features_orb_extract(detector,mode == 2 ? blank.get() : image.get(),&raw,&count);
        check(status == 0 && raw != nullptr && (mode == 2 ? count == 0 : count > 0), "extract");
        Result result(raw, opencv_features_result_destroy);
        check(opencv_features_result_descriptors(raw,output.get()) == 0, "export");
        schema(output.get(),count);
        if (count > 0) {
            opencv_features_keypoint point{};
            for (int index : {-1, count}) {
                point = {1,1,1,1,1,1,1};
                check(opencv_features_result_point(raw,index,&point) == 1 &&
                      point.x == 0 && point.y == 0 && point.size == 0 && point.angle == 0 &&
                      point.response == 0 && point.octave == 0 && point.class_id == 0,
                      "failed point clearing");
            }
            check(opencv_features_result_point(raw,0,nullptr) == 1, "null point");
            check(opencv_features_result_point(nullptr,0,&point) == 1 && point.size == 0, "null result");
            check(opencv_features_result_descriptors(nullptr,output.get()) == 1, "null export result");
            check(opencv_features_result_descriptors(raw,nullptr) == 1, "null export destination");
            unsigned char buffer[4] = {};
            opencv_core_mat_handle* external = nullptr;
            check(opencv_core_mat_create_external_2d(2,2,0,1,buffer,sizeof buffer,&external) == 0,
                  "real external Core view factory");
            Mat view(external,opencv_core_mat_destroy);
            check(opencv_features_result_descriptors(raw,view.get()) == 1, "external output rejection");
#ifdef OPENCV_FEATURES_TEST_HOOKS
            opencv_features_test_fail(5,3);
            check(opencv_features_result_point(raw,0,&point) == 3 && point.size == 0, "point barrier");
            opencv_features_test_fail(6,3);
            check(opencv_features_result_descriptors(raw,output.get()) == 3, "export barrier");
            schema(output.get(),count); // previous destination is unchanged
#endif
            check(opencv_features_result_point(raw,0,&point) == 0 && point.size > 0, "first point");
            check(opencv_features_result_point(raw,count-1,&point) == 0, "last point");
        }
        raw = nullptr;
    }
    check(opencv_features_orb_extract(detector,image.get(),&raw,&count) == 0, "lifetime extract");
    Result result(raw,opencv_features_result_destroy);
    owned.reset();
    opencv_features_keypoint point{};
    check(opencv_features_result_point(raw,count-1,&point) == 0, "detector-independent result");
    check(opencv_features_result_descriptors(raw,output.get()) == 0, "lifetime export");
    result.reset();
    schema(output.get(),count);
    opencv_features_result_destroy(nullptr);
}
}
int main() {
    try {
        // Qualification is CPU-only. Test-driver policy, not a binding side effect.
        // Avoid loading optional host GPU ICDs; leak detection remains enabled.
        cv::ocl::setUseOpenCL(false);
        run();
        std::cout << "PASS: actual Features shim / Core bridge / ORB boundary on "
                  << opencv_features_native_version() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}