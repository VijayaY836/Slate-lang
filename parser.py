"""
parser.py - Recursive-descent parser for SimpleLang.

Grammar (informal):

    program     := statement* EOF
    statement   := varDecl | assign | ifStmt | unlessStmt | whileStmt
                 | repeatStmt | forStmt | printStmt | block | exprStmt
    varDecl     := 'let' IDENT '=' expr ';'
    assign      := IDENT '=' expr ';'
    printStmt   := 'print' '(' expr (',' expr)* ')' ';'
    ifStmt      := 'if' '(' expr ')' block ('else' (ifStmt | block))?
    unlessStmt  := 'unless' '(' expr ')' block ('else' (ifStmt | block))?
    whileStmt   := 'while' '(' expr ')' block
    repeatStmt  := 'repeat' expr 'times' ('as' IDENT)? block
    forStmt     := 'for' '(' (varDecl|assign)? ';' expr? ';' assign? ')' block
                 | 'for' IDENT 'in' expr '..' expr ('step' expr)? block
    block       := '{' statement* '}'
    exprStmt    := expr ';'

    expr        := logical
    logical     := equality (('and'|'or') equality)*
    equality    := comparison (('=='|'!=') comparison)*
    comparison  := term (('<'|'>'|'<='|'>=') term)*
    term        := factor (('+'|'-') factor)*
    factor      := unary (('*'|'/'|'%') unary)*
    unary       := ('-'|'not') unary | primary
    primary     := NUMBER | STRING | 'true' | 'false' | IDENT | '(' expr ')'
"""

