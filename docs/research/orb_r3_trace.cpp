// SPDX-License-Identifier: Apache-2.0
// Research only: inventory intermediate stores alongside the unchanged R2 probe.
#include <opencv2/core.hpp>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#include <tlhelp32.h>
#elif defined(__APPLE__)
#include <mach-o/dyld.h>
#endif

int main() {
    const double scale = 1.2f;
    const double reciprocal = 1.0 / scale;
    const float factor = float(reciprocal);
    std::cout << std::hexfloat << "RECIPROCAL64 " << reciprocal << '\n';
    for (int n : {1, 2, 3, 500, 16777217, INT32_MAX / 2}) {
        for (int levels = 1; levels <= 8; ++levels) {
            const double power = std::pow(double(factor), double(levels));
            const float stored = float(power);
            const float numerator = n * (1 - factor);
            const float denominator = 1 - stored;
            float share = numerator / denominator;
            std::cout << "INITIAL " << n << ' ' << levels << ' ' << power << ' '
                      << stored << ' ' << numerator << ' ' << denominator << ' ' << share << '\n';
            std::int64_t sum = 0;
            for (int level = 0; level < levels - 1; ++level) {
                const int target = cvRound(share);
                std::cout << "SHARE " << n << ' ' << levels << ' ' << level << ' '
                          << share << ' ' << target << '\n';
                sum += target;
                share *= factor;
            }
            std::cout << "RESIDUAL " << n << ' ' << levels << ' '
                      << std::max(std::int64_t(n) - sum, std::int64_t(0)) << '\n';
        }
    }
    for (int level = 0; level < 8; ++level) {
        const double power = std::pow(scale, double(level));
        const float stored = float(power);
        std::cout << "SCALE_STORE " << level << ' ' << power << ' ' << stored
                  << ' ' << (1.f / stored) << '\n';
    }
    // Force OpenCV loading before enumerating modules.
    std::cout << "BUILD_INFORMATION\n" << cv::getBuildInformation();
#ifdef _WIN32
    const HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, GetCurrentProcessId());
    if (snapshot == INVALID_HANDLE_VALUE) throw std::runtime_error("module snapshot failed");
    MODULEENTRY32 entry{};
    entry.dwSize = sizeof(entry);
    if (!Module32First(snapshot, &entry)) throw std::runtime_error("module enumeration failed");
    do { std::cout << "LOADED " << entry.szExePath << '\n'; }
    while (Module32Next(snapshot, &entry));
    CloseHandle(snapshot);
#elif defined(__APPLE__)
    for (uint32_t index = 0; index < _dyld_image_count(); ++index)
        std::cout << "LOADED " << _dyld_get_image_name(index) << '\n';
#endif
    return 0;
}