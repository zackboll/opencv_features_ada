# C++ interop

Use C++17 and a small fixed-width C ABI. Never export C++ references, strings,
cv::Mat objects, cv::Ptr, std::vector, templates or exceptions across it.
Every fallible entry initializes its scalar/pointer outputs and contains all
exception types. Do not claim arbitrary C pointer validity can be checked.

Borrow Core native headers only inside scoped callbacks. Do not store/delete
them. Native scratch Mats are allowed, but only Core allocates application
Mat wrappers. Temporary native results need RAII ownership on both sides.

Validate source/mask schema and arithmetic before native execution. Match
OpenCV's actual operation, not an invented algorithm fallback. Re-check bounds
when changing fixed structural parameters. Preserve independent ROI snapshots.
Keep g++/libstdc++ on Linux, Apple clang++/libc++ on macOS, and matching MSYS2
external C++ DLLs on Windows. Do not inject the C++ compiler into Ada's PATH.
