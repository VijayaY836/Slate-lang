"""
lexer.py - Tokenizer for SimpleLang

Converts raw source code (a string) into a flat list of Token objects
that the Parser can consume.
"""

KEYWORDS = {
    "let", "if", "else", "unless", "while", "for", "in", "step",
    "repeat", "times", "as", "print",
    "true", "false", "and", "or", "not",
    "func", "return", "break", "continue",
}

# Multi-character operators must be listed before their single-char prefixes
SYMBOLS = [
    "==", "!=", "<=", ">=", "..",
    "+", "-", "*", "/", "%",
    "=", "<", ">",
    "(", ")", "{", "}", "[", "]",
    ";", ",",
]


class Token:
    def __init__(self, type_, value, line):
        self.type = type_      # e.g. 'NUMBER', 'IDENT', 'STRING', 'KEYWORD', 'SYMBOL', 'EOF'
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


class LexError(Exception):
    pass


class Lexer:
    def __init__(self, source):
        self.src = source
        self.pos = 0
        self.line = 1
        self.length = len(source)

    def error(self, msg):
        raise LexError(f"Lex error on line {self.line}: {msg}")

    def peek(self, offset=0):
        p = self.pos + offset
        if p < self.length:
            return self.src[p]
        return ""

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def tokenize(self):
        tokens = []
        while self.pos < self.length:
            ch = self.peek()

            # Skip whitespace
            if ch in " \t\r\n":
                self.advance()
                continue

            # Skip comments: # until end of line
            if ch == "#":
                while self.pos < self.length and self.peek() != "\n":
                    self.advance()
                continue

            # Numbers (int or float)
            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            # Strings "..."
            if ch == '"':
                tokens.append(self._read_string())
                continue

            # Template strings `...${expr}...`
            if ch == "`":
                tokens.append(self._read_template())
                continue

            # Identifiers / keywords
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_ident())
                continue

            # Symbols / operators
            matched = False
            for sym in SYMBOLS:
                if self.src.startswith(sym, self.pos):
                    line = self.line
                    for _ in sym:
                        self.advance()
                    tokens.append(Token("SYMBOL", sym, line))
                    matched = True
                    break
            if matched:
                continue

            self.error(f"Unexpected character {ch!r}")

        tokens.append(Token("EOF", None, self.line))
        return tokens

    def _read_number(self):
        start_line = self.line
        start = self.pos
        is_float = False
        while self.pos < self.length and self.peek().isdigit():
            self.advance()
        if self.peek() == "." and self.peek(1).isdigit():
            is_float = True
            self.advance()
            while self.pos < self.length and self.peek().isdigit():
                self.advance()
        text = self.src[start:self.pos]
        value = float(text) if is_float else int(text)
        return Token("NUMBER", value, start_line)

    def _read_string(self):
        start_line = self.line
        self.advance()  # consume opening quote
        chars = []
        while True:
            if self.pos >= self.length:
                self.error("Unterminated string literal")
            ch = self.peek()
            if ch == '"':
                self.advance()
                break
            if ch == "\\":
                self.advance()
                esc = self.advance()
                mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                chars.append(mapping.get(esc, esc))
                continue
            chars.append(self.advance())
        return Token("STRING", "".join(chars), start_line)

    def _read_template(self):
        """Reads a `...` template string into a Token whose value is a list
        of ('str', text) / ('expr', source) segments. Anything inside
        ${ ... } is kept as raw source text, to be lexed+parsed as an
        expression later (see Parser.primary_base)."""
        start_line = self.line
        self.advance()  # consume opening backtick
        parts = []
        buf = []
        while True:
            if self.pos >= self.length:
                self.error("Unterminated template string literal")
            ch = self.peek()
            if ch == "`":
                self.advance()
                break
            if ch == "\\":
                self.advance()
                esc = self.advance()
                mapping = {"n": "\n", "t": "\t", "`": "`", "\\": "\\", "$": "$"}
                buf.append(mapping.get(esc, esc))
                continue
            if ch == "$" and self.peek(1) == "{":
                parts.append(("str", "".join(buf)))
                buf = []
                self.advance()
                self.advance()  # consume '${'
                expr_chars = []
                depth = 1
                while True:
                    if self.pos >= self.length:
                        self.error("Unterminated ${...} inside template string")
                    c = self.peek()
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            self.advance()
                            break
                    expr_chars.append(self.advance())
                parts.append(("expr", "".join(expr_chars)))
                continue
            buf.append(self.advance())
        parts.append(("str", "".join(buf)))
        return Token("TEMPLATE", parts, start_line)

    def _read_ident(self):
        start_line = self.line
        start = self.pos
        while self.pos < self.length and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        text = self.src[start:self.pos]
        if text in KEYWORDS:
            return Token("KEYWORD", text, start_line)
        return Token("IDENT", text, start_line)