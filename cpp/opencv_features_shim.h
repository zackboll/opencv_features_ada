/* SPDX-License-Identifier: Apache-2.0 */
#ifndef OPENCV_FEATURES_SHIM_H
#define OPENCV_FEATURES_SHIM_H
#include <stdint.h>

#if defined(_WIN32) && defined(OPENCV_FEATURES_BUILDING)
# define OPENCV_FEATURES_API __declspec(dllexport)
#elif defined(_WIN32)
# define OPENCV_FEATURES_API __declspec(dllimport)
#else
# define OPENCV_FEATURES_API
#endif
#ifdef __cplusplus
extern "C" {
#endif

typedef struct opencv_core_mat_handle opencv_core_mat_handle;
typedef struct opencv_features_orb_handle opencv_features_orb_handle;
typedef struct opencv_features_result_handle opencv_features_result_handle;
typedef struct opencv_features_match_result_handle opencv_features_match_result_handle;
typedef struct opencv_features_knn2_result_handle opencv_features_knn2_result_handle;
typedef int32_t opencv_features_status;
enum {
    OPENCV_FEATURES_OK = 0,
    OPENCV_FEATURES_INVALID_ARGUMENT = 1,
    OPENCV_FEATURES_NATIVE_ERROR = 2,
    OPENCV_FEATURES_ALLOCATION_ERROR = 3,
    OPENCV_FEATURES_INTERNAL_ERROR = 4
};
typedef struct opencv_features_keypoint {
    float x, y, size, angle, response;
    int32_t octave, class_id;
} opencv_features_keypoint;

typedef struct opencv_features_descriptor_match {
    int32_t query_index, train_index, distance;
} opencv_features_descriptor_match;

typedef struct opencv_features_knn2_match {
    int32_t query_index, nearest_train_index, nearest_distance;
    int32_t second_train_index, second_distance;
} opencv_features_knn2_match;

/* Private semantic selectors, not OpenCV numeric norm constants. */
enum { OPENCV_FEATURES_HAMMING = 0, OPENCV_FEATURES_HAMMING2 = 1 };
enum { OPENCV_FEATURES_NEAREST = 0, OPENCV_FEATURES_MUTUAL_NEAREST = 1 };

/* Error text is thread-local, borrowed, and replaced by the next fallible
 * Features call on that thread. Destructor and metadata calls leave it alone.
 * Non-null opaque handles must be live handles created by their owner.
 * Pointer validity/lifetime cannot be proven for arbitrary C callers. */
OPENCV_FEATURES_API const char *opencv_features_last_error(void);
OPENCV_FEATURES_API const char *opencv_features_native_version(void);
OPENCV_FEATURES_API const char *opencv_features_native_backend(void);

OPENCV_FEATURES_API opencv_features_status opencv_features_orb_create(
    int32_t maximum_features, int32_t tuple, int32_t score,
    int32_t fast_threshold, opencv_features_orb_handle **out_handle);
OPENCV_FEATURES_API void opencv_features_orb_destroy(opencv_features_orb_handle *handle);

/* Outputs are initialized to null/zero before validation. Inputs are borrowed
 * only for this call. Result owns temporary native output, never input headers. */
OPENCV_FEATURES_API opencv_features_status opencv_features_orb_extract(
    opencv_features_orb_handle *handle, const opencv_core_mat_handle *image,
    opencv_features_result_handle **out_result, int32_t *out_count);
OPENCV_FEATURES_API opencv_features_status opencv_features_orb_extract_masked(
    opencv_features_orb_handle *handle, const opencv_core_mat_handle *image,
    const opencv_core_mat_handle *mask,
    opencv_features_result_handle **out_result, int32_t *out_count);
OPENCV_FEATURES_API opencv_features_status opencv_features_result_point(
    const opencv_features_result_handle *handle, int32_t index,
    opencv_features_keypoint *out_point);
OPENCV_FEATURES_API opencv_features_status opencv_features_result_descriptors(
    const opencv_features_result_handle *handle, opencv_core_mat_handle *destination);
OPENCV_FEATURES_API void opencv_features_result_destroy(opencv_features_result_handle *handle);

/* Borrowed ORB descriptor Mats: nonempty inputs must be 2-D UInt8 C1 Nx32.
 * Train rows < 2^18. Empty inputs succeed. Outputs initialize to null/zero.
 * Results own plain values, ascending by zero-based query_index. */
OPENCV_FEATURES_API opencv_features_status opencv_features_bf_match(
    const opencv_core_mat_handle *query, const opencv_core_mat_handle *train,
    int32_t norm, int32_t mode,
    opencv_features_match_result_handle **out_result, int32_t *out_count);
OPENCV_FEATURES_API opencv_features_status opencv_features_match_result_get(
    const opencv_features_match_result_handle *handle, int32_t index,
    opencv_features_descriptor_match *out_match);
OPENCV_FEATURES_API void opencv_features_match_result_destroy(
    opencv_features_match_result_handle *handle);

/* Same binary schema/train bound. Fixed K=2, no cross-check or masks.
 * Nonempty query requires >=2 train rows unless train is empty. Valid empties
 * publish an owned empty result. Otherwise one ordered pair per query row,
 * distinct train indices, nondecreasing exact integer distances. */
OPENCV_FEATURES_API opencv_features_status opencv_features_bf_knn2(
    const opencv_core_mat_handle *query, const opencv_core_mat_handle *train,
    int32_t norm, opencv_features_knn2_result_handle **out_result, int32_t *out_count);
OPENCV_FEATURES_API opencv_features_status opencv_features_knn2_result_get(
    const opencv_features_knn2_result_handle *handle, int32_t index,
    opencv_features_knn2_match *out_match);
OPENCV_FEATURES_API void opencv_features_knn2_result_destroy(
    opencv_features_knn2_result_handle *handle);

#ifdef __cplusplus
}
#endif
#endif
