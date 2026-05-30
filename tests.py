import difflib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union


def run_step(cmd: List[str], env: Optional[Dict[str, str]] = None) -> None:
    cmd_str = " ".join(cmd)
    print(f"-> {cmd_str}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(f"-> FAILED: {cmd_str}", file=sys.stderr)
        sys.exit(result.returncode)


def check_diff(out_path: Union[str, Path], expected_path: Union[str, Path]) -> None:
    out_file = Path(out_path)
    exp_file = Path(expected_path)

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


def run_test(test_dir: Path) -> None:
    host_c = test_dir / "host_fns.c"
    main_c = test_dir / "main.c"
    expected_dir = test_dir / "expected"

    print(f"\n{'=' * 60}")
    print(f"Running test: {test_dir.name}")
    print(f"{'=' * 60}")

    out_dir = test_dir / ".output"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    host_fns_grir = str(out_dir / "host_fns.grir")
    host_fns_ll = str(out_dir / "host_fns.ll")
    tests_ll = str(out_dir / "tests.ll")
    tests_bc = str(out_dir / "tests.bc")
    test_exe = str(out_dir / ("main.exe" if sys.platform == "win32" else "main.out"))

    env = os.environ.copy()
    env["COVERAGE_PROCESS_START"] = ".coveragerc"

    # 1. Run c2grir.py to yield the .grir TAC representation
    run_step(["coverage", "run", "--append", "c2grir.py", str(host_c), host_fns_grir], env=env)

    # 2. Compile the .grir to .ll via grir2ll.py
    run_step(["coverage", "run", "--append", "grir2ll.py", host_fns_grir, host_fns_ll], env=env)

    # 3. Optimized LTO Link: Generate binary bitcode (.bc)
    run_step(
        [
            "clang",
            "-O3",
            "-fuse-ld=lld",
            "-flto",
            "-Wl,--plugin-opt=emit-llvm",
            host_fns_ll,
            str(main_c),
            "-o",
            tests_bc,
        ]
    )

    # 4. Disassemble binary bitcode to text IR (.ll) using clang
    run_step(["clang", "-x", "ir", tests_bc, "-S", "-emit-llvm", "-o", tests_ll])

    # 5. Compile final executable from the optimized .ll
    run_step(["clang", tests_ll, "-o", test_exe])

    # 6. Execute program
    run_step([f"./{test_exe}" if sys.platform != "win32" else test_exe])

    # 7. Verify outputs
    print("\nVerifying outputs...")

    # Use strict diff for grug's stable IR
    check_diff(host_fns_grir, expected_dir / "host_fns.grir")
    check_diff(host_fns_ll, expected_dir / "host_fns.ll")

    # Use FileCheck for Clang's unstable IR
    run_filecheck(Path(tests_ll), expected_dir / "tests.ll")

    print(f"\nTest '{test_dir.name}' completed successfully.")


def main() -> None:
    tests_dir = Path("tests")

    test_dirs = sorted(p for p in tests_dir.iterdir() if p.is_dir())

    for test_dir in test_dirs:
        run_test(test_dir)

    print("\nAll tests completed successfully.")


if __name__ == "__main__":
    main()
