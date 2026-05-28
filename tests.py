import subprocess
import sys


def run_step(cmd: list) -> None:
    cmd_str = " ".join(cmd)
    print(f"-> {cmd_str}")
    result = subprocess.run(cmd)
    if result.returncode != 0:  # pragma: no cover
        print(f"FAILED: {cmd_str}", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    # Step 1: Run the (currently stubbed) c2grbc.py to yield output_host_fns.grir
    run_step([sys.executable, "c2grbc.py"])

    # Step 2: Compile the .grir TAC representation to .ll via grbc2ll.py
    run_step([sys.executable, "grbc2ll.py"])

    # Step 3: Emit LLVM IR for the C tests (-O3 removes alloca boilerplate)
    run_step(["clang", "-O3", "-S", "-emit-llvm", "tests.c", "-o", "output_tests_unlinked.ll"])

    # Step 4: Link the host functions and the tests into a single unoptimized IR module
    run_step(
        [
            "llvm-link",
            "-S",
            "output_host_fns.ll",
            "output_tests_unlinked.ll",
            "-o",
            "output_tests_unopt.ll",
        ]
    )

    # Step 5: Run the LLVM optimizer on the linked IR.
    # This generates the optimal .ll file (output_tests_opt.ll) for your inspection.
    run_step(["opt", "-S", "-O3", "output_tests_unopt.ll", "-o", "output_tests_opt.ll"])

    # Step 6: Compile the optimized LLVM IR into the final executable
    run_step(["clang", "output_tests_opt.ll", "-o", "tests"])

    # Step 7: Execute the test binary
    test_executable = "./tests" if sys.platform != "win32" else "tests.exe"
    run_step([test_executable])

    print("\nAll pipeline steps completed successfully.")


if __name__ == "__main__":
    main()
