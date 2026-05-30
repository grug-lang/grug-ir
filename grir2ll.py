import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple


def compile_grir_to_ll(grir_text: str) -> str:
    ll_lines: List[str] = []
    lines: List[str] = [line.strip() for line in grir_text.splitlines() if line.strip()]

    in_func: bool = False
    func_name: str = ""
    params_map: Dict[str, str] = {}
    locals_map: Dict[str, str] = {}
    ret_type: str = "void"

    cmp_counter: int = 0
    fallthrough_counter: int = 0
    load_counter: int = 0
    call_counter: int = 0
    op_counter: int = 0

    args_stack: List[Tuple[str, str]] = []
    # (function_name, return_type, tuple_of_arg_types)
    declarations: Set[Tuple[str, str, Tuple[str, ...]]] = set()

    # Map grug types to LLVM types
    type_map: Dict[str, str] = {"number": "double", "id": "i64"}

    def get_val(op: str) -> Tuple[str, str]:
        """Resolves variable types and emits loads for locals."""
        nonlocal load_counter
        try:
            f: float = float(op)
            val: str = str(f) if "." in str(f) else f"{f}.0"
            return ("double", val)
        except ValueError:
            pass

        if op in locals_map:
            reg: str = f"%load{load_counter}"
            load_counter += 1
            ty: str = locals_map[op]
            ll_lines.append(f"  {reg} = load {ty}, ptr %{op}")
            return (ty, reg)
        else:
            assert op in params_map
            return (params_map[op], f"%{op}")

    i: int = 0
    while i < len(lines):
        parts: List[str] = lines[i].split()
        cmd: str = parts[0]

        if cmd in ("host_fn", "local_fn", "export_fn"):
            if in_func:
                # Close out previous function safely
                last_line: str = ll_lines[-1].strip() if ll_lines else ""
                if ret_type == "void" and not last_line.startswith(("ret", "br")):
                    ll_lines.append("  ret void")
                ll_lines.append("}\n")

            in_func = True
            func_name = parts[1]
            params_list: List[Tuple[str, str]] = []
            params_map.clear()
            locals_map.clear()
            args_stack.clear()

            cmp_counter = 0
            fallthrough_counter = 0
            load_counter = 0
            call_counter = 0
            op_counter = 0
            ret_type = "void"
            i += 1

            # Gather parameters and return type
            while i < len(lines):
                sub_parts: List[str] = lines[i].split()
                if sub_parts[0] == "param":
                    p_name: str = sub_parts[1]
                    p_type: str = type_map.get(sub_parts[2], "double")
                    params_list.append((p_name, p_type))
                    params_map[p_name] = p_type
                    i += 1
                elif sub_parts[0] == "returns":
                    ret_type = type_map.get(sub_parts[1], "void")
                    i += 1
                    break
                else:
                    break

            param_str: str = ", ".join(f"{t} %{n}" for n, t in params_list)
            ll_lines.append(f"define {ret_type} @{func_name}({param_str}) {{")
            ll_lines.append("entry:")
            continue

        elif cmd == "local":
            var_name: str = parts[1]
            g_type: str = parts[2] if len(parts) > 2 else "number"
            ty = type_map.get(g_type, "double")
            locals_map[var_name] = ty
            ll_lines.append(f"  %{var_name} = alloca {ty}")

        elif cmd == "arg":
            ty, val = get_val(parts[1])
            args_stack.append((ty, val))

        elif cmd == "call" or (
            len(parts) >= 3 and parts[1] == "=" and parts[2] == "call"
        ):
            if cmd == "call":
                f_name: str = parts[1]
                dest_var: str | None = None
            else:
                dest_var = parts[0]
                f_name = parts[3]

            call_args: List[Tuple[str, str]] = list(args_stack)
            args_stack.clear()

            arg_str: str = ", ".join(f"{t} {v}" for t, v in call_args)

            if dest_var:
                if dest_var in locals_map:
                    r_ty: str = locals_map[dest_var]
                else:  # pragma: no cover # TODO: Remove prama, since reassigning params is allowed in grug (for now)
                    assert dest_var in params_map
                    r_ty = params_map[dest_var]
            else:
                r_ty = "void"

            # Register declaration for external linking
            declarations.add((f_name, r_ty, tuple(t for t, _v in call_args)))

            if dest_var:
                reg = f"%call{call_counter}"
                call_counter += 1
                ll_lines.append(f"  {reg} = call {r_ty} @{f_name}({arg_str})")
                if dest_var in locals_map:
                    ll_lines.append(f"  store {r_ty} {reg}, ptr %{dest_var}")
            else:
                ll_lines.append(f"  call {r_ty} @{f_name}({arg_str})")

        elif (
            len(parts) >= 3 and parts[1] == "=" and parts[2] != "call"
        ):  # pragma: no cover # TODO: Remove pragma, since this just requires `local_var = 10`
            # Variable assignments: var = val OR var = a op b
            dest_var = parts[0]
            if len(parts) == 3:
                ty, val = get_val(parts[2])
                if dest_var in locals_map:
                    ll_lines.append(f"  store {ty} {val}, ptr %{dest_var}")
            elif len(parts) == 5:
                ty1, val1 = get_val(parts[2])
                op: str = parts[3]
                _ty2, val2 = get_val(parts[4])
                reg = f"%op{op_counter}"
                op_counter += 1

                instr: str = (
                    "fadd"
                    if op == "+"
                    else "fsub" if op == "-" else "fmul" if op == "*" else "fdiv"
                )
                ll_lines.append(f"  {reg} = {instr} {ty1} {val1}, {val2}")
                if dest_var in locals_map:
                    ll_lines.append(f"  store {ty1} {reg}, ptr %{dest_var}")

        elif cmd == "if":
            op1, cond, op2, _, label = parts[1], parts[2], parts[3], parts[4], parts[5]
            cond_map: Dict[str, str] = {
                ">=": "oge",
                "<=": "ole",
                ">": "ogt",
                "<": "olt",
                "==": "oeq",
                "!=": "one",
            }
            llvm_cond: str = cond_map.get(cond, "oeq")
            cmp_reg: str = f"%cmp{cmp_counter}"
            cmp_counter += 1
            fallthrough_label: str = f"fallthrough{fallthrough_counter}"
            fallthrough_counter += 1

            ty1, val1 = get_val(op1)
            _ty2, val2 = get_val(op2)
            ll_lines.append(f"  {cmp_reg} = fcmp {llvm_cond} {ty1} {val1}, {val2}")
            ll_lines.append(
                f"  br i1 {cmp_reg}, label %{label}, label %{fallthrough_label}"
            )
            ll_lines.append(f"\n{fallthrough_label}:")

        elif cmd == "ret":
            op = parts[1]
            ty, val = get_val(op)
            ll_lines.append(f"  ret {ret_type} {val}")

        elif cmd.endswith(":"):
            ll_lines.append(f"\n{cmd}")

        i += 1

    if in_func:
        last_line = ll_lines[-1].strip() if ll_lines else ""
        if ret_type == "void" and not last_line.startswith(("ret", "br")):
            ll_lines.append("  ret void")
        ll_lines.append("}\n")

    # Emit function declarations at the top for resolving cross-module symbols
    decl_lines: List[str] = []
    defined_funcs: Set[str] = {
        line.strip().split()[1]
        for line in lines
        if line.strip().split()
        and line.strip().split()[0] in ("host_fn", "local_fn", "export_fn")
    }

    for f_name, r_ty, arg_types in sorted(list(declarations)):
        if f_name not in defined_funcs:
            arg_str = ", ".join(arg_types)
            decl_lines.append(f"declare {r_ty} @{f_name}({arg_str})")

    return "\n".join(decl_lines + ll_lines)


def main():
    parser = argparse.ArgumentParser(description="Compile .grir representation to .ll")
    parser.add_argument("input", type=Path, help="Path to the input .grir file")
    parser.add_argument("output", type=Path, help="Path for the output .ll file")
    args = parser.parse_args()

    grir_text = args.input.read_text(encoding="utf-8")
    ll_text = compile_grir_to_ll(grir_text)
    args.output.write_text(ll_text, encoding="utf-8")
    print(f"Successfully compiled {args.input.name} -> {args.output.name}")


if __name__ == "__main__":
    main()
