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
    declarations: Set[Tuple[str, str, Tuple[str, ...]]] = set()

    # Map grug types to LLVM types
    type_map: Dict[str, str] = {
        "number": "double",
        "id": "i64",
        "bool": "i1",
        "void": "void",
    }

    def get_val(op: str) -> Tuple[str, str]:
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
                last_line: str = ll_lines[-1].strip() if ll_lines else ""
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
                dest_var = None
            else:
                dest_var = parts[0]
                f_name = parts[3]

            call_args: List[Tuple[str, str]] = list(args_stack)
            args_stack.clear()
            arg_str: str = ", ".join(f"{t} {v}" for t, v in call_args)

            if dest_var:
                r_ty: str = locals_map.get(dest_var, params_map.get(dest_var, "double"))
            else:
                r_ty = "void"

            declarations.add((f_name, r_ty, tuple(t for t, _v in call_args)))

            if dest_var:
                reg = f"%call{call_counter}"
                call_counter += 1
                ll_lines.append(f"  {reg} = call {r_ty} @{f_name}({arg_str})")
                if dest_var in locals_map:
                    ll_lines.append(f"  store {r_ty} {reg}, ptr %{dest_var}")
            else:
                ll_lines.append(f"  call {r_ty} @{f_name}({arg_str})")

        elif len(parts) >= 3 and parts[1] == "=" and parts[2] != "call":
            dest_var = parts[0]
            if len(parts) == 5:
                ty1, val1 = get_val(parts[2])
                op: str = parts[3]
                _ty2, val2 = get_val(parts[4])
                reg = f"%op{op_counter}"
                op_counter += 1

                if op in ("==", "!=", ">", "<", ">=", "<="):
                    cond_map = {
                        "==": "oeq",
                        "!=": "one",
                        ">": "ogt",
                        "<": "olt",
                        ">=": "oge",
                        "<=": "ole",
                    }
                    instr = cond_map[op]
                    ll_lines.append(f"  {reg} = fcmp {instr} {ty1} {val1}, {val2}")
                    if dest_var in locals_map:
                        ll_lines.append(f"  store i1 {reg}, ptr %{dest_var}")

        elif cmd == "if":
            op1, cond, op2, _, label = parts[1], parts[2], parts[3], parts[4], parts[5]
            ty1, val1 = get_val(op1)
            _ty2, val2 = get_val(op2)

            cmp_reg = f"%cmp{cmp_counter}"
            cmp_counter += 1
            fallthrough_label = f"fallthrough{fallthrough_counter}"
            fallthrough_counter += 1

            if ty1 == "i1":
                cond_map = {"==": "eq", "!=": "ne"}
                llvm_cond = cond_map.get(cond, "eq")
                val2_i1 = "0" if "0" in val2 else "1"
                ll_lines.append(f"  {cmp_reg} = icmp {llvm_cond} i1 {val1}, {val2_i1}")
            else:
                cond_map = {
                    ">=": "oge",
                    "<=": "ole",
                    ">": "ogt",
                    "<": "olt",
                    "==": "oeq",
                    "!=": "one",
                }
                llvm_cond = cond_map.get(cond, "oeq")
                ll_lines.append(f"  {cmp_reg} = fcmp {llvm_cond} {ty1} {val1}, {val2}")

            ll_lines.append(
                f"  br i1 {cmp_reg}, label %{label}, label %{fallthrough_label}"
            )
            ll_lines.append(f"\n{fallthrough_label}:")

        elif cmd == "return":
            assert len(parts) > 1
            ty, val = get_val(parts[1])
            ll_lines.append(f"  ret {ret_type} {val}")

        elif cmd.endswith(":"):
            label_name = cmd[:-1]
            last = next((l.strip() for l in reversed(ll_lines) if l.strip()), "")
            if not last.startswith(("ret ", "br ")):
                ll_lines.append(f"  br label %{label_name}")
            ll_lines.append(f"\n{cmd}")

        i += 1

    if in_func:
        last_line = ll_lines[-1].strip() if ll_lines else ""
        if ret_type == "void" and not last_line.startswith(("return", "br")):
            ll_lines.append("  ret void")
        ll_lines.append("}\n")

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


if __name__ == "__main__":
    main()
