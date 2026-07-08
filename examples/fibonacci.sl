# Print the first 10 Fibonacci numbers using a for loop
let a = 0;
let b = 1;

print("Fibonacci sequence:");
for (let i = 0; i < 10; i = i + 1) {
    print(a);
    let temp = a + b;
    a = b;
    b = temp;
}

# Bonus: a prime checker using nested loops and conditions
print("Primes up to 30:");
let n = 2;
while (n <= 30) {
    let is_prime = true;
    let d = 2;
    while (d * d <= n) {
        if (n % d == 0) {
            is_prime = false;
        }
        d = d + 1;
    }
    if (is_prime) {
        print(n);
    }
    n = n + 1;
}
