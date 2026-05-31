import difflib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Union


def run_step(cmd: List[str]) -> None:
    cmd_str = " ".join(cmd)
    print(f"-> {cmd_str}")
    result = subprocess.run(cmd)
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
            exp_lines, out_lines, fromfile=str(exp_file), tofile=str(out_file)
        )
        sys.stdout.writelines(diff)
        sys.exit(1)

    print(f"-> OK: {out_file.name} matches {exp_file.name}")


def get_llvm_config(args: List[str]) -> List[str]:
    return subprocess.check_output(["llvm-config"] + args).decode().split()


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
    creeper_grug = str(test_dir / "creeper-Entity.grug")
    creeper_grir = str(out_dir / "creeper-Entity.grir")
    creeper_ll = str(out_dir / "creeper-Entity.ll")
    test_exe = str(out_dir / ("main.exe" if sys.platform == "win32" else "main.out"))

    # 1-4. Compile .c/.grug -> .grir -> .ll targets
    run_step(["coverage", "run", "--append", "c2grir.py", str(host_c), host_fns_grir])
    run_step(["coverage", "run", "--append", "grir2ll.py", host_fns_grir, host_fns_ll])
    run_step(
        ["coverage", "run", "--append", "compile_grug.py", creeper_grug, creeper_grir]
    )
    run_step(["coverage", "run", "--append", "grir2ll.py", creeper_grir, creeper_ll])

    # 5. Compile JIT loader dynamically tracking LLVM system libs
    llvm_cflags = get_llvm_config(["--cflags"])
    llvm_ldflags = get_llvm_config(["--ldflags"])
    llvm_libs = get_llvm_config(
        [
            "--libs",
            "core",
            "executionengine",
            "mcjit",
            "irreader",
            "linker",
            "target",
            "native",
            "ipo",
        ]
    )
    llvm_syslibs = get_llvm_config(["--system-libs"])

    run_step(
        ["clang", str(main_c), "-o", test_exe]
        + llvm_cflags
        + llvm_ldflags
        + llvm_libs
        + llvm_syslibs
    )

    # 6. Execute JIT
    run_step([f"./{test_exe}" if sys.platform != "win32" else test_exe])

    # 7. Verify outputs strictly
    print("\nVerifying outputs...")
    check_diff(host_fns_grir, expected_dir / "host_fns.grir")
    check_diff(host_fns_ll, expected_dir / "host_fns.ll")
    check_diff(creeper_grir, expected_dir / "creeper-Entity.grir")
    check_diff(creeper_ll, expected_dir / "creeper-Entity.ll")

    # 8. Run FileCheck against the generated mods.ll
    run_step(
        [
            "FileCheck",
            str(expected_dir / "mods.ll"),
            "--input-file",
            str(out_dir / "mods.ll"),
        ]
    )

    print(f"\nTest '{test_dir.name}' completed successfully.")


def main() -> None:
    tests_dir = Path("tests")
    test_dirs = sorted(p for p in tests_dir.iterdir() if p.is_dir())
    for test_dir in test_dirs:
        run_test(test_dir)
    print("\nAll tests completed successfully.")


if __name__ == "__main__":
    main()
