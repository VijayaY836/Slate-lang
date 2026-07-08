# Slate Programming Guide

Slate is a tiny language you write in plain `.sl` text files. This guide
walks through everything you need to write your own programs, from "hello
world" to functions and arrays. Run any file with:

```bash
python main.py yourfile.sl
```

---

## 1. Hello, World

```
print("Hello, world!");
```

Every statement ends with a semicolon `;`. `print` accepts one or more
comma-separated values.

```
print("The answer is", 42);
```

---

## 2. Comments

Anything after `#` on a line is ignored.

```
# this is a comment
print("still runs");   # this too
```

---

## 3. Variables

Declare with `let`, reassign without it:

```
let name = "Vij";
let age = 21;
age = age + 1;          # no 'let' when reassigning
print(name, "is", age);
```

Types: numbers (`5`, `3.14`), strings (`"text"`), booleans (`true`/`false`).

---

## 4. Operators

```
+  -  *  /  %        # arithmetic (% is remainder)
== != < > <= >=       # comparison, gives true/false
and  or  not          # boolean logic
```

`+` also joins strings: `"score: " + 10` → `"score: 10"`.

For building strings out of multiple values, template strings are
usually nicer than `+`-chains. Wrap the text in backticks and drop any
expression inside `${...}`:

```
let name = "Vij";
let age = 21;
print(`${name} is ${age} years old`);   # Vij is 21 years old
print(`next year: ${age + 1}`);          # next year: 22
```

---

## 5. Conditions

```
let x = 7;
if (x > 10) {
    print("big");
} else if (x > 5) {
    print("medium");
} else {
    print("small");
}
```

The `else if` chain can be as long as you like; `else` is optional.

`unless` is the mirror image of `if` — read it as "do this unless the
condition holds" for cases where a negative check reads more naturally
than `if (not ...)`:

```
let age = 15;
unless (age >= 18) {
    print("no entry");
} else {
    print("welcome");
}
```

---

## 6. Loops

**while** — repeats as long as the condition is true:

```
let i = 0;
while (i < 5) {
    print(i);
    i = i + 1;
}
```

**for (classic)** — the setup/condition/step live in one line:

```
for (let i = 0; i < 5; i = i + 1) {
    print(i);
}
```

**for...in (range)** — the more expressive way to count. Ranges are
inclusive on both ends and default to a step of `1`; if `end` is less
than `start`, the loop simply runs zero times, unless you supply an
explicit (negative) `step`:

```
for i in 1..5 {
    print(i);            # 1 2 3 4 5
}

for i in 0..10 step 2 {
    print(i);            # 0 2 4 6 8 10
}

for i in 5..1 step -1 {
    print(i);            # 5 4 3 2 1 -- counting down
}
```

**repeat...times** — for when you just need to do something N times
and don't care about a loop variable (add `as name` if you do want a
0-indexed counter):

```
repeat 3 times {
    print("hi");
}

repeat 3 times as round {
    print(`round ${round}`);
}
```

**break** exits the loop immediately. **continue** skips to the next
iteration (in a `for` loop, the step still runs).

```
let i = 0;
while (i < 10) {
    i = i + 1;
    if (i % 2 == 0) { continue; }   # skip even numbers
    if (i > 7) { break; }           # stop once i passes 7
    print(i);
}
```

---

## 7. Functions

Define with `func`, return a value with `return`:

```
func add(a, b) {
    return a + b;
}
print(add(2, 3));   # 5
```

Functions can call themselves (recursion):

```
func factorial(n) {
    if (n <= 1) { return 1; }
    return n * factorial(n - 1);
}
print(factorial(5));   # 120
```

A function with no `return` gives back `null`. You can define functions
anywhere in the file — even after the code that calls them.

---

## 8. Arrays

```
let nums = [10, 20, 30];
print(nums[0]);        # 10 (indexing starts at 0)
nums[0] = 99;           # change an element
print(nums);            # [99, 20, 30]
```

Built-in helpers:

```
len(nums)          # number of elements
push(nums, 40)      # add an element to the end
pop(nums)           # remove and return the last element
```

Arrays passed into a function are shared, so a function can modify the
caller's array directly:

```
func double_all(arr) {
    let i = 0;
    while (i < len(arr)) {
        arr[i] = arr[i] * 2;
        i = i + 1;
    }
}
let vals = [1, 2, 3];
double_all(vals);
print(vals);   # [2, 4, 6]
```

---

## 9. Putting it together — FizzBuzz

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

---

## 10. Common mistakes

| Mistake | Fix |
|---|---|
| Forgetting `;` at the end of a statement | Every statement (not blocks) needs one |
| Reassigning with `let` again | Only use `let` the first time; drop it after |
| Using a variable before declaring it | Declare with `let` before you read it |
| Array index out of range | Check `len(arr)` first |
| Mismatched function argument count | Call must pass exactly as many args as params |
| `for i in 5..1 { ... }` runs zero times | Ranges default to step `1`; add `step -1` to count down |

---

## 11. More examples

See the `examples/` folder:

- `fizzbuzz.sl` — the classic, with a range `for...in` loop and `unless`
- `factorial.sl` — factorial with a range `for...in` loop and a template string
- `fibonacci.sl` — Fibonacci sequence + a prime sieve using `unless`
- `features_demo.sl` — recursion, arrays, bubble sort, `repeat...times`,
  template strings, `break`/`continue`

Copy one, tweak it, and run it to see how things work.