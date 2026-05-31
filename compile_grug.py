import re
import sys
from typing import Any, Dict, List, Optional


def compile_grug(source_code: str) -> str:
    # Strip out comments before lexing
    source_code = re.sub(r"#.*", "", source_code)

    # 1. Lexer: Tokenize identifiers, floats, operators, and basic syntax
    tokens: List[str] = re.findall(
        r"[a-zA-Z_]\w*|\d+(?:\.\d+)?|==|[(){},]", source_code
    )
    pos: int = 0

    def peek() -> str:
        return tokens[pos] if pos < len(tokens) else ""

    def consume() -> str:
        nonlocal pos
        res = tokens[pos]
        pos += 1
        return res

    # 2. Parser: Build a simple AST
    def parse_expr() -> Dict[str, Any]:
        tok = consume()
        if tok[0].isdigit():
            left: Dict[str, Any] = {"type": "num", "val": tok}
        else:
            assert peek() == "("
            consume()  # '('
            args: List[Dict[str, Any]] = []
            while peek() != ")":
                args.append(parse_expr())
                if peek() == ",":
                    consume()  # ','
            consume()  # ')'
            left = {"type": "call", "name": tok, "args": args}

        # Handle inline equality operators immediately after functions/numbers
        if peek() == "==":
            consume()  # '=='
            right = parse_expr()
            return {"type": "binop", "op": "==", "left": left, "right": right}

        return left

    def parse_fn() -> Dict[str, Any]:
        consume()  # 'export'
        name = consume()
        consume()  # '('
        consume()  # ')'
        consume()  # '{'
        exprs: List[Dict[str, Any]] = []
        while peek() != "}":
            exprs.append(parse_expr())
        consume()  # '}'
        return {"name": name, "body": exprs}

    ast = parse_fn()

    # 3. Code Generator: Flatten the AST into GRIR TAC instructions
    instructions: List[str] = []
    temp_count: int = 1

    def generate_expr(node: Dict[str, Any], is_stmt: bool = False) -> Optional[str]:
        nonlocal temp_count
        if node["type"] == "num":
            return node["val"]
        elif node["type"] == "binop":
            left_val = generate_expr(node["left"])
            right_val = generate_expr(node["right"])
            tmp = f"t{temp_count}"
            temp_count += 1
            # Declare inline with type
            instructions.append(f"{tmp}: bool = {left_val} {node['op']} {right_val}")
            return tmp
        else:
            assert node["type"] == "call"
            # Evaluate inner arguments first
            arg_vals = [generate_expr(arg) for arg in node["args"]]

            # Emit arguments
            for val in arg_vals:
                instructions.append(f"arg {val}")

            if is_stmt:
                instructions.append(f"call {node['name']}")
                return None
            else:
                tmp = f"t{temp_count}"
                temp_count += 1
                # Declare inline with type
                instructions.append(f"{tmp}: number = call {node['name']}")
                return tmp

    for stmt in ast["body"]:
        generate_expr(stmt, is_stmt=True)

    # Combine into final GRIR format with 4-space indentation
    header = f"export {ast['name']}()"
    indented_instrs = [f"    {line}" for line in instructions]

    # All functions must end with a return
    lines: List[str] = [header] + indented_instrs + ["    return"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 3:  # pragma: no cover
        sys.exit("Usage: python compile_grug.py <input.grug> <output.grir>")

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        source = f.read()

    grir_output = compile_grug(source)

    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(grir_output)
