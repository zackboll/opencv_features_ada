# Local host OpenCL runtime leak — preserved diagnostic

OpenCV 4.10.0; selected Alire GCC 16.1.0, Linux x86_64. This is a minimized
upstream-only reproduction, not a defect attributed to Features. No sanitizer
suppression was used. The actual-shim default-runtime run and direct upstream
textured ORB probe report the same totals:

```text
ERROR: LeakSanitizer: detected memory leaks
Direct leak of 2592 byte(s) in 36 object(s) allocated from:
    operator new(unsigned long)
    libhsa-runtime64.so.1+0x6aff5
    BuildId: b6b95ef508da4a05ac4a421d634550f3ed87fd60
Direct leak of 224 byte(s) in 4 object(s) allocated from:
    operator new(unsigned long)
    libhsa-runtime64.so.1+0x6ae52
Direct leak of 160 byte(s) in 4 object(s) allocated from:
    operator new(unsigned long, std::nothrow_t const&)
    amd_comgr_metadata_lookup (libamd_comgr.so.2+0x494f52)
    BuildId: a45964b1a2328f6d641787f3bfa60ae55920c4f7
Other stacks include:
    libamdocl64.so+0x10a191
    BuildId: fc87203a44e06bf3b18dc635ad545ad81b222d1a
    libLLVM-17.so.1+0x16dc517
    BuildId: ca6adac1afa505da5a6236004c61ce968a73043f
    hsaKmtCreateEvent (libhsakmt.so.1+0x69e2)
    BuildId: 192c686b43a615d9796d1db7acfbae7481529b09
SUMMARY: AddressSanitizer: 9724 byte(s) leaked in 173 allocation(s).
```

Reproduce after building, from the root Alire environment:

```sh
alr -n exec -- sh -c '
  g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror -g -O1 \
    -fsanitize=address,undefined -fno-omit-frame-pointer \
    $(pkg-config --cflags opencv4) tests/cpp/upstream_orb_probe.cpp \
    $(pkg-config --libs opencv4) -o obj/sanitizers/upstream-orb
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 \
    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
    obj/sanitizers/upstream-orb
'
```

The default-runtime probe exited 1 on this host; `upstream-orb cpu` exited 0
with the same leak detector enabled. The CPU-only Features driver also exited
0 in both production-source and fault-injection variants. That driver calls
`cv::ocl::setUseOpenCL(false)` in **test main only**, not the binding.
The CPU qualification does not certify this optional GPU ICD or the entire
uninstrumented OpenCV/Core/dependency graph. A blank upstream fixture did not
reach the same initialization; the included reproducer is textured and nonempty.