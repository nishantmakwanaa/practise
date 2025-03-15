import re
import random

def analyze_cpp(code):
    issues = []
    suggestions = []
    test_cases = []
    
    if 'new' in code and 'delete' not in code:
        issues.append({
            "line": find_line_number(code, 'new'),
            "message": "Memory allocated with 'new' but no 'delete' found. Potential memory leak.",
            "severity": "warning",
            "type": "performance"
        })
        
        suggestions.append({
            "description": "Use smart pointers instead of raw pointers to avoid memory leaks",
            "originalCode": "int* ptr = new int(10);",
            "improvedCode": "std::unique_ptr<int> ptr = std::make_unique<int>(10);"
        })
    
    if 'using namespace std;' in code:
        issues.append({
            "line": find_line_number(code, 'using namespace std;'),
            "message": "Avoid 'using namespace std;' in header files as it can lead to name conflicts",
            "severity": "info",
            "type": "readability"
        })
    
    functions = re.findall(r'(\w+)\s+(\w+)\s*$$([^)]*)$$', code)
    
    for return_type, func_name, params in functions:
        if func_name in ['if', 'for', 'while', 'switch', 'class', 'struct']:
            continue
            
        param_list = []
        for p in params.split(','):
            if p.strip():
                parts = p.strip().split()
                if len(parts) > 1:
                    param_list.append(parts[-1])

        test_code = generate_cpp_test(func_name, param_list, return_type)
        test_cases.append({
            "name": f"Test {func_name}()",
            "code": test_code,
            "description": f"Google Test for the {func_name} function"
        })
    
    readability_score = calculate_readability_score(code, issues)
    security_score = calculate_security_score(code, issues)
    performance_score = calculate_performance_score(code, issues)
    overall_score = (readability_score + security_score + performance_score) / 3
    
    return {
        "issues": issues,
        "suggestions": suggestions,
        "testCases": test_cases,
        "metrics": {
            "readabilityScore": readability_score,
            "securityScore": security_score,
            "performanceScore": performance_score,
            "overallScore": overall_score
        }
    }

def find_line_number(code, pattern):
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if pattern in line:
            return i + 1
    return 1

def generate_cpp_test(func_name, params, return_type):
    return f"""
#include <gtest/gtest.h>

TEST({func_name.capitalize()}Test, BasicFunctionality) {{
    // Arrange
    {"int expected = 0;" if return_type == "int" else "auto expected = nullptr;"}
    
    // Act
    auto result = {func_name}({", ".join(["0" if i % 2 == 0 else "nullptr" for i in range(len(params))])});
    
    // Assert
    {"EXPECT_EQ(expected, result);" if return_type != "void" else "// No return value to check for void functions"}
}}
"""

def calculate_readability_score(code, issues):
    base_score = 75
    
    readability_issues = sum(1 for issue in issues if issue["type"] == "readability")
    
    comment_ratio = len(re.findall(r'\/\/|\/\*|\*\/', code)) / max(1, len(code.split('\n')))
    comment_bonus = min(15, int(comment_ratio * 100))
    
    return max(0, min(100, base_score - (readability_issues * 5) + comment_bonus))

def calculate_security_score(code, issues):
    base_score = 80
    
    security_issues = sum(1 for issue in issues if issue["type"] == "security")
    
    return max(0, min(100, base_score - (security_issues * 10)))

def calculate_performance_score(code, issues):
    base_score = 85
    
    performance_issues = sum(1 for issue in issues if issue["type"] == "performance")
    
    return max(0, min(100, base_score - (performance_issues * 10)))
