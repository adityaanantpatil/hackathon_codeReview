# Sample Python code for testing CodeReview AI
# This code has intentional issues for demonstration

def calculate_sum(a, b):
    result = a + b
    print("The sum is: " + str(result))
    return result

x = calculate_sum(5, 10)
print(x)

# Issues this code demonstrates:
# 1. Missing indentation
# 2. No type hints
# 3. Using string concatenation instead of f-strings
# 4. No docstring
# 5. Poor variable naming
# 6. No error handling
