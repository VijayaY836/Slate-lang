"""
ast_nodes.py - AST node classes for SimpleLang.

Each node is a plain data container; the Interpreter has one visit_X
method per node type.
"""


class Node:
    pass


# ---- Statements ----

class Program(Node):
    def __init__(self, statements):
        self.statements = statements


class VarDecl(Node):
    def __init__(self, name, expr, line):
        self.name = name
        self.expr = expr
        self.line = line


class Assign(Node):
    def __init__(self, name, expr, line):
        self.name = name
        self.expr = expr
        self.line = line


class Print(Node):
    def __init__(self, exprs, line):
        self.exprs = exprs
        self.line = line


class Block(Node):
    def __init__(self, statements):
        self.statements = statements


class If(Node):
    def __init__(self, condition, then_block, else_block, line):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block  # Block, If (else-if chain), or None
        self.line = line


class While(Node):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body
        self.line = line


class For(Node):
    def __init__(self, init, condition, update, body, line):
        self.init = init            # VarDecl or Assign or None
        self.condition = condition  # Expr or None
        self.update = update        # Assign or None
        self.body = body
        self.line = line


class ForIn(Node):
    def __init__(self, var_name, start, end, step, body, line):
        self.var_name = var_name
        self.start = start        # Expr
        self.end = end            # Expr (inclusive)
        self.step = step          # Expr or None (auto: +1 / -1)
        self.body = body
        self.line = line


class RepeatTimes(Node):
    def __init__(self, count, var_name, body, line):
        self.count = count        # Expr
        self.var_name = var_name  # str or None (0-indexed loop counter)
        self.body = body
        self.line = line


class ExprStmt(Node):
    def __init__(self, expr):
        self.expr = expr


class FuncDecl(Node):
    def __init__(self, name, params, body, line):
        self.name = name
        self.params = params      # list of str
        self.body = body          # Block
        self.line = line


class Return(Node):
    def __init__(self, expr, line):
        self.expr = expr          # Expr or None
        self.line = line


class Break(Node):
    def __init__(self, line):
        self.line = line


class Continue(Node):
    def __init__(self, line):
        self.line = line


class IndexAssign(Node):
    def __init__(self, target, index, value, line):
        self.target = target      # Expr evaluating to a list
        self.index = index        # Expr evaluating to an int
        self.value = value        # Expr for the new value
        self.line = line


# ---- Expressions ----

class Literal(Node):
    def __init__(self, value):
        self.value = value


class Var(Node):
    def __init__(self, name, line):
        self.name = name
        self.line = line


class BinOp(Node):
    def __init__(self, op, left, right, line):
        self.op = op
        self.left = left
        self.right = right
        self.line = line


class Logical(Node):
    def __init__(self, op, left, right, line):
        self.op = op
        self.left = left
        self.right = right
        self.line = line


class UnaryOp(Node):
    def __init__(self, op, operand, line):
        self.op = op
        self.operand = operand
        self.line = line


class ArrayLiteral(Node):
    def __init__(self, elements, line):
        self.elements = elements  # list of Expr
        self.line = line


class Index(Node):
    def __init__(self, target, index, line):
        self.target = target      # Expr evaluating to a list/string
        self.index = index        # Expr evaluating to an int
        self.line = line


class Call(Node):
    def __init__(self, callee, args, line):
        self.callee = callee      # Var node (function name) in this language
        self.args = args          # list of Expr
        self.line = line


class TemplateStr(Node):
    def __init__(self, parts, line):
        self.parts = parts        # list of Expr; stringified and concatenated
        self.line = line