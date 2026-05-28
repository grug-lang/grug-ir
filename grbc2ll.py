import sys
from pathlib import Path


def compile_grir_to_ll(grir_text: str) -> str:
    ll_lines = []
    lines = [line.strip() for line in grir_text.splitlines() if line.strip()]

    in_func = False
    func_name = ""
    params = []
    ret_type = "void"
    cmp_counter = 0
    fallthrough_counter = 0

    # Map grug types to LLVM types
    type_map = {"number": "double", "id": "i64"}

    i = 0
    while i < len(lines):
        parts = lines[i].split()
        cmd = parts[0]

        if cmd in ("host_fn", "local_fn"):
            if in_func:
                ll_lines.append("}\n")

            in_func = True
            func_name = parts[1]
            params = []
            cmp_counter = 0
            fallthrough_counter = 0
            i += 1

            # Gather parameters and return type
            while i < len(lines):
                sub_parts = lines[i].split()
                if sub_parts[0] == "param":
                    params.append((sub_parts[1], type_map.get(sub_parts[2], "double")))
                    i += 1
                elif sub_parts[0] == "returns":
                    ret_type = type_map.get(sub_parts[1], "void")
                    i += 1
                    break
                else:
                    break

            param_str = ", ".join(f"{t} %{n}" for n, t in params)
            ll_lines.append(f"define {ret_type} @{func_name}({param_str}) {{")
            ll_lines.append("entry:")
            continue

        elif cmd == "if":
            # e.g., if a >= b goto L1
            op1, cond, op2, _, label = parts[1], parts[2], parts[3], parts[4], parts[5]

            # Map grug operators to LLVM floating-point conditions
            cond_map = {
                ">=": "oge",
                "<=": "ole",
                ">": "ogt",
                "<": "olt",
                "==": "oeq",
                "!=": "one",
            }
            llvm_cond = cond_map.get(cond, "oeq")

            cmp_reg = f"%cmp{cmp_counter}"
            cmp_counter += 1
            fallthrough_label = f"fallthrough{fallthrough_counter}"
            fallthrough_counter += 1

            # Distinguish between constants and registers
            def fmt_op(op: str) -> str:
                try:
                    float(op)
                    return op
                except ValueError:
                    return f"%{op}"

            ll_lines.append(
                f"  {cmp_reg} = fcmp {llvm_cond} double {fmt_op(op1)}, {fmt_op(op2)}"
            )
            ll_lines.append(
                f"  br i1 {cmp_reg}, label %{label}, label %{fallthrough_label}"
            )
            ll_lines.append(f"\n{fallthrough_label}:")

        elif cmd == "ret":
            op = parts[1]
            try:
                float(op)
                ll_lines.append(f"  ret {ret_type} {op}")
            except ValueError:
                ll_lines.append(f"  ret {ret_type} %{op}")

        elif cmd.endswith(":"):
            ll_lines.append(f"\n{cmd}")

        i += 1

    if in_func:
        ll_lines.append("}")

    return "\n".join(ll_lines) + "\n"


def main():
    input_file = Path("output_host_fns.grir")
    output_file = Path("output_host_fns.ll")

    if not input_file.exists():
        print(f"Error: {input_file} not found.", file=sys.stderr)
        sys.exit(1)

    grir_text = input_file.read_text(encoding="utf-8")
    ll_text = compile_grir_to_ll(grir_text)
    output_file.write_text(ll_text, encoding="utf-8")
    print(f"Successfully compiled {input_file.name} -> {output_file.name}")


if __name__ == "__main__":
    main()
