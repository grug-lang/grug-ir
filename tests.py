import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run_step(cmd: list) -> None:
    cmd_str = " ".join(cmd)
    print(f"-> {cmd_str}")
    result = subprocess.run(cmd)
    if result.returncode != 0:  # pragma: no cover
        print(f"FAILED: {cmd_str}", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run the compiler test pipeline.")
    parser.add_argument(
        "--host-c", default="host_fns.c", help="Path to the C host functions file"
    )
    parser.add_argument("--test-c", default="tests.c", help="Path to the C test file")
    parser.add_argument(
        "--out-dir",
        default=".output",
        type=Path,
        help="Directory for all generated artifacts",
    )
    args = parser.parse_args()

    out_dir = args.out_dir

    # Clean slate: remove deep if exists, then recreate
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Define output file paths
    host_fns_grir = str(out_dir / "host_fns.grir")
    host_fns_ll = str(out_dir / "host_fns.ll")
    tests_unlinked_ll = str(out_dir / "tests_unlinked.ll")
    tests_unopt_ll = str(out_dir / "tests_unopt.ll")
    tests_opt_ll = str(out_dir / "tests_opt.ll")
    test_exe = str(out_dir / ("tests.exe" if sys.platform == "win32" else "tests"))

    # Step 1: Run c2grbc.py to yield the .grir TAC representation
    run_step([sys.executable, "c2grbc.py", args.host_c, host_fns_grir])

    # Step 2: Compile the .grir to .ll via grbc2ll.py
    run_step([sys.executable, "grbc2ll.py", host_fns_grir, host_fns_ll])

    # Step 3: Emit LLVM IR for the C tests (-O3 removes alloca boilerplate)
    run_step(
        [
            "clang",
            "-O3",
            "-S",
            "-emit-llvm",
            args.test_c,
            "-o",
            tests_unlinked_ll,
        ]
    )

    # Step 4: Link the host functions and the tests into a single unoptimized IR module
    run_step(
        [
            "llvm-link",
            "-S",
            host_fns_ll,
            tests_unlinked_ll,
            "-o",
            tests_unopt_ll,
        ]
    )

    # Step 5: Run the LLVM optimizer on the linked IR.
    run_step(["opt", "-S", "-O3", tests_unopt_ll, "-o", tests_opt_ll])

    # Step 6: Compile the optimized LLVM IR into the final executable
    run_step(["clang", tests_opt_ll, "-o", test_exe])

    # Step 7: Execute the test binary
    run_step([f"./{test_exe}" if sys.platform != "win32" else test_exe])

    print("\nAll pipeline steps completed successfully.")


if __name__ == "__main__":
    main()
