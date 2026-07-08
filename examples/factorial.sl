# Compute the factorial of n using a while loop
let n = 10;
let result = 1;
let i = 1;

while (i <= n) {
    result = result * i;
    i = i + 1;
}

print("Factorial of", n, "is", result);
