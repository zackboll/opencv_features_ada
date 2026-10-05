// Linux qualification driver. Core's actual C factory owns every wrapper.
#include "opencv_features_shim.h"
#include "opencv_core_shim.h"
#include "opencv_core_module_bridge.hpp"
#include "radius_limits.hpp"
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
Mat matrix(int rows, int columns, int depth = OPENCV_CORE_DEPTH_UINT8, int channels = 1) {
    opencv_core_mat_handle* handle = nullptr;
    check(opencv_core_mat_create_2d(rows, columns, depth, channels, &handle) == OPENCV_CORE_OK,
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
using Matches = std::unique_ptr<opencv_features_match_result_handle,
                               decltype(&opencv_features_match_result_destroy)>;
void matching() {
    auto query = matrix(2,32), train = matrix(1,32);
    fill(query.get(),false); fill(train.get(),false);
    // q0 identical, q1 one differing bit/bin; train has one unique candidate.
    cv::Mat *q = nullptr;
    check(opencv_core_module_output_mat(query.get(),&q) == 0, "descriptor writer");
    q->at<unsigned char>(1,0) = 1;
    for (int norm : {OPENCV_FEATURES_HAMMING, OPENCV_FEATURES_HAMMING2}) {
        for (int mode : {OPENCV_FEATURES_NEAREST, OPENCV_FEATURES_MUTUAL_NEAREST}) {
            opencv_features_match_result_handle *raw = nullptr;
            int32_t count = -1;
            check(opencv_features_bf_match(query.get(),train.get(),norm,mode,&raw,&count) == 0 &&
                  raw != nullptr && count == (mode == 0 ? 2 : 1), "nearest/cross-check count");
            Matches result(raw,opencv_features_match_result_destroy);
            for (int i = 0; i < count; ++i) {
                opencv_features_descriptor_match item{};
                check(opencv_features_match_result_get(raw,i,&item) == 0 && item.query_index == i &&
                      item.train_index == 0 && item.distance == i, "exact distance 0/1 and index oracle");
            }
            opencv_features_descriptor_match item{7,8,9};
            for (int i : {-1,count}) {
                item = {7,8,9};
                check(opencv_features_match_result_get(raw,i,&item) == 1 && item.query_index == 0 &&
                      item.train_index == 0 && item.distance == 0, "match invalid-index clearing");
            }
            check(opencv_features_match_result_get(raw,0,nullptr) == 1, "null match output");
            item = {7,8,9};
            check(opencv_features_match_result_get(nullptr,0,&item) == 1 && item.query_index == 0 &&
                  item.train_index == 0 && item.distance == 0, "null result clearing");
#ifdef OPENCV_FEATURES_TEST_HOOKS
            opencv_features_test_fail(10,3);
            check(opencv_features_match_result_get(raw,0,&item) == 3 && item.distance == 0,
                  "match get exception barrier");
#endif
        }
        auto maximum = matrix(1,32);
        fill(maximum.get(),false,255);
        opencv_features_match_result_handle *raw = nullptr;
        int32_t count = -1;
        check(opencv_features_bf_match(train.get(),maximum.get(),norm,0,&raw,&count) == 0 && count == 1,
              "maximum distance match");
        Matches result(raw,opencv_features_match_result_destroy);
        // Results no longer depend on descriptor input lifetime.
        maximum.reset();
        opencv_features_descriptor_match item{};
        check(opencv_features_match_result_get(raw,0,&item) == 0 && item.query_index == 0 &&
              item.train_index == 0 && item.distance == (norm == 0 ? 256 : 128), "maximum distance oracle");
    }
    // Distinguish a changed 2-bit cell (0b11) from two changed bits.
    q->at<unsigned char>(1,0) = 3;
    for (int norm : {0,1}) {
        opencv_features_match_result_handle *raw = nullptr;
        int32_t count = 0;
        check(opencv_features_bf_match(query.get(),train.get(),norm,0,&raw,&count) == 0 && count == 2,
              "two-bit-cell fixture");
        Matches result(raw,opencv_features_match_result_destroy);
        opencv_features_descriptor_match item{};
        check(opencv_features_match_result_get(raw,1,&item) == 0 && item.distance == (norm == 0 ? 2 : 1),
              "Hamming versus Hamming2 cell oracle");
    }
    // Unique nonzero train index oracle and noncontiguous descriptor ROI.
    auto backing = matrix(2,40);
    fill(backing.get(),false,255);
    cv::Mat *header = nullptr;
    check(opencv_core_module_output_mat(backing.get(),&header) == 0, "ROI writer");
    (*header) = (*header)(cv::Rect(0,0,32,2));
    header->row(1).setTo(0);
    opencv_features_match_result_handle *sentinel = nullptr;
    int32_t count = -1;
    check(opencv_features_bf_match(train.get(),backing.get(),0,0,&sentinel,&count) == 0 && count == 1,
          "noncontiguous descriptors");
    Matches live(sentinel,opencv_features_match_result_destroy);
    opencv_features_descriptor_match item{};
    check(opencv_features_match_result_get(sentinel,0,&item) == 0 && item.train_index == 1 &&
          item.query_index == 0 && item.distance == 0, "unique train-index oracle");
    auto raw = sentinel;
    auto fail = [&](int status) {
        check(status == 1 && raw == nullptr && count == 0, "failed match output initialization");
        raw = sentinel; count = -1;
    };
    count = -1;
    check(opencv_features_bf_match(query.get(),train.get(),0,0,nullptr,&count) == 1 && count == 0,
          "null result output");
    check(opencv_features_bf_match(query.get(),train.get(),0,0,&raw,nullptr) == 1 && raw == nullptr,
          "null count output");
    raw = sentinel; count = -1;
    fail(opencv_features_bf_match(nullptr,train.get(),0,0,&raw,&count));
    fail(opencv_features_bf_match(query.get(),nullptr,0,0,&raw,&count));
    for (int selector : {-1,2,INT32_MAX}) {
        fail(opencv_features_bf_match(query.get(),train.get(),selector,0,&raw,&count));
        fail(opencv_features_bf_match(query.get(),train.get(),0,selector,&raw,&count));
    }
    auto wrong = matrix(1,32,OPENCV_CORE_DEPTH_FLOAT32), multi = matrix(1,32,0,2);
    auto short_row = matrix(1,31), long_row = matrix(1,33), too_many = matrix(262144,32);
    const int32_t sizes[] = {2,2,32};
    opencv_core_mat_handle *nd = nullptr;
    check(opencv_core_mat_create_nd(3,sizes,0,1,&nd) == 0, "real N-D descriptor factory");
    Mat dimensional(nd,opencv_core_mat_destroy);
    for (auto *bad : {wrong.get(),multi.get(),short_row.get(),long_row.get(),dimensional.get()}) {
        fail(opencv_features_bf_match(bad,train.get(),0,0,&raw,&count));
        fail(opencv_features_bf_match(query.get(),bad,0,0,&raw,&count));
    }
    fail(opencv_features_bf_match(query.get(),too_many.get(),0,0,&raw,&count));
    fail(opencv_features_bf_match(query.get(),too_many.get(),0,1,&raw,&count));
    // Exact admissible train bound; unique minimum at the last packed index.
    auto last_train = matrix(262143,32);
    fill(last_train.get(),false,255);
    cv::Mat *last_header = nullptr;
    check(opencv_core_module_output_mat(last_train.get(),&last_header) == 0, "train bound writer");
    last_header->row(262142).setTo(0);
    for (int mode : {0,1}) {
        raw = nullptr;
        check(opencv_features_bf_match(train.get(),last_train.get(),0,mode,&raw,&count) == 0 && count == 1,
              "262143 train rows accepted");
        Matches result(raw,opencv_features_match_result_destroy);
        check(opencv_features_match_result_get(raw,0,&item) == 0 && item.train_index == 262142 &&
              item.query_index == 0 && item.distance == 0, "last packed train index preserved");
    }
    // Query is NOT subject to packed train-index bound, including cross-check.
    fill(too_many.get(),false);
    for (int mode : {0,1}) {
        raw = nullptr;
        check(opencv_features_bf_match(too_many.get(),train.get(),0,mode,&raw,&count) == 0 &&
              count == (mode == 0 ? 262144 : 1), "large query accepted");
        Matches large(raw,opencv_features_match_result_destroy);
        check(opencv_features_match_result_get(raw,count-1,&item) == 0 && item.distance == 0 &&
              (mode == 0 ? item.query_index == 262143 :
               item.query_index >= 0 && item.query_index < 262144), "large query index is not packed");
    }
    opencv_core_mat_handle *empty_handle = nullptr;
    check(opencv_core_mat_create(&empty_handle) == 0, "empty Core descriptor factory");
    Mat empty(empty_handle,opencv_core_mat_destroy);
    for (int mode : {0,1}) {
        for (int combination = 0; combination < 3; ++combination) {
            raw = nullptr;
            check(opencv_features_bf_match(combination == 1 ? query.get() : empty.get(),
                  combination == 0 ? train.get() : empty.get(),0,mode,&raw,&count) == 0 &&
                  count == 0 && raw != nullptr, "empty match success");
            Matches result(raw,opencv_features_match_result_destroy);
            item = {7,8,9};
            check(opencv_features_match_result_get(raw,0,&item) == 1 && item.distance == 0,
                  "empty result access");
        }
    }
#ifdef OPENCV_FEATURES_TEST_HOOKS
    for (int stage : {7,8,9}) for (int kind = 1; kind <= 5; ++kind) {
        raw = sentinel; count = -1;
        opencv_features_test_fail(stage,kind);
        const int expected[] = {0,1,2,3,4,4};
        check(opencv_features_bf_match(query.get(),train.get(),0,0,&raw,&count) == expected[kind] &&
              raw == nullptr && count == 0, "matcher exception/publication atomicity");
    }
    raw = sentinel; count = -1;
    opencv_features_test_fail(9,3);
    check(opencv_features_bf_match(empty.get(),train.get(),0,0,&raw,&count) == 3 &&
          raw == nullptr && count == 0, "empty matcher publication cleanup");
#endif
    opencv_features_match_result_destroy(nullptr);
    std::cout << "PASS: matcher Hamming 0/1/2/256; Hamming2 0/1/128; cross-check A/X retained B/X rejected; "
                 "raw negatives, empty, ROI, large query, lifetime/publication\n";
}
using KNN2 = std::unique_ptr<opencv_features_knn2_result_handle,
                             decltype(&opencv_features_knn2_result_destroy)>;
bool cleared(const opencv_features_knn2_match &item) {
    return item.query_index == 0 && item.nearest_train_index == 0 && item.nearest_distance == 0 &&
           item.second_train_index == 0 && item.second_distance == 0;
}
void knn2() {
    auto query = matrix(1,32), train = matrix(3,32);
    fill(query.get(),false);
    cv::Mat *t = nullptr;
    check(opencv_core_module_output_mat(train.get(),&t) == 0, "KNN2 descriptor writer");
    for (int norm : {0,1}) {
        fill(train.get(),false);
        // Separate bits for Hamming, separate 2-bit cells for Hamming2.
        t->at<unsigned char>(1,0) = 1;
        t->at<unsigned char>(2,0) = norm == 0 ? 3 : 5;
        opencv_features_knn2_result_handle *raw = nullptr;
        int32_t count = -1;
        check(opencv_features_bf_knn2(query.get(),train.get(),norm,&raw,&count) == 0 &&
              raw != nullptr && count == 1, "KNN2 exact pair count");
        KNN2 result(raw,opencv_features_knn2_result_destroy);
        opencv_features_knn2_match item{};
        check(opencv_features_knn2_result_get(raw,0,&item) == 0 && item.query_index == 0 &&
              item.nearest_train_index == 0 && item.nearest_distance == 0 &&
              item.second_train_index == 1 && item.second_distance == 1, "KNN2 exact 0/1 oracle");
        for (int index : {-1,count}) {
            item = {7,8,9,10,11};
            check(opencv_features_knn2_result_get(raw,index,&item) == 1 && cleared(item),
                  "KNN2 invalid-index clearing");
        }
        check(opencv_features_knn2_result_get(raw,0,nullptr) == 1, "KNN2 null output");
        item = {7,8,9,10,11};
        check(opencv_features_knn2_result_get(nullptr,0,&item) == 1 && cleared(item),
              "KNN2 null result clearing");
#ifdef OPENCV_FEATURES_TEST_HOOKS
        for (int kind = 1; kind <= 5; ++kind) {
            const int expected[] = {0,1,2,3,4,4};
            item = {7,8,9,10,11};
            opencv_features_test_fail(14,kind);
            check(opencv_features_knn2_result_get(raw,0,&item) == expected[kind] && cleared(item),
                  "KNN2 get exception clearing");
        }
#endif
        result.reset();
        // No exact copy: best=1, second=2. Third row is deliberately farther.
        t->row(0).setTo(255);
        raw = nullptr;
        check(opencv_features_bf_knn2(query.get(),train.get(),norm,&raw,&count) == 0 && count == 1,
              "KNN2 nonzero pair");
        KNN2 nonzero(raw,opencv_features_knn2_result_destroy);
        check(opencv_features_knn2_result_get(raw,0,&item) == 0 && item.nearest_train_index == 1 &&
              item.nearest_distance == 1 && item.second_train_index == 2 && item.second_distance == 2,
              "KNN2 exact nonzero 1/2 oracle");
        // Equal best distances: do not freeze tied train ordering.
        t->at<unsigned char>(2,0) = norm == 0 ? 2 : 4;
        raw = nullptr;
        check(opencv_features_bf_knn2(query.get(),train.get(),norm,&raw,&count) == 0 && count == 1,
              "KNN2 tie pair");
        KNN2 tie(raw,opencv_features_knn2_result_destroy);
        check(opencv_features_knn2_result_get(raw,0,&item) == 0 && item.nearest_distance == 1 &&
              item.second_distance == 1 && item.nearest_train_index != item.second_train_index &&
              item.nearest_train_index >= 1 && item.nearest_train_index <= 2 &&
              item.second_train_index >= 1 && item.second_train_index <= 2, "KNN2 tie oracle");
    }
    // Explicit 0x03 norm distinction on KNN2, with unique ranks.
    fill(train.get(),false,255);
    t->row(0).setTo(0); t->row(1).setTo(0); t->at<unsigned char>(1,0) = 3;
    for (int norm : {0,1}) {
        opencv_features_knn2_result_handle *raw = nullptr;
        int32_t count = 0;
        check(opencv_features_bf_knn2(query.get(),train.get(),norm,&raw,&count) == 0 && count == 1,
              "KNN2 cell pair");
        KNN2 result(raw,opencv_features_knn2_result_destroy);
        opencv_features_knn2_match item{};
        check(opencv_features_knn2_result_get(raw,0,&item) == 0 && item.nearest_distance == 0 &&
              item.second_distance == (norm == 0 ? 2 : 1), "KNN2 Hamming/Hamming2 cell oracle");
    }
    opencv_features_knn2_result_handle *sentinel = nullptr;
    int32_t count = 0;
    check(opencv_features_bf_knn2(query.get(),train.get(),0,&sentinel,&count) == 0, "KNN2 sentinel");
    KNN2 live(sentinel,opencv_features_knn2_result_destroy);
    auto raw = sentinel;
    auto fail = [&](int status) {
        check(status == 1 && raw == nullptr && count == 0, "KNN2 failure atomicity");
        raw = sentinel; count = -1;
    };
    count = -1;
    check(opencv_features_bf_knn2(query.get(),train.get(),0,nullptr,&count) == 1 && count == 0,
          "KNN2 null result output");
    check(opencv_features_bf_knn2(query.get(),train.get(),0,&raw,nullptr) == 1 && raw == nullptr,
          "KNN2 null count output");
    raw = sentinel; count = -1;
    fail(opencv_features_bf_knn2(nullptr,train.get(),0,&raw,&count));
    fail(opencv_features_bf_knn2(query.get(),nullptr,0,&raw,&count));
    for (int norm : {-1,2,INT32_MAX})
        fail(opencv_features_bf_knn2(query.get(),train.get(),norm,&raw,&count));
    auto wrong = matrix(2,32,OPENCV_CORE_DEPTH_FLOAT32), multi = matrix(2,32,0,2);
    auto short_row = matrix(2,31), long_row = matrix(2,33), one = matrix(1,32);
    const int32_t sizes[] = {2,2,32};
    opencv_core_mat_handle *nd = nullptr;
    check(opencv_core_mat_create_nd(3,sizes,0,1,&nd) == 0, "KNN2 real N-D factory");
    Mat dimensional(nd,opencv_core_mat_destroy);
    for (auto *bad : {wrong.get(),multi.get(),short_row.get(),long_row.get(),dimensional.get()}) {
        fail(opencv_features_bf_knn2(bad,train.get(),0,&raw,&count));
        fail(opencv_features_bf_knn2(query.get(),bad,0,&raw,&count));
    }
    for (int norm : {0,1})
        fail(opencv_features_bf_knn2(query.get(),one.get(),norm,&raw,&count));
    auto too_many = matrix(262144,32), boundary = matrix(262143,32);
    fail(opencv_features_bf_knn2(query.get(),too_many.get(),0,&raw,&count));
    fill(boundary.get(),false,255);
    cv::Mat *b = nullptr;
    check(opencv_core_module_output_mat(boundary.get(),&b) == 0, "KNN2 train-bound writer");
    b->row(262142).setTo(0); b->row(262141).setTo(0); b->at<unsigned char>(262141,0) = 1;
    for (int norm : {0,1}) {
        raw = nullptr;
        check(opencv_features_bf_knn2(query.get(),boundary.get(),norm,&raw,&count) == 0 && count == 1,
              "KNN2 262143 train rows accepted");
        KNN2 result(raw,opencv_features_knn2_result_destroy);
        opencv_features_knn2_match item{};
        check(opencv_features_knn2_result_get(raw,0,&item) == 0 && item.nearest_train_index == 262142 &&
              item.second_train_index == 262141 && item.nearest_distance == 0 && item.second_distance == 1,
              "KNN2 both high packed train indices preserved");
        fail(opencv_features_bf_knn2(query.get(),too_many.get(),norm,&raw,&count));
    }
    fill(too_many.get(),false);
    auto two = matrix(2,32); fill(two.get(),false);
    for (int norm : {0,1}) {
        raw = nullptr;
        check(opencv_features_bf_knn2(too_many.get(),two.get(),norm,&raw,&count) == 0 && count == 262144,
              "KNN2 no 18-bit query limit");
        KNN2 result(raw,opencv_features_knn2_result_destroy);
        for (int index : {0,262143}) {
            opencv_features_knn2_match item{};
            check(opencv_features_knn2_result_get(raw,index,&item) == 0 && item.query_index == index &&
                  item.nearest_distance == 0 && item.second_distance == 0 &&
                  item.nearest_train_index != item.second_train_index &&
                  item.nearest_train_index >= 0 && item.nearest_train_index < 2 &&
                  item.second_train_index >= 0 && item.second_train_index < 2, "KNN2 large query indices");
        }
    }
    opencv_core_mat_handle *empty_handle = nullptr;
    check(opencv_core_mat_create(&empty_handle) == 0, "KNN2 empty Core factory");
    Mat empty(empty_handle,opencv_core_mat_destroy);
    for (int norm : {0,1}) for (int combination = 0; combination < 3; ++combination) {
        raw = nullptr;
        check(opencv_features_bf_knn2(combination == 1 ? query.get() : empty.get(),
              combination == 0 ? one.get() : empty.get(),norm,&raw,&count) == 0 && raw && count == 0,
              "KNN2 owned empty result, including empty query + one train row");
        KNN2 result(raw,opencv_features_knn2_result_destroy);
        opencv_features_knn2_match item{7,8,9,10,11};
        check(opencv_features_knn2_result_get(raw,0,&item) == 1 && cleared(item), "KNN2 empty access");
    }
#ifdef OPENCV_FEATURES_TEST_HOOKS
    for (int stage : {11,12,13}) for (int kind = 1; kind <= 5; ++kind) {
        const int expected[] = {0,1,2,3,4,4};
        raw = sentinel; count = -1;
        opencv_features_test_fail(stage,kind);
        check(opencv_features_bf_knn2(query.get(),train.get(),0,&raw,&count) == expected[kind] &&
              raw == nullptr && count == 0, "KNN2 exception/publication atomicity");
    }
    raw = sentinel; count = -1;
    opencv_features_test_fail(13,3);
    check(opencv_features_bf_knn2(empty.get(),train.get(),0,&raw,&count) == 3 && raw == nullptr && count == 0,
          "KNN2 empty publication cleanup");
#endif
    // Noncontiguous Nx32 snapshot and lifetime independent of both descriptor Mats.
    auto roi = matrix(3,40); fill(roi.get(),false,255);
    cv::Mat *r = nullptr;
    check(opencv_core_module_output_mat(roi.get(),&r) == 0, "KNN2 ROI writer");
    *r = (*r)(cv::Rect(0,0,32,3));
    r->row(2).setTo(0); r->row(1).setTo(0); r->at<unsigned char>(1,0) = 1;
    raw = nullptr;
    check(opencv_features_bf_knn2(query.get(),roi.get(),0,&raw,&count) == 0 && count == 1,
          "KNN2 noncontiguous ROI");
    KNN2 result(raw,opencv_features_knn2_result_destroy);
    query.reset(); roi.reset(); train.reset();
    opencv_features_knn2_match item{};
    check(opencv_features_knn2_result_get(raw,0,&item) == 0 && item.nearest_train_index == 2 &&
          item.nearest_distance == 0 && item.second_train_index == 1 && item.second_distance == 1,
          "KNN2 lifetime/ROI oracle");
    opencv_features_knn2_result_destroy(nullptr);
    std::cout << "PASS: KNN2 Hamming/Hamming2 exact 0/1, nonzero 1/2, 0x03 cell, tie; "
                 "raw negatives/empty/one-row; 262143 train high indices; 262144 query; ROI/lifetime/get/publication\n";
}
void radius() {
    auto query = matrix(3,32), train = matrix(6,32);
    cv::Mat *q = nullptr, *t = nullptr;
    check(opencv_core_module_output_mat(query.get(),&q) == 0 &&
          opencv_core_module_output_mat(train.get(),&t) == 0, "radius descriptor writers");
    for (int norm : {0,1}) {
        fill(query.get(),false); fill(train.get(),false);
        q->row(1).setTo(170); // no matches: preserve missing-query gap
        q->row(2).setTo(255);
        t->at<unsigned char>(1,0) = norm == 0 ? 1 : 3;
        t->at<unsigned char>(2,0) = norm == 0 ? 3 : 15;
        t->at<unsigned char>(3,0) = norm == 0 ? 7 : 63;
        t->at<unsigned char>(4,0) = norm == 0 ? 2 : 12; // distance-1 tie
        t->row(5).setTo(255); // exactly one q2 match
        const auto before_q = q->clone(), before_t = t->clone();
        opencv_features_match_result_handle *raw = nullptr;
        int32_t count = -1;
        check(opencv_features_bf_radius_match(query.get(),train.get(),norm,2,&raw,&count) == 0 && raw && count == 5,
              "radius multiple/one/zero bucket count, not K=2");
        Matches result(raw,opencv_features_match_result_destroy);
        bool seen[6] = {}; int previous = -1;
        for (int i = 0; i < count; ++i) {
            opencv_features_descriptor_match item{};
            check(opencv_features_match_result_get(raw,i,&item) == 0, "radius getter");
            if (i < 4) {
                check(item.query_index == 0 && item.train_index >= 0 && item.train_index < 5 &&
                      item.train_index != 3 && !seen[item.train_index] && item.distance >= previous &&
                      item.distance == (item.train_index == 0 ? 0 : item.train_index == 2 ? 2 : 1),
                      "radius exact Hamming/Hamming2 inclusive boundary/tie/order");
                seen[item.train_index] = true; previous = item.distance;
            } else check(item.query_index == 2 && item.train_index == 5 && item.distance == 0,
                         "radius missing-query gap and one bucket");
        }
        check(cv::countNonZero(*q != before_q) == 0 && cv::countNonZero(*t != before_t) == 0,
              "radius inputs preserved");
        opencv_features_descriptor_match item{7,8,9};
        for (int index : {-1,count}) {
            item = {7,8,9};
            check(opencv_features_match_result_get(raw,index,&item) == 1 && item.query_index == 0 &&
                  item.train_index == 0 && item.distance == 0, "radius invalid-index clearing");
        }
        check(opencv_features_match_result_get(raw,0,nullptr) == 1, "radius null output record");
        item = {7,8,9};
        check(opencv_features_match_result_get(nullptr,0,&item) == 1 && item.query_index == 0 &&
              item.train_index == 0 && item.distance == 0, "radius null result clearing");
        std::cout << "PASS: radius " << (norm == 0 ? "Hamming" : "Hamming2")
                  << " exact 0/1/2/3, inclusive boundary, ties, multiple/one/zero buckets\n";
    }
    // High index really appears. Use row 262144 (one-based 262145), beyond
    // even the representable low packed KNN index, not merely a large Mat.
    auto one = matrix(1,32), high = matrix(262145,32);
    fill(one.get(),false); fill(high.get(),false,255);
    cv::Mat *h = nullptr;
    check(opencv_core_module_output_mat(high.get(),&h) == 0, "radius high-index writer");
    h->row(262144).setTo(0);
    for (int norm : {0,1}) {
        opencv_features_match_result_handle *raw = nullptr; int32_t count = -1;
        check(opencv_features_bf_radius_match(one.get(),high.get(),norm,1,&raw,&count) == 0 && count == 1,
              "radius high train row accepted");
        Matches result(raw,opencv_features_match_result_destroy);
        opencv_features_descriptor_match item{};
        check(opencv_features_match_result_get(raw,0,&item) == 0 && item.query_index == 0 &&
              item.train_index == 262144 && item.distance == 0, "radius direct high train index preserved");
    }
    std::cout << "PASS: radius high train index 262144 (Ada 262145), both norms; KNN rejection retained\n";
    opencv_features_match_result_handle *sentinel = nullptr; int32_t count = -1;
    check(opencv_features_bf_radius_match(one.get(),one.get(),0,1,&sentinel,&count) == 0, "radius sentinel");
    Matches live(sentinel,opencv_features_match_result_destroy);
    auto raw = sentinel;
    auto fail = [&](int status) {
        check(status == 1 && raw == nullptr && count == 0, "radius failure atomicity");
        raw = sentinel; count = -1;
    };
    check(opencv_features_bf_radius_match(one.get(),one.get(),0,1,nullptr,&count) == 1 && count == 0,
          "radius null result pointer");
    check(opencv_features_bf_radius_match(one.get(),one.get(),0,1,&raw,nullptr) == 1 && raw == nullptr,
          "radius null count pointer");
    raw = sentinel; count = -1;
    fail(opencv_features_bf_radius_match(nullptr,one.get(),0,1,&raw,&count));
    fail(opencv_features_bf_radius_match(one.get(),nullptr,0,1,&raw,&count));
    for (int norm : {-1,2,INT32_MAX}) fail(opencv_features_bf_radius_match(one.get(),one.get(),norm,1,&raw,&count));
    auto wrong = matrix(2,32,OPENCV_CORE_DEPTH_FLOAT32), multi = matrix(2,32,0,2);
    auto short_row = matrix(2,31), long_row = matrix(2,33);
    const int32_t sizes[] = {2,2,32}; opencv_core_mat_handle *nd = nullptr;
    check(opencv_core_mat_create_nd(3,sizes,0,1,&nd) == 0, "radius N-D Core factory");
    Mat dimensional(nd,opencv_core_mat_destroy);
    for (auto *bad : {wrong.get(),multi.get(),short_row.get(),long_row.get(),dimensional.get()}) {
        fail(opencv_features_bf_radius_match(bad,one.get(),0,1,&raw,&count));
        fail(opencv_features_bf_radius_match(one.get(),bad,0,1,&raw,&count));
    }
    opencv_core_mat_handle *empty_handle = nullptr;
    check(opencv_core_mat_create(&empty_handle) == 0, "radius empty Core factory");
    Mat empty(empty_handle,opencv_core_mat_destroy);
    for (int norm : {0,1}) {
        for (int threshold : {-1,0,norm == 0 ? 257 : 129,INT32_MAX}) {
            fail(opencv_features_bf_radius_match(one.get(),one.get(),norm,threshold,&raw,&count));
            fail(opencv_features_bf_radius_match(empty.get(),one.get(),norm,threshold,&raw,&count));
            fail(opencv_features_bf_radius_match(one.get(),empty.get(),norm,threshold,&raw,&count));
            fail(opencv_features_bf_radius_match(empty.get(),empty.get(),norm,threshold,&raw,&count));
        }
        for (int combination = 0; combination < 3; ++combination) {
            raw = nullptr;
            check(opencv_features_bf_radius_match(combination == 1 ? one.get() : empty.get(),
                  combination == 0 ? one.get() : empty.get(),norm,1,&raw,&count) == 0 && raw && count == 0,
                  "radius compatible owned empty");
            Matches result(raw,opencv_features_match_result_destroy);
        }
        raw = nullptr;
        check(opencv_features_bf_radius_match(one.get(),high.get(),norm,norm == 0 ? 256 : 128,&raw,&count) == 0 &&
              count == 262145, "radius norm attainable maximum inclusive");
        Matches all(raw,opencv_features_match_result_destroy);
    }
    // Pure arithmetic injection of impossible counts uses the exact production
    // helper, without allocating billions of matches or forged native handles.
    check(opencv_features_detail::radius_count_fits(INT32_MAX-1,1,INT32_MAX) &&
          !opencv_features_detail::radius_count_fits(INT32_MAX,1,INT32_MAX) &&
          !opencv_features_detail::radius_count_fits(0,std::size_t(INT32_MAX)+1,INT32_MAX) &&
          !opencv_features_detail::radius_count_fits(2,1,2) &&
          !opencv_features_detail::radius_layout_fits(std::numeric_limits<std::size_t>::max(),2),
          "radius count/layout overflow arithmetic");
#ifdef OPENCV_FEATURES_TEST_HOOKS
    for (int stage : {15,16,17,18}) for (int kind = 1; kind <= 5; ++kind) {
        raw = sentinel; count = -1;
        opencv_features_test_fail(stage,kind);
        const int expected[] = {0,1,2,3,4,4};
        check(opencv_features_bf_radius_match(one.get(),one.get(),0,1,&raw,&count) == expected[kind] &&
              raw == nullptr && count == 0, "radius injected exception/publication atomicity");
    }
    for (int stage : {15,16,18}) {
        raw = sentinel; count = -1; opencv_features_test_fail(stage,3);
        check(opencv_features_bf_radius_match(empty.get(),one.get(),0,1,&raw,&count) == 3 &&
              raw == nullptr && count == 0, "radius empty result cleanup");
    }
    std::cout << "PASS: radius fault stages 15/16/17/18 x five exception categories, empty cleanup\n";
#endif
    // Noncontiguous descriptor rows and result lifetime after input destruction.
    auto roi = matrix(2,40); fill(roi.get(),false);
    cv::Mat *r = nullptr;
    check(opencv_core_module_output_mat(roi.get(),&r) == 0, "radius ROI writer");
    *r = (*r)(cv::Rect(0,0,32,2));
    check(!r->isContinuous(), "radius ROI fixture must be noncontiguous");
    const auto roi_before = r->clone();
    raw = nullptr;
    check(opencv_features_bf_radius_match(roi.get(),one.get(),0,1,&raw,&count) == 0 && count == 2 &&
          cv::countNonZero(*r != roi_before) == 0, "radius ROI preserved/no cross-check");
    Matches saved(raw,opencv_features_match_result_destroy);
    roi.reset(); one.reset();
    opencv_features_descriptor_match item{};
    for (int i : {0,1})
        check(opencv_features_match_result_get(raw,i,&item) == 0 && item.query_index == i &&
              item.train_index == 0 && item.distance == 0, "radius input-independent lifetime/no global uniqueness");
    opencv_features_match_result_destroy(nullptr);
    std::cout << "PASS: radius raw negatives, thresholds/empties/one row, overflow helpers, ROI/lifetime\n";
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
        matching();
        knn2();
        radius();
        std::cout << "PASS: actual Features shim / Core bridge / ORB boundary on "
                  << opencv_features_native_version() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}