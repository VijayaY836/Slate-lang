# FizzBuzz from 1 to 20 -- using a range-based for loop and `unless`
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
