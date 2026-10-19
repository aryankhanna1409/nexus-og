# Aegis-Net top-level Makefile.
# Targets are added milestone by milestone; see IMPLEMENTATION_PLAN.md.

C_DIR        := c-library
C_BUILD      := $(C_DIR)/build
C_BUILD_ASAN := $(C_DIR)/build-asan
JOBS         ?= $(shell nproc 2>/dev/null || echo 4)

.PHONY: help c-build c-test c-test-asan test clean

help:
	@echo "Targets:"
	@echo "  c-build      Build libcallanalyzer (warnings as errors)"
	@echo "  c-test       Build and run the C test suite"
	@echo "  c-test-asan  Build and run the C tests with ASan/UBSan/LSan"
	@echo "  test         Run all available test suites"
	@echo "  clean        Remove build artifacts"

c-build:
	cmake -S $(C_DIR) -B $(C_BUILD) -DCMAKE_BUILD_TYPE=RelWithDebInfo
	cmake --build $(C_BUILD) -j $(JOBS)

c-test: c-build
	ctest --test-dir $(C_BUILD) --output-on-failure

c-test-asan:
	cmake -S $(C_DIR) -B $(C_BUILD_ASAN) -DCMAKE_BUILD_TYPE=Debug -DCA_ENABLE_SANITIZERS=ON
	cmake --build $(C_BUILD_ASAN) -j $(JOBS)
	ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
		ctest --test-dir $(C_BUILD_ASAN) --output-on-failure

test: c-test c-test-asan

clean:
	rm -rf $(C_BUILD) $(C_BUILD_ASAN)
