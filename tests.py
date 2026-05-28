import argparse
import difflib
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


def check_diff(out_path: str | Path, expected_path: str | Path) -> None:
    out_file = Path(out_path)
    exp_file = Path(expected_path)

    if not exp_file.exists():
        print(f"-> WARNING: Expected file {exp_file} not found. Skipping diff.")
        return

    out_lines = out_file.read_text(encoding="utf-8").splitlines(keepends=True)
    exp_lines = exp_file.read_text(encoding="utf-8").splitlines(keepends=True)

    if out_lines != exp_lines:
        print(f"FAILED: Mismatch found for {out_file.name}", file=sys.stderr)
        diff = difflib.unified_diff(
            exp_lines,
            out_lines,
            fromfile=str(exp_file),
            tofile=str(out_file),
        )
        sys.stdout.writelines(diff)
        sys.exit(1)

    print(f"-> OK: {out_file.name} matches {exp_file.name}")


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
    parser.add_argument(
        "--expected-dir",
        default="expected",
        type=Path,
        help="Directory containing expected artifacts to diff against",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    expected_dir = args.expected_dir

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

    # Run c2grir.py to yield the .grir TAC representation
    run_step([sys.executable, "c2grir.py", args.host_c, host_fns_grir])

    # Compile the .grir to .ll via grir2ll.py
    run_step([sys.executable, "grir2ll.py", host_fns_grir, host_fns_ll])

    # Emit LLVM IR for the C tests (-O3 removes alloca boilerplate)
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

    # Link the host functions and the tests into a single unoptimized IR module
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

    # Run the LLVM optimizer on the linked IR.
    run_step(["opt", "-S", "-O3", tests_unopt_ll, "-o", tests_opt_ll])

    # Compile the optimized LLVM IR into the final executable
    run_step(["clang", tests_opt_ll, "-o", test_exe])

    # Execute the test binary
    run_step([f"./{test_exe}" if sys.platform != "win32" else test_exe])

    # Verify generated artifacts against expected
    print("\nVerifying outputs...")
    check_diff(host_fns_grir, expected_dir / "host_fns.grir")
    check_diff(host_fns_ll, expected_dir / "host_fns.ll")
    check_diff(tests_unlinked_ll, expected_dir / "tests_unlinked.ll")
    check_diff(tests_unopt_ll, expected_dir / "tests_unopt.ll")
    check_diff(tests_opt_ll, expected_dir / "tests_opt.ll")

    print("\nAll pipeline steps and diff checks completed successfully.")


if __name__ == "__main__":
    main()
