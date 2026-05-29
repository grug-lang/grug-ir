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
        print(f"-> FAILED: {cmd_str}", file=sys.stderr)
        sys.exit(result.returncode)


def check_diff(out_path: str | Path, expected_path: str | Path) -> None:
    out_file = Path(out_path)
    exp_file = Path(expected_path)

    if not exp_file.exists():
        sys.exit(f"-> FAILED: Expected file {exp_file} not found.")

    out_lines = out_file.read_text(encoding="utf-8").splitlines(keepends=True)
    exp_lines = exp_file.read_text(encoding="utf-8").splitlines(keepends=True)

    if out_lines != exp_lines:
        print(f"-> FAILED: Mismatch found for {out_file.name}", file=sys.stderr)
        diff = difflib.unified_diff(
            exp_lines,
            out_lines,
            fromfile=str(exp_file),
            tofile=str(out_file),
        )
        sys.stdout.writelines(diff)
        sys.exit(1)

    print(f"-> OK: {out_file.name} matches {exp_file.name}")


def run_filecheck(actual_path: Path, expected_path: Path) -> None:
    """Verifies actual_path using FileCheck directives found in expected_path."""
    if not shutil.which("FileCheck"):
        sys.exit("-> FAILED: 'FileCheck' not found in PATH. Please install LLVM tools.")

    cmd = ["FileCheck", str(expected_path), "--input-file", str(actual_path)]

    print(f"-> Running FileCheck on {actual_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(
            f"-> FAILED: FileCheck verification failed for {actual_path.name}",
            file=sys.stderr,
        )
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(f"-> OK: {actual_path.name} passed FileCheck verification")


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

    # Clean slate
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Define output file paths
    host_fns_grir = str(out_dir / "host_fns.grir")
    host_fns_ll = str(out_dir / "host_fns.ll")
    tests_ll = str(out_dir / "tests.ll")
    tests_bc = str(out_dir / "tests.bc")
    test_exe = str(out_dir / ("tests.exe" if sys.platform == "win32" else "tests"))

    # 1. Run c2grir.py to yield the .grir TAC representation
    run_step([sys.executable, "c2grir.py", args.host_c, host_fns_grir])

    # 2. Compile the .grir to .ll via grir2ll.py
    run_step([sys.executable, "grir2ll.py", host_fns_grir, host_fns_ll])

    # 3. Optimized LTO Link: Generate binary bitcode (.bc)
    run_step(
        [
            "clang",
            "-O3",
            "-fuse-ld=lld",
            "-flto",
            "-Wl,--plugin-opt=emit-llvm",
            host_fns_ll,
            args.test_c,
            "-o",
            tests_bc,
        ]
    )

    # 4. Disassemble binary bitcode to text IR (.ll) using clang
    run_step(["clang", "-x", "ir", tests_bc, "-S", "-emit-llvm", "-o", tests_ll])

    # 5. Compile final executable from the optimized .ll
    run_step(["clang", tests_ll, "-o", test_exe])

    # 6. Execute tests
    run_step([f"./{test_exe}" if sys.platform != "win32" else test_exe])

    # 7. Verify outputs
    print("\nVerifying outputs...")

    # Use strict diff for grug's stable IR
    check_diff(host_fns_grir, expected_dir / "host_fns.grir")
    check_diff(host_fns_ll, expected_dir / "host_fns.ll")

    # Use FileCheck for Clang's unstable IR
    run_filecheck(Path(tests_ll), expected_dir / "tests.ll")

    print("\nAll pipeline steps and checks completed successfully.")


if __name__ == "__main__":
    main()
