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

    # Step 3: Compile and link the LLVM IR with the C test assertions
    run_step(["clang", "output_host_fns.ll", "tests.c", "-o", "tests"])

    # Step 4: Execute the test binary
    test_executable = "./tests" if sys.platform != "win32" else "tests.exe"
    run_step([test_executable])

    print("\nAll pipeline steps completed successfully.")


if __name__ == "__main__":
    main()
