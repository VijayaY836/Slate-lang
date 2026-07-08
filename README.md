# Slate

Demo Video : https://drive.google.com/file/d/1qbOc0PUA0CqjztWwzftw5-bxdR-H7RlI/view?usp=sharing

A small interpreted programming language, written in Python, with:

- Variables (`let`)
- Arithmetic (`+ - * / %`) and comparison (`== != < > <= >=`) operators
- Boolean logic (`and`, `or`, `not`)
- Conditionals (`if` / `else if` / `else`) and its mirror image, `unless`
- Loops: `while`, C-style `for`, range-based `for i in 1..10 [step n]`,
  and `repeat n times [as i]`, with `break` and `continue`
- Functions with parameters and `return` values (recursion supported)
- Arrays: literals `[1, 2, 3]`, indexing `arr[i]`, index assignment `arr[i] = v`,
  and builtins `len(arr)`, `push(arr, v)`, `pop(arr)`
- Template strings: `` `Hello, ${name}!` `` for inline interpolation
- `print(...)` for output
- Comments with `#`

It's implemented as a classic **lexer → parser → tree-walking interpreter**
pipeline, with no external dependencies (pure Python 3, standard library only).

## Project structure

```
simplelang/
├── lexer.py        # Source code -> tokens
├── parser.py        # Tokens -> AST (recursive-descent parser)
├── ast_nodes.py    # AST node class definitions
├── requirements.txt
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

`unless` is the negated form of `if`, for when it reads better than `if (not ...)`:

```
unless (x > 0) {
    print("non-positive");
} else {
    print("positive");
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

### Range-based for...in

Inclusive on both ends, defaults to a step of `1` (a descending range
needs an explicit negative `step`, otherwise it runs zero times):

```
for i in 1..5 {
    print(i);            # 1 2 3 4 5
}
for i in 10..0 step -2 {
    print(i);            # 10 8 6 4 2 0
}
```

### repeat...times

```
repeat 3 times as i {
    print(`pass ${i}`);
}
```

### Template strings

```
let name = "Slate";
print(`Hello, ${name}! 2 + 2 = ${2 + 2}`);
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
for i in 1..20 {
    unless (i % 15 == 0 or i % 3 == 0 or i % 5 == 0) {
        print(i);
    } else if (i % 15 == 0) {
        print("FizzBuzz");
    } else if (i % 3 == 0) {
        print("Fizz");
    } else {
        print("Buzz");
    }
}
```

## Design notes

- **Lexer** (`lexer.py`): hand-written scanner producing `Token(type, value, line)`
  objects. Handles numbers, strings, template strings (`` `...${expr}...` ``),
  identifiers/keywords, operators, and `#` comments.
- **Parser** (`parser.py`): recursive-descent parser with standard precedence
  climbing for expressions (`or/and` → `==/!=` → `</>/<=/>=` → `+/-` → `*/%//` → unary → primary).
  `else if` is handled by recursively parsing another `if` statement as the else-branch,
  and `unless` reuses the same `If` node with a negated condition. Each `${...}`
  segment inside a template string is re-lexed and re-parsed as its own expression.
- **Interpreter** (`interpreter.py`): tree-walking evaluator. Each block
  (`{ ... }`, loop bodies, `for`-loop scope) creates a new `Environment`
  chained to its parent, giving proper lexical scoping — a variable declared
  inside a block or loop doesn't leak into the outer scope, but inner scopes
  can read and reassign outer variables.
- Errors (lexing, parsing, runtime) are reported with line numbers and a
  clear message rather than raw Python tracebacks.

## Possible extensions

- A REPL mode in `main.py`
- Hash maps / objects
- User-defined operators or a pipeline (`|>`) operator
