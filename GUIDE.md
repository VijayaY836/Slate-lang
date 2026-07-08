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

**for** — same idea, but the setup/condition/step live in one line:

```
for (let i = 0; i < 5; i = i + 1) {
    print(i);
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

---

## 10. Common mistakes

| Mistake | Fix |
|---|---|
| Forgetting `;` at the end of a statement | Every statement (not blocks) needs one |
| Reassigning with `let` again | Only use `let` the first time; drop it after |
| Using a variable before declaring it | Declare with `let` before you read it |
| Array index out of range | Check `len(arr)` first |
| Mismatched function argument count | Call must pass exactly as many args as params |

---

## 11. More examples

See the `examples/` folder:

- `fizzbuzz.sl` — the classic
- `factorial.sl` — factorial with a `while` loop
- `fibonacci.sl` — Fibonacci sequence + a prime sieve
- `features_demo.sl` — recursion, arrays, bubble sort, `break`/`continue`

Copy one, tweak it, and run it to see how things work.