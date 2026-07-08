"""
lexer.py - Tokenizer for SimpleLang

Converts raw source code (a string) into a flat list of Token objects
that the Parser can consume.
"""

KEYWORDS = {
    "let", "if", "else", "while", "for", "print",
    "true", "false", "and", "or", "not",
    "func", "return", "break", "continue",
}

# Multi-character operators must be listed before their single-char prefixes
SYMBOLS = [
    "==", "!=", "<=", ">=",
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

    def _read_ident(self):
        start_line = self.line
        start = self.pos
        while self.pos < self.length and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        text = self.src[start:self.pos]
        if text in KEYWORDS:
            return Token("KEYWORD", text, start_line)
        return Token("IDENT", text, start_line)