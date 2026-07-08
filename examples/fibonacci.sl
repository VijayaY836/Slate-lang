# Print the first 10 Fibonacci numbers using a range-based for loop
let a = 0;
let b = 1;

print("Fibonacci sequence:");
for i in 0..9 {
    print(a);
    let temp = a + b;
    a = b;
    b = temp;
}

# Bonus: a prime checker using `unless` and nested loops
print("Primes up to 30:");
for n in 2..30 {
    let is_prime = true;
    let d = 2;
    while (d * d <= n) {
        if (n % d == 0) {
            is_prime = false;
        }
        d = d + 1;
    }
    unless (not is_prime) {
        print(`${n} is prime`);
    }
}
