// Sample C++ code for testing CodeReview AI
// This code has intentional issues for demonstration

#include <iostream>
using namespace std;

int calculateSum(int a,int b) {
    int result=a+b;
    cout << "Sum is: " << result << endl;
    return result;
}

int main() {
    int x = calculateSum(5,10);
    cout << x << endl;
    return 0;
}

// Issues this code demonstrates:
// 1. Using 'using namespace std' (bad practice)
// 2. No const correctness
// 3. No header guards (if in header file)
// 4. No documentation comments
// 5. Poor variable naming
// 6. No input validation
