/* SPDX-License-Identifier: Apache-2.0 */
#include "opencv_features_shim.h"
#include <stddef.h>
_Static_assert(sizeof(opencv_features_keypoint) == 28, "keypoint ABI size");
_Static_assert(_Alignof(opencv_features_keypoint) == 4, "keypoint ABI alignment");
_Static_assert(offsetof(opencv_features_keypoint, x) == 0, "x offset");
_Static_assert(offsetof(opencv_features_keypoint, y) == 4, "y offset");
_Static_assert(offsetof(opencv_features_keypoint, size) == 8, "size offset");
_Static_assert(offsetof(opencv_features_keypoint, angle) == 12, "angle offset");
_Static_assert(offsetof(opencv_features_keypoint, response) == 16, "response offset");
_Static_assert(offsetof(opencv_features_keypoint, octave) == 20, "octave offset");
_Static_assert(offsetof(opencv_features_keypoint, class_id) == 24, "keypoint ABI layout");
int main(void) { return OPENCV_FEATURES_OK; }
