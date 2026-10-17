// SPDX-License-Identifier: Apache-2.0
// Research only. Exercise installed ORB, then inventory the loaded modules.
#include <opencv2/core.hpp>
#include <opencv2/core/ocl.hpp>
#include <opencv2/core/version.hpp>
#if CV_VERSION_MAJOR == 4
#include <opencv2/features2d.hpp>
#else
#include <opencv2/features.hpp>
#endif
#include <cfenv>
#include <cfloat>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#include <windows.h>
#include <tlhelp32.h>
#elif defined(__APPLE__)
#include <mach-o/dyld.h>
#else
#include <fstream>
#endif

static void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

static void powers() {
    require(sizeof(int) == 4 && FLT_RADIX == 2, "integer/radix premise");
    require(FLT_MANT_DIG == 24 && DBL_MANT_DIG == 53, "IEEE width premise");
    require(std::numeric_limits<float>::is_iec559, "binary32 premise");
    require(FLT_EVAL_METHOD == 0, "evaluation-method premise");
#ifdef __FAST_MATH__
    throw std::runtime_error("fast-math configuration is not qualified");
#endif
    require(std::fesetround(FE_TONEAREST) == 0, "cannot select nearest rounding");
    require(std::fegetround() == FE_TONEAREST, "rounding mode changed");
    const double scale = 1.2f;
    const float factor = float(1.0 / scale);
    require(scale == 0x1.333334p+0 && factor == 0x1.aaaaaap-1f, "stored constants");
    std::cout << std::hexfloat;
    std::cout << "POWER_ENV FLT_EVAL_METHOD=" << FLT_EVAL_METHOD
              << " rounding=" << std::fegetround() << '\n';
    std::cout << "INPUT scale " << scale << " factor " << factor << '\n';
    for (int level = 1; level <= 8; ++level) {
        volatile double base = factor, exponent = level;
        const double power = std::pow(base, exponent);
        const float stored = float(power);
        std::cout << "POWER factor " << level << ' ' << power
                  << " stored " << stored << '\n';
    }
    for (int level = 0; level < 8; ++level) {
        volatile double base = scale, exponent = level;
        const double power = std::pow(base, exponent);
        const float stored = float(power);
        require(stored >= 1.f && stored < 4.f, "scale store envelope");
        std::cout << "POWER scale " << level << ' ' << power
                  << " stored " << stored << '\n';
    }
    std::cout << "PASS R3E fixed powers\n";
}

static void modules() {
#ifdef _WIN32
    const HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, GetCurrentProcessId());
    require(snapshot != INVALID_HANDLE_VALUE, "module snapshot failed");
    MODULEENTRY32 entry{};
    entry.dwSize = sizeof(entry);
    require(Module32First(snapshot, &entry), "module enumeration failed");
    do { std::cout << "LOADED " << entry.szExePath << '\n'; }
    while (Module32Next(snapshot, &entry));
    CloseHandle(snapshot);
#elif defined(__APPLE__)
    for (uint32_t index = 0; index < _dyld_image_count(); ++index)
        std::cout << "LOADED " << _dyld_get_image_name(index) << '\n';
#else
    std::ifstream maps("/proc/self/maps");
    require(maps.good(), "module map unavailable");
    std::string line;
    while (std::getline(maps, line)) {
        const auto slash = line.rfind(" /");
        if (slash == std::string::npos) continue;
        const std::string path = line.substr(slash + 1);
        if (path.find("libopencv_features") != std::string::npos) {
            std::cout << "LOADED " << path << '\n';
            break;
        }
    }
#endif
}

static void extraction(bool disable_opencl) {
    if (disable_opencl) cv::ocl::setUseOpenCL(false);
    std::cout << "OPENCL have=" << cv::ocl::haveOpenCL()
              << " use=" << cv::ocl::useOpenCL()
              << " disabled=" << int(disable_opencl) << '\n';
    cv::Mat image(96, 128, CV_8UC1);
    for (int row = 0; row < image.rows; ++row)
        for (int column = 0; column < image.cols; ++column)
            image.at<unsigned char>(row, column) = static_cast<unsigned char>(
                (row * 37 + column * 17 + ((row / 8 + column / 8) % 2) * 83) % 256);
    require(image.type() == CV_8UC1 && image.isContinuous(), "CPU Mat input");
    auto orb = cv::ORB::create(500, 1.2f, 8, 31, 0, 2, cv::ORB::HARRIS_SCORE, 31, 20);
    require(orb->getNLevels() == 8, "ORB level profile");
    std::vector<cv::KeyPoint> points;
    cv::Mat descriptors;
    orb->detectAndCompute(image, cv::noArray(), points, descriptors, false);
    require(!points.empty(), "native extraction returned no keypoints");
    require(descriptors.rows == int(points.size()), "descriptor rows unpaired");
    require(descriptors.cols == 32 && descriptors.type() == CV_8UC1, "descriptor schema");
    for (const auto& point : points)
        require(point.octave >= 0 && point.octave < 8, "octave outside configured levels");
    std::cout << "ORB_EXTRACTION keypoints=" << points.size()
              << " rows=" << descriptors.rows
              << " input=CV_8UC1 continuous=1 levels=8\n";
    std::cout << "PASS native ORB extraction\n";
}

int main(int argc, char** argv) {
    require(argc == 2, "usage: orb_r3e_native_probe {cpu,opencl-observe,powers}");
    const std::string mode = argv[1];
    std::cout << "OpenCV=" << CV_VERSION << " compiler=" << __VERSION__ << '\n';
    if (mode == "powers") {
        powers();
    } else if (mode == "cpu") {
        extraction(true);
        std::cout << "BUILD_INFORMATION\n" << cv::getBuildInformation();
        modules();
    } else if (mode == "opencl-observe") {
        extraction(false);
        modules();
    } else {
        throw std::runtime_error("unknown probe mode");
    }
}
