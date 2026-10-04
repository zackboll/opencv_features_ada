/* Compiler-derived C layout, linked only into the test executable. */
#include "../../cpp/opencv_features_shim.h"
#include <stddef.h>

int32_t features_test_layout(int32_t field)
{
    const size_t layout[] = {
        sizeof(opencv_features_keypoint), _Alignof(opencv_features_keypoint),
        offsetof(opencv_features_keypoint, x), offsetof(opencv_features_keypoint, y),
        offsetof(opencv_features_keypoint, size), offsetof(opencv_features_keypoint, angle),
        offsetof(opencv_features_keypoint, response), offsetof(opencv_features_keypoint, octave),
        offsetof(opencv_features_keypoint, class_id)
    };
    return field >= 0 && field < 9 ? (int32_t)layout[field] : -1;
}

void features_test_keypoint(opencv_features_keypoint *point)
{
    *point = (opencv_features_keypoint){1.25f, -2.5f, 31.0f, 90.0f, 0.125f, 7, -1};
}