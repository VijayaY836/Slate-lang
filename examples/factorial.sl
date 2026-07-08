# Compute the factorial of n using a range-based for loop
let n = 10;
let result = 1;

for i in 1..n {
    result = result * i;
}

print(`Factorial of ${n} is ${result}`);