from lexer import Lexer
from ast_nodes import (
    Program, VarDecl, Assign, Print, Block, If, While, For, ForIn,
    RepeatTimes, ExprStmt,
    Literal, Var, BinOp, Logical, UnaryOp,
    FuncDecl, Return, Break, Continue, IndexAssign,
    ArrayLiteral, Index, Call, TemplateStr,
)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---- token helpers ----

    def current(self):
        return self.tokens[self.pos]

    def check(self, type_, value=None):
        tok = self.current()
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def peek_token(self, offset):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def match(self, type_, value=None):
        if self.check(type_, value):
            return self.advance()
        return None

    def advance(self):
        tok = self.current()
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def expect(self, type_, value=None):
        if self.check(type_, value):
            return self.advance()
        tok = self.current()
        expected = value if value is not None else type_
        raise ParseError(
            f"Parse error on line {tok.line}: expected {expected!r}, got {tok.value!r}"
        )

    # ---- entry point ----

    def parse(self):
        statements = []
        while not self.check("EOF"):
            statements.append(self.statement())
        return Program(statements)

    # ---- statements ----

    def statement(self):
        if self.check("KEYWORD", "let"):
            return self.var_decl()
        if self.check("KEYWORD", "if"):
            return self.if_stmt()
        if self.check("KEYWORD", "unless"):
            return self.unless_stmt()
        if self.check("KEYWORD", "while"):
            return self.while_stmt()
        if self.check("KEYWORD", "repeat"):
            return self.repeat_stmt()
        if self.check("KEYWORD", "for"):
            return self.for_stmt()
        if self.check("KEYWORD", "print"):
            return self.print_stmt()
        if self.check("KEYWORD", "func"):
            return self.func_decl()
        if self.check("KEYWORD", "return"):
            return self.return_stmt()
        if self.check("KEYWORD", "break"):
            line = self.advance().line
            self.expect("SYMBOL", ";")
            return Break(line)
        if self.check("KEYWORD", "continue"):
            line = self.advance().line
            self.expect("SYMBOL", ";")
            return Continue(line)
        if self.check("SYMBOL", "{"):
            return self.block()
        return self.assignment_or_expr_stmt()

    def var_decl(self):
        line = self.current().line
        self.expect("KEYWORD", "let")
        name = self.expect("IDENT").value
        self.expect("SYMBOL", "=")
        expr = self.expr()
        self.expect("SYMBOL", ";")
        return VarDecl(name, expr, line)

    def _target_to_assignment(self, target, value, line):
        """Convert a parsed expression used as an assignment target (Var or
        Index) into the matching Assign / IndexAssign statement node."""
        if isinstance(target, Var):
            return Assign(target.name, value, line)
        if isinstance(target, Index):
            return IndexAssign(target.target, target.index, value, line)
        raise ParseError(f"Parse error on line {line}: invalid assignment target")

    def assignment_or_expr_stmt(self):
        """Parses either `target = expr;` (where target is a variable or an
        indexed array slot) or a bare expression statement, e.g. a function
        call used for its side effects: `push(arr, 1);`"""
        line = self.current().line
        target = self.expr()
        if self.match("SYMBOL", "="):
            value = self.expr()
            self.expect("SYMBOL", ";")
            return self._target_to_assignment(target, value, line)
        self.expect("SYMBOL", ";")
        return ExprStmt(target)

    def assign_no_semi(self):
        """Used inside for(...) init/update clauses, no trailing ';' """
        line = self.current().line
        target = self.expr()
        self.expect("SYMBOL", "=")
        value = self.expr()
        return self._target_to_assignment(target, value, line)

    def func_decl(self):
        line = self.current().line
        self.expect("KEYWORD", "func")
        name = self.expect("IDENT").value
        self.expect("SYMBOL", "(")
        params = []
        if not self.check("SYMBOL", ")"):
            params.append(self.expect("IDENT").value)
            while self.match("SYMBOL", ","):
                params.append(self.expect("IDENT").value)
        self.expect("SYMBOL", ")")
        body = self.block()
        return FuncDecl(name, params, body, line)

    def return_stmt(self):
        line = self.current().line
        self.expect("KEYWORD", "return")
        expr = None
        if not self.check("SYMBOL", ";"):
            expr = self.expr()
        self.expect("SYMBOL", ";")
        return Return(expr, line)

    def print_stmt(self):
        line = self.current().line
        self.expect("KEYWORD", "print")
        self.expect("SYMBOL", "(")
        exprs = [self.expr()]
        while self.match("SYMBOL", ","):
            exprs.append(self.expr())
        self.expect("SYMBOL", ")")
        self.expect("SYMBOL", ";")
        return Print(exprs, line)

    def block(self):
        self.expect("SYMBOL", "{")
        statements = []
        while not self.check("SYMBOL", "}"):
            statements.append(self.statement())
        self.expect("SYMBOL", "}")
        return Block(statements)

    def if_stmt(self):
        line = self.current().line
        self.expect("KEYWORD", "if")
        self.expect("SYMBOL", "(")
        condition = self.expr()
        self.expect("SYMBOL", ")")
        then_block = self.block()
        else_block = None
        if self.match("KEYWORD", "else"):
            if self.check("KEYWORD", "if"):
                else_block = self.if_stmt()   # else-if chaining
            else:
                else_block = self.block()
        return If(condition, then_block, else_block, line)

    def unless_stmt(self):
        """unless (cond) { ... } [else { ... }] -- sugar for `if (not cond)`."""
        line = self.current().line
        self.expect("KEYWORD", "unless")
        self.expect("SYMBOL", "(")
        condition = self.expr()
        self.expect("SYMBOL", ")")
        then_block = self.block()
        else_block = None
        if self.match("KEYWORD", "else"):
            if self.check("KEYWORD", "if"):
                else_block = self.if_stmt()
            else:
                else_block = self.block()
        return If(UnaryOp("not", condition, line), then_block, else_block, line)

    def while_stmt(self):
        line = self.current().line
        self.expect("KEYWORD", "while")
        self.expect("SYMBOL", "(")
        condition = self.expr()
        self.expect("SYMBOL", ")")
        body = self.block()
        return While(condition, body, line)

    def repeat_stmt(self):
        """repeat <count> times [as name] { ... }"""
        line = self.current().line
        self.expect("KEYWORD", "repeat")
        count = self.expr()
        self.expect("KEYWORD", "times")
        var_name = None
        if self.match("KEYWORD", "as"):
            var_name = self.expect("IDENT").value
        body = self.block()
        return RepeatTimes(count, var_name, body, line)

    def for_stmt(self):
        line = self.current().line
        self.expect("KEYWORD", "for")

        # for name in start..end [step n] { ... }
        if self.check("IDENT") and self.peek_token(1).type == "KEYWORD" and self.peek_token(1).value == "in":
            var_name = self.advance().value
            self.expect("KEYWORD", "in")
            start = self.expr()
            self.expect("SYMBOL", "..")
            end = self.expr()
            step = None
            if self.match("KEYWORD", "step"):
                step = self.expr()
            body = self.block()
            return ForIn(var_name, start, end, step, body, line)

        self.expect("SYMBOL", "(")

        init = None
        if not self.check("SYMBOL", ";"):
            if self.check("KEYWORD", "let"):
                init = self.var_decl()  # consumes trailing ';'
            else:
                init = self.assign_no_semi()
                self.expect("SYMBOL", ";")
        else:
            self.expect("SYMBOL", ";")

        condition = None
        if not self.check("SYMBOL", ";"):
            condition = self.expr()
        self.expect("SYMBOL", ";")

        update = None
        if not self.check("SYMBOL", ")"):
            update = self.assign_no_semi()
        self.expect("SYMBOL", ")")

        body = self.block()
        return For(init, condition, update, body, line)

    def expr_stmt(self):
        expr = self.expr()
        self.expect("SYMBOL", ";")
        return ExprStmt(expr)

    # ---- expressions (precedence climbing) ----

    def expr(self):
        return self.logical()

    def logical(self):
        left = self.equality()
        while self.check("KEYWORD", "and") or self.check("KEYWORD", "or"):
            op_tok = self.advance()
            right = self.equality()
            left = Logical(op_tok.value, left, right, op_tok.line)
        return left

    def equality(self):
        left = self.comparison()
        while self.check("SYMBOL", "==") or self.check("SYMBOL", "!="):
            op_tok = self.advance()
            right = self.comparison()
            left = BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def comparison(self):
        left = self.term()
        while (self.check("SYMBOL", "<") or self.check("SYMBOL", ">")
               or self.check("SYMBOL", "<=") or self.check("SYMBOL", ">=")):
            op_tok = self.advance()
            right = self.term()
            left = BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def term(self):
        left = self.factor()
        while self.check("SYMBOL", "+") or self.check("SYMBOL", "-"):
            op_tok = self.advance()
            right = self.factor()
            left = BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def factor(self):
        left = self.unary()
        while (self.check("SYMBOL", "*") or self.check("SYMBOL", "/")
               or self.check("SYMBOL", "%")):
            op_tok = self.advance()
            right = self.unary()
            left = BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def unary(self):
        if self.check("SYMBOL", "-") or self.check("KEYWORD", "not"):
            op_tok = self.advance()
            operand = self.unary()
            return UnaryOp(op_tok.value, operand, op_tok.line)
        return self.primary()

    def primary(self):
        node = self.primary_base()
        # postfix chain: indexing arr[i] and calls name(args), e.g. matrix[i][j]
        while True:
            if self.check("SYMBOL", "["):
                line = self.advance().line
                idx = self.expr()
                self.expect("SYMBOL", "]")
                node = Index(node, idx, line)
            elif self.check("SYMBOL", "("):
                line = self.advance().line
                args = []
                if not self.check("SYMBOL", ")"):
                    args.append(self.expr())
                    while self.match("SYMBOL", ","):
                        args.append(self.expr())
                self.expect("SYMBOL", ")")
                node = Call(node, args, line)
            else:
                break
        return node

    def primary_base(self):
        tok = self.current()

        if tok.type == "NUMBER":
            self.advance()
            return Literal(tok.value)

        if tok.type == "STRING":
            self.advance()
            return Literal(tok.value)

        if tok.type == "TEMPLATE":
            self.advance()
            segments = []
            for kind, text in tok.value:
                if kind == "str":
                    if text != "":
                        segments.append(Literal(text))
                else:
                    sub_tokens = Lexer(text).tokenize()
                    segments.append(Parser(sub_tokens).expr())
            if not segments:
                segments.append(Literal(""))
            return TemplateStr(segments, tok.line)

        if self.check("KEYWORD", "true"):
            self.advance()
            return Literal(True)

        if self.check("KEYWORD", "false"):
            self.advance()
            return Literal(False)

        if tok.type == "IDENT":
            self.advance()
            return Var(tok.value, tok.line)

        if self.check("SYMBOL", "("):
            self.advance()
            expr = self.expr()
            self.expect("SYMBOL", ")")
            return expr

        if self.check("SYMBOL", "["):
            line = self.advance().line
            elements = []
            if not self.check("SYMBOL", "]"):
                elements.append(self.expr())
                while self.match("SYMBOL", ","):
                    elements.append(self.expr())
            self.expect("SYMBOL", "]")
            return ArrayLiteral(elements, line)

        raise ParseError(f"Parse error on line {tok.line}: unexpected token {tok.value!r}")