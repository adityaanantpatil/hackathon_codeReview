// Sample JavaScript code for testing CodeReview AI
// This code has intentional issues for demonstration

function calculateSum(a,b) {
    var result = a + b;
    console.log("The sum is: " + result);
    return result;
}

var x = calculateSum(5, 10);
console.log(x);

// Issues this code demonstrates:
// 1. Using 'var' instead of 'const/let'
// 2. No parameter validation
// 3. String concatenation instead of template literals
// 4. No JSDoc comments
// 5. No error handling
// 6. Console.log in production code
