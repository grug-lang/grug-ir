#!/usr/bin/env python3
"""Compile C host functions to grug IR (.grir)."""

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
        if key not in C_TYPE_TO_GRIR:
            raise NotImplementedError(f"Unsupported C type: {key!r}")
        return C_TYPE_TO_GRIR[key]
    raise NotImplementedError(f"Unsupported type node: {type(type_node).__name__}")


def expr_to_str(node):
    if isinstance(node, c_ast.ID):
        return node.name
    if isinstance(node, c_ast.Constant):
        return node.value
    raise NotImplementedError(f"Unsupported expression: {type(node).__name__}")


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
            raise NotImplementedError(f"Unsupported statement: {type(stmt).__name__}")

    def _emit_return(self, ret):
        if isinstance(ret.expr, c_ast.TernaryOp):
            self._emit_ternary_return(ret.expr)
        else:
            self.lines.append(f"ret {expr_to_str(ret.expr)}")

    def _emit_ternary_return(self, ternary):
        cond = ternary.cond
        label = self._new_label()

        if not isinstance(cond, c_ast.BinaryOp):
            raise NotImplementedError(
                f"Unsupported ternary condition: {type(cond).__name__}"
            )

        inv_op = INVERT_OP.get(cond.op)
        if inv_op is None:
            raise NotImplementedError(f"Unsupported binary operator: {cond.op!r}")

        left = expr_to_str(cond.left)
        right = expr_to_str(cond.right)
        self.lines.append(f"if {left} {inv_op} {right} goto {label}")
        self.lines.append(f"ret {expr_to_str(ternary.iftrue)}")
        self.lines.append(f"{label}:")
        self.lines.append(f"ret {expr_to_str(ternary.iffalse)}")


def main():
    ast = parse_file("host_fns.c", use_cpp=False)
    generator = GrirGenerator()
    grir = generator.generate(ast)
    with open("output_host_fns.grir", "w") as f:
        f.write(grir)


if __name__ == "__main__":
    main()
