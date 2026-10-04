// Minimal upstream-only reproducer for host OpenCL initialization leaks.
#include <opencv2/core/ocl.hpp>
#include <opencv2/core/version.hpp>
#if CV_VERSION_MAJOR == 4
#include <opencv2/features2d.hpp>
#else
#include <opencv2/features.hpp>
#endif
#include <iostream>
int main(int argc, char**) {
    if (argc > 1) cv::ocl::setUseOpenCL(false);
    cv::Mat image(256, 256, CV_8UC1, cv::Scalar(0)), descriptors;
    for (int r = 0; r < image.rows; ++r)
        for (int c = 0; c < image.cols; ++c)
            image.at<unsigned char>(r,c) = static_cast<unsigned char>(
                (r*37+c*17+((r/16+c/16)%2)*83+(r*c)%251)%256);
    std::vector<cv::KeyPoint> points;
    cv::ORB::create()->detectAndCompute(image, cv::noArray(), points, descriptors);
    std::cout << "Direct upstream ORB " << CV_VERSION << ": " << points.size() << '\n';
}