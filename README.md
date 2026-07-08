# Slate

A small interpreted programming language, written in Python, with:

- Variables (`let`)
- Arithmetic (`+ - * / %`) and comparison (`== != < > <= >=`) operators
- Boolean logic (`and`, `or`, `not`)
- Conditionals (`if` / `else if` / `else`)
- Loops (`while` and C-style `for`), with `break` and `continue`
- Functions with parameters and `return` values (recursion supported)
- Arrays: literals `[1, 2, 3]`, indexing `arr[i]`, index assignment `arr[i] = v`,
  and builtins `len(arr)`, `push(arr, v)`, `pop(arr)`
- `print(...)` for output
- Comments with `#`

It's implemented as a classic **lexer → parser → tree-walking interpreter**
pipeline, with no external dependencies (pure Python 3, standard library only).

## Project structure

```
simplelang/
├── lexer.py        # Source code -> tokens
├── parser.py        # Tokens -> AST (recursive-descent parser)
├── ast_nodes.py      # AST node class definitions
├── interpreter.py    # Tree-walking evaluator (executes the AST)
├── main.py           # CLI entry point
├── web_ui.py         # Local browser playground (code box + run + output)
└── examples/
    ├── fizzbuzz.sl       # Classic FizzBuzz 1-20
    ├── factorial.sl      # Factorial of 10 via while loop
    ├── fibonacci.sl      # Fibonacci sequence (for loop) + prime sieve (nested while)
    └── features_demo.sl  # Recursive functions, arrays, bubble sort, break/continue
```

## Running a program

Requires Python 3.7+, nothing else.

```bash
python main.py examples/fizzbuzz.sl
python main.py examples/factorial.sl
python main.py examples/fibonacci.sl
```

## Web playground

A small local web UI is included for writing and running SimpleLang code in
the browser, with no external dependencies (stdlib only).

```bash
python web_ui.py        # serves on http://127.0.0.1:5000 and opens it
python web_ui.py 8080    # or pick a different port
```

It gives you a code box and an output panel — write `.sl` code, hit **Run**
(or Ctrl/Cmd + Enter), and see `print(...)` output or lexer/parser/runtime
errors right there.

## Language reference

### Variables

```
let x = 5;
x = x + 1;       # reassignment (must be declared with 'let' first)
```

### Data types

- Numbers: integers and floats (`5`, `3.14`)
- Strings: `"hello"` (supports `\n`, `\t`, `\"`, `\\` escapes)
- Booleans: `true`, `false`

### Operators

| Category   | Operators                  |
|------------|-----------------------------|
| Arithmetic | `+ - * / %`                |
| Comparison | `== != < > <= >=`          |
| Logical    | `and  or  not`              |

`+` also does string concatenation if either operand is a string
(non-string values are auto-stringified).

### Conditionals

```
if (x > 10) {
    print("big");
} else if (x > 0) {
    print("small positive");
} else {
    print("non-positive");
}
```

### While loop

```
let i = 0;
while (i < 5) {
    print(i);
    i = i + 1;
}
```

### For loop

```
for (let i = 0; i < 10; i = i + 1) {
    print(i);
}
```

### Print

```
print("value is", x, "and y is", y);   # multiple comma-separated args
```

### Comments

```
# this is a comment, runs to end of line
```

### Functions

```
func add(a, b) {
    return a + b;
}
print(add(2, 3));   # 5

# recursion works too
func factorial(n) {
    if (n <= 1) { return 1; }
    return n * factorial(n - 1);
}
```

### Arrays

```
let nums = [5, 2, 9];
print(nums[0]);        # 5
nums[0] = 42;
print(len(nums));       # 3
push(nums, 100);        # append
let last = pop(nums);   # remove & return last element
```

### break / continue

```
let i = 0;
while (i < 10) {
    i = i + 1;
    if (i % 2 == 0) { continue; }
    if (i > 7) { break; }
    print(i);
}
```

## Example: FizzBuzz (`examples/fizzbuzz.sl`)

```
let i = 1;
while (i <= 20) {
    if (i % 15 == 0) {
        print("FizzBuzz");
    } else if (i % 3 == 0) {
        print("Fizz");
    } else if (i % 5 == 0) {
        print("Buzz");
    } else {
        print(i);
    }
    i = i + 1;
}
```

## Design notes

- **Lexer** (`lexer.py`): hand-written scanner producing `Token(type, value, line)`
  objects. Handles numbers, strings, identifiers/keywords, operators, and `#` comments.
- **Parser** (`parser.py`): recursive-descent parser with standard precedence
  climbing for expressions (`or/and` → `==/!=` → `</>/<=/>=` → `+/-` → `*/%//` → unary → primary).
  `else if` is handled by recursively parsing another `if` statement as the else-branch.
- **Interpreter** (`interpreter.py`): tree-walking evaluator. Each block
  (`{ ... }`, loop bodies, `for`-loop scope) creates a new `Environment`
  chained to its parent, giving proper lexical scoping — a variable declared
  inside a block or loop doesn't leak into the outer scope, but inner scopes
  can read and reassign outer variables.
- Errors (lexing, parsing, runtime) are reported with line numbers and a
  clear message rather than raw Python tracebacks.

## Possible extensions

- Functions/procedures with parameters and return values
- Arrays/lists and a `for-in` loop
- `break` / `continue`
- A REPL mode in `main.py`