import re
import sys
from typing import Any, Dict, List, Optional


def compile_grug(source_code: str) -> str:
    # 1. Lexer: Tokenize identifiers, numbers, and basic syntax
    tokens: List[str] = re.findall(r"[a-zA-Z_]\w*|\d+|[(){},]", source_code)
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
        if tok.isdigit():
            return {"type": "num", "val": tok}
        elif peek() == "(":
            consume()  # '('
            args: List[Dict[str, Any]] = []
            while peek() != ")":
                args.append(parse_expr())
                if peek() == ",":
                    consume()  # ','
            consume()  # ')'
            return {"type": "call", "name": tok, "args": args}
        raise SyntaxError(f"Unexpected token: {tok}")  # pragma: no cover

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

    # 3. Code Generator: Flatten the AST into GRIR instructions
    locals_decl: List[str] = []
    instructions: List[str] = []
    temp_count: int = 1

    def generate_expr(node: Dict[str, Any], is_stmt: bool = False) -> Optional[str]:
        nonlocal temp_count
        if node["type"] == "num":
            return node["val"]
        elif node["type"] == "call":
            # Evaluate inner arguments first
            arg_vals = [generate_expr(arg) for arg in node["args"]]

            # Emit arguments
            for val in arg_vals:
                instructions.append(f"arg {val}")

            if is_stmt:
                instructions.append(f"call {node['name']}")
                return None
            else:
                # Need a temporary variable for nested calls
                tmp = f"t{temp_count}"
                temp_count += 1
                locals_decl.append(f"local {tmp} number")
                instructions.append(f"{tmp} = call {node['name']}")
                return tmp

    for stmt in ast["body"]:
        generate_expr(stmt, is_stmt=True)

    # Combine into final GRIR format
    lines: List[str] = [f"export_fn {ast['name']}"] + locals_decl + instructions
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 3:  # pragma: no cover
        sys.exit("Usage: python compile_grug.py <input.grug> <output.grir>")

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        source = f.read()

    grir_output = compile_grug(source)

    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(grir_output)
