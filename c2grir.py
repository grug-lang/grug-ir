import argparse

import pycparser_fake_libc
from pycparser import c_ast, parse_file

C_TYPE_TO_GRIR = {"double": "number", "bool": "bool", "void": "void"}

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

    assert isinstance(type_node, c_ast.IdentifierType)
    key = " ".join(type_node.names)
    assert key in C_TYPE_TO_GRIR
    return C_TYPE_TO_GRIR[key]


def expr_to_str(node):
    assert isinstance(node, c_ast.ID)
    return node.name


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
            stmts = compound.block_items
            i = 0
            while i < len(stmts):
                stmt = stmts[i]
                self._emit_stmt(stmt)
                i += 1

    def _emit_stmt(self, stmt):
        if isinstance(stmt, c_ast.Return):
            self._emit_return(stmt)
        elif isinstance(stmt, c_ast.If):
            self._emit_if(stmt)
        elif isinstance(stmt, c_ast.FuncCall):
            self._emit_func_call(stmt)
        else:
            assert isinstance(stmt, c_ast.Compound)
            self._emit_compound(stmt)

    def _emit_if(self, if_stmt):
        cond = if_stmt.cond
        label = self._new_label()

        if isinstance(cond, c_ast.UnaryOp) and cond.op == "!":
            var_name = expr_to_str(cond.expr)
            self.lines.append(f"if {var_name} != 0 goto {label}")

        self._emit_stmt(if_stmt.iftrue)
        self.lines.append(f"{label}:")

    def _emit_func_call(self, call):
        name = call.name.name
        self.lines.append(f"call {name}")

    def _emit_return(self, ret):
        assert ret.expr
        assert isinstance(ret.expr, c_ast.TernaryOp)
        self._emit_ternary_return(ret.expr)

    def _emit_ternary_return(self, ternary):
        cond = ternary.cond
        label = self._new_label()
        inv_op = INVERT_OP[cond.op]
        left = expr_to_str(cond.left)
        right = expr_to_str(cond.right)

        self.lines.append(f"if {left} {inv_op} {right} goto {label}")
        self.lines.append(f"return {expr_to_str(ternary.iftrue)}")
        self.lines.append(f"{label}:")
        self.lines.append(f"return {expr_to_str(ternary.iffalse)}")


def main():
    parser = argparse.ArgumentParser(
        description="Compile C host functions to grug IR (.grir)."
    )
    parser.add_argument("input", help="Path to the input C file (e.g., host_fns.c)")
    parser.add_argument("output", help="Path for the output .grir file")
    args = parser.parse_args()

    fake_libc_arg = "-I" + pycparser_fake_libc.directory
    ast = parse_file(args.input, use_cpp=True, cpp_args=fake_libc_arg)

    generator = GrirGenerator()
    grir = generator.generate(ast)
    with open(args.output, "w") as f:
        f.write(grir)


if __name__ == "__main__":
    main()
