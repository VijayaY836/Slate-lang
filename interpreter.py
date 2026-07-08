"""
interpreter.py - Tree-walking interpreter for SimpleLang.
"""

from ast_nodes import (
    Program, VarDecl, Assign, Print, Block, If, While, For, ExprStmt,
    Literal, Var, BinOp, Logical, UnaryOp,
    FuncDecl, Return, Break, Continue, IndexAssign,
    ArrayLiteral, Index, Call,
)


class RuntimeErrorSL(Exception):
    pass


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    """A single lexical scope, chained to its parent."""

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def define(self, name, value):
        self.vars[name] = value

    def get(self, name, line):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise RuntimeErrorSL(f"Runtime error on line {line}: undefined variable '{name}'")

    def set(self, name, value, line):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        raise RuntimeErrorSL(
            f"Runtime error on line {line}: cannot assign to undefined variable '{name}' "
            f"(use 'let' to declare it first)"
        )


def stringify(value):
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, list):
        return "[" + ", ".join(stringify(v) for v in value) + "]"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.functions = {}   # name -> FuncDecl
        self.builtins = {
            "len": lambda args, line: self._builtin_len(args, line),
            "push": lambda args, line: self._builtin_push(args, line),
            "pop": lambda args, line: self._builtin_pop(args, line),
        }

    def run(self, program):
        # Hoist function declarations so they can be called before their
        # textual definition (and from within other functions).
        for stmt in program.statements:
            if isinstance(stmt, FuncDecl):
                self.exec_FuncDecl(stmt, self.global_env)
        try:
            self.exec_block_statements(program.statements, self.global_env)
        except BreakException:
            raise RuntimeErrorSL("Runtime error: 'break' used outside of a loop")
        except ContinueException:
            raise RuntimeErrorSL("Runtime error: 'continue' used outside of a loop")
        except ReturnException:
            raise RuntimeErrorSL("Runtime error: 'return' used outside of a function")

    # ---- builtins ----

    def _builtin_len(self, args, line):
        if len(args) != 1:
            raise RuntimeErrorSL(f"Runtime error on line {line}: len() expects 1 argument")
        val = args[0]
        if isinstance(val, (list, str)):
            return len(val)
        raise RuntimeErrorSL(f"Runtime error on line {line}: len() expects an array or string")

    def _builtin_push(self, args, line):
        if len(args) != 2 or not isinstance(args[0], list):
            raise RuntimeErrorSL(f"Runtime error on line {line}: push() expects (array, value)")
        args[0].append(args[1])
        return args[0]

    def _builtin_pop(self, args, line):
        if len(args) != 1 or not isinstance(args[0], list):
            raise RuntimeErrorSL(f"Runtime error on line {line}: pop() expects (array)")
        if not args[0]:
            raise RuntimeErrorSL(f"Runtime error on line {line}: pop() called on an empty array")
        return args[0].pop()

    # ---- statement execution ----

    def exec_block_statements(self, statements, env):
        for stmt in statements:
            self.execute(stmt, env)

    def execute(self, node, env):
        method_name = "exec_" + type(node).__name__
        method = getattr(self, method_name)
        return method(node, env)

    def exec_VarDecl(self, node, env):
        value = self.evaluate(node.expr, env)
        env.define(node.name, value)

    def exec_Assign(self, node, env):
        value = self.evaluate(node.expr, env)
        env.set(node.name, value, node.line)

    def exec_Print(self, node, env):
        parts = [stringify(self.evaluate(e, env)) for e in node.exprs]
        print(" ".join(parts))

    def exec_Block(self, node, env):
        inner = Environment(parent=env)
        self.exec_block_statements(node.statements, inner)

    def exec_If(self, node, env):
        if self.evaluate(node.condition, env):
            self.execute(node.then_block, env)
        elif node.else_block is not None:
            self.execute(node.else_block, env)

    def exec_While(self, node, env):
        while self.evaluate(node.condition, env):
            try:
                self.execute(node.body, env)
            except BreakException:
                break
            except ContinueException:
                continue

    def exec_For(self, node, env):
        loop_env = Environment(parent=env)
        if node.init is not None:
            self.execute(node.init, loop_env)
        while node.condition is None or self.evaluate(node.condition, loop_env):
            try:
                self.execute(node.body, loop_env)
            except BreakException:
                break
            except ContinueException:
                pass  # fall through to the update clause below
            if node.update is not None:
                self.execute(node.update, loop_env)

    def exec_ExprStmt(self, node, env):
        self.evaluate(node.expr, env)

    def exec_FuncDecl(self, node, env):
        self.functions[node.name] = node

    def exec_Return(self, node, env):
        value = self.evaluate(node.expr, env) if node.expr is not None else None
        raise ReturnException(value)

    def exec_Break(self, node, env):
        raise BreakException()

    def exec_Continue(self, node, env):
        raise ContinueException()

    def exec_IndexAssign(self, node, env):
        target = self.evaluate(node.target, env)
        if not isinstance(target, list):
            raise RuntimeErrorSL(f"Runtime error on line {node.line}: can only index into an array")
        idx = self.evaluate(node.index, env)
        if not isinstance(idx, int) or isinstance(idx, bool):
            raise RuntimeErrorSL(f"Runtime error on line {node.line}: array index must be an integer")
        if idx < 0 or idx >= len(target):
            raise RuntimeErrorSL(f"Runtime error on line {node.line}: array index {idx} out of range")
        target[idx] = self.evaluate(node.value, env)

    # ---- expression evaluation ----

    def evaluate(self, node, env):
        method_name = "eval_" + type(node).__name__
        method = getattr(self, method_name)
        return method(node, env)

    def eval_Literal(self, node, env):
        return node.value

    def eval_Var(self, node, env):
        return env.get(node.name, node.line)

    def eval_ArrayLiteral(self, node, env):
        return [self.evaluate(e, env) for e in node.elements]

    def eval_Index(self, node, env):
        target = self.evaluate(node.target, env)
        idx = self.evaluate(node.index, env)
        if not isinstance(idx, int) or isinstance(idx, bool):
            raise RuntimeErrorSL(f"Runtime error on line {node.line}: array index must be an integer")
        if isinstance(target, (list, str)):
            if idx < 0 or idx >= len(target):
                raise RuntimeErrorSL(f"Runtime error on line {node.line}: array index {idx} out of range")
            return target[idx]
        raise RuntimeErrorSL(f"Runtime error on line {node.line}: can only index into an array or string")

    def eval_Call(self, node, env):
        if not isinstance(node.callee, Var):
            raise RuntimeErrorSL(f"Runtime error on line {node.line}: expression is not callable")
        name = node.callee.name
        args = [self.evaluate(a, env) for a in node.args]

        if name in self.builtins:
            return self.builtins[name](args, node.line)

        func = self.functions.get(name)
        if func is None:
            raise RuntimeErrorSL(f"Runtime error on line {node.line}: undefined function '{name}'")
        if len(args) != len(func.params):
            raise RuntimeErrorSL(
                f"Runtime error on line {node.line}: '{name}' expects {len(func.params)} "
                f"argument(s), got {len(args)}"
            )

        call_env = Environment(parent=self.global_env)
        for param, arg in zip(func.params, args):
            call_env.define(param, arg)

        try:
            self.exec_block_statements(func.body.statements, call_env)
        except ReturnException as ret:
            return ret.value
        return None

    def eval_UnaryOp(self, node, env):
        val = self.evaluate(node.operand, env)
        if node.op == "-":
            self._check_number(val, node.line)
            return -val
        if node.op == "not":
            return not self._truthy(val)
        raise RuntimeErrorSL(f"Runtime error on line {node.line}: unknown unary op '{node.op}'")

    def eval_Logical(self, node, env):
        left = self.evaluate(node.left, env)
        if node.op == "and":
            if not self._truthy(left):
                return False
            right = self.evaluate(node.right, env)
            return self._truthy(right)
        if node.op == "or":
            if self._truthy(left):
                return True
            right = self.evaluate(node.right, env)
            return self._truthy(right)
        raise RuntimeErrorSL(f"Runtime error on line {node.line}: unknown logical op '{node.op}'")

    def eval_BinOp(self, node, env):
        left = self.evaluate(node.left, env)
        right = self.evaluate(node.right, env)
        op = node.op
        line = node.line

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return stringify(left) + stringify(right)
            self._check_number(left, line); self._check_number(right, line)
            return left + right
        if op == "-":
            self._check_number(left, line); self._check_number(right, line)
            return left - right
        if op == "*":
            self._check_number(left, line); self._check_number(right, line)
            return left * right
        if op == "/":
            self._check_number(left, line); self._check_number(right, line)
            if right == 0:
                raise RuntimeErrorSL(f"Runtime error on line {line}: division by zero")
            result = left / right
            if isinstance(left, int) and isinstance(right, int) and left % right == 0:
                return left // right
            return result
        if op == "%":
            self._check_number(left, line); self._check_number(right, line)
            if right == 0:
                raise RuntimeErrorSL(f"Runtime error on line {line}: modulo by zero")
            return left % right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right

        raise RuntimeErrorSL(f"Runtime error on line {line}: unknown operator '{op}'")

    # ---- helpers ----

    def _truthy(self, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True

    def _check_number(self, value, line):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise RuntimeErrorSL(f"Runtime error on line {line}: expected a number, got {value!r}")