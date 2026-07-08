# Demonstrates: functions, arrays, template strings, `repeat`, `unless`,
# range-based `for...in`, and break/continue

# --- Recursive function with a return value ---
func factorial(n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

print(`factorial(6) = ${factorial(6)}`);

# --- Function operating on an array (bubble sort) ---
func bubble_sort(arr) {
    let n = len(arr);
    for i in 0..n - 1 {
        for j in 0..n - i - 2 {
            if (arr[j] > arr[j + 1]) {
                let temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
    return arr;
}

let numbers = [5, 2, 9, 1, 5, 6, 3];
print(`unsorted: ${numbers}`);
bubble_sort(numbers);
print(`sorted:   ${numbers}`);

# --- push/pop builtins ---
let stack = [];
push(stack, 10);
push(stack, 20);
push(stack, 30);
print(`stack after pushes: ${stack}`);
print(`popped: ${pop(stack)}`);
print(`stack after pop:    ${stack}`);

# --- `repeat ... times` for simple counted work ---
repeat 3 times as round {
    print(`greeting round ${round}: hello!`);
}

# --- break / continue inside a range loop ---
print("numbers 1..20, skipping multiples of 3, stopping at first multiple of 7 above 10:");
for k in 1..20 {
    if (k % 3 == 0) {
        continue;
    }
    if (k > 10 and k % 7 == 0) {
        break;
    }
    print(k);
}
