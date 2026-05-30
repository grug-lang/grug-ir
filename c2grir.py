import argparse

from pycparser import c_ast, parse_file  # pyright: ignore[reportMissingImports]

C_TYPE_TO_GRIR = {
    "double": "number",
}

INVERT_OP = {
    "<": ">=",
    ">": "<=",
    "<=": ">",
    ">=": "<",
    "==": "!=",
    "!=": "==",
}


def c_type_to_grir(type_node):
    if isinstance(type_node, c_ast.TypeDecl):
        return c_type_to_grir(type_node.type)
    if isinstance(type_node, c_ast.IdentifierType):
        key = " ".join(type_node.names)
        if key not in C_TYPE_TO_GRIR:  # pragma: no cover
            raise NotImplementedError(f"Unsupported C type: {key!r}")
        return C_TYPE_TO_GRIR[key]
    raise NotImplementedError(
        f"Unsupported type node: {type(type_node).__name__}"
    )  # pragma: no cover


def expr_to_str(node):
    if isinstance(node, c_ast.ID):
        return node.name
    # if isinstance(node, c_ast.Constant):
    #     return node.value
    raise NotImplementedError(
        f"Unsupported expression: {type(node).__name__}"
    )  # pragma: no cover


class GrirGenerator:
    def __init__(self):
        self.lines = []
        self._label_counter = 0

    def _new_label(self):
        self._label_counter += 1
        return f"L{self._label_counter}"

    def generate(self, ast):
        for node in ast.ext:
            if isinstance(node, c_ast.FuncDef):
                self._emit_func(node)
        return "\n".join(self.lines) + "\n"

    def _emit_func(self, func_def):
        decl = func_def.decl
        func_decl = decl.type

        self.lines.append(f"host_fn {decl.name}")

        if func_decl.args is not None:
            for param in func_decl.args.params:
                param_type = c_type_to_grir(param.type)
                self.lines.append(f"param {param.name} {param_type}")

        ret_type = c_type_to_grir(func_decl.type)
        self.lines.append(f"returns {ret_type}")

        self._emit_compound(func_def.body)

    def _emit_compound(self, compound):
        if compound.block_items:
            for stmt in compound.block_items:
                self._emit_stmt(stmt)

    def _emit_stmt(self, stmt):
        if isinstance(stmt, c_ast.Return):
            self._emit_return(stmt)
        else:
            raise NotImplementedError(
                f"Unsupported statement: {type(stmt).__name__}"
            )  # pragma: no cover

    def _emit_return(self, ret):
        if isinstance(ret.expr, c_ast.TernaryOp):
            self._emit_ternary_return(ret.expr)
        else:
            self.lines.append(
                f"ret {expr_to_str(ret.expr)}"
            )  # pragma: no cover # TODO: Remove pragma, since non-ternaries reach this

    def _emit_ternary_return(self, ternary):
        cond = ternary.cond
        label = self._new_label()

        if not isinstance(cond, c_ast.BinaryOp):
            raise NotImplementedError(
                f"Unsupported ternary condition: {type(cond).__name__}"
            )  # pragma: no cover # TODO: Remove pragma, since conditions can be any expr

        inv_op = INVERT_OP[cond.op]
        left = expr_to_str(cond.left)
        right = expr_to_str(cond.right)
        self.lines.append(f"if {left} {inv_op} {right} goto {label}")
        self.lines.append(f"ret {expr_to_str(ternary.iftrue)}")
        self.lines.append(f"{label}:")
        self.lines.append(f"ret {expr_to_str(ternary.iffalse)}")


def main():
    parser = argparse.ArgumentParser(
        description="Compile C host functions to grug IR (.grir)."
    )
    parser.add_argument("input", help="Path to the input C file (e.g., host_fns.c)")
    parser.add_argument("output", help="Path for the output .grir file")
    args = parser.parse_args()

    ast = parse_file(args.input, use_cpp=False)
    generator = GrirGenerator()
    grir = generator.generate(ast)
    with open(args.output, "w") as f:
        f.write(grir)


if __name__ == "__main__":
    main()
