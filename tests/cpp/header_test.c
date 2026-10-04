/* SPDX-License-Identifier: Apache-2.0 */
#include "opencv_features_shim.h"
#include <stddef.h>
_Static_assert(sizeof(opencv_features_keypoint) == 28, "keypoint ABI size");
_Static_assert(offsetof(opencv_features_keypoint, class_id) == 24, "keypoint ABI layout");
int main(void) { return OPENCV_FEATURES_OK; }
