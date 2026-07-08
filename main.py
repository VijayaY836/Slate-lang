"""
main.py - Command-line entry point for SimpleLang.

Usage:
    python main.py path/to/program.sl
"""

import sys

from lexer import Lexer, LexError
from parser import Parser, ParseError
from interpreter import Interpreter, RuntimeErrorSL


def run_file(path):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        Interpreter().run(program)
    except LexError as e:
        print(f"[Lexer error] {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"[Parser error] {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeErrorSL as e:
        print(f"[Runtime error] {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <script.sl>")
        sys.exit(1)
    run_file(sys.argv[1])


if __name__ == "__main__":
    main()