# Tests

One complete vertical operation at a time: public API, private ABI, native
shim, semantic/negative/ownership tests and documentation. AUnit is test-only.
Exercise empty/no-feature results, masks, noncontiguous Regions, preserved
inputs, result lifetime, descriptor schema, index mapping and invalid configs.

Run static/configuration/helper tests and the native AUnit suite separately.
Written/registered/executed/passed are different counts. ASan/UBSan are normal
development tools; helper-only runs are not native algorithm coverage.
Use real Core handles for native bridge tests. Do not weaken tests to hide an
implementation/environment failure. Record native/compiler versions and SHA.
Windows runs on main/manual, not every PR iteration. No fabricated CI evidence.
