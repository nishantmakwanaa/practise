import re
import random

def analyze_csharp(code):
    issues = []
    suggestions = []
    test_cases = []
    
    console_writes = re.findall(r'Console\.Write', code)
    if console_writes:
        issues.append({
            "line": find_line_number(code, 'Console.Write'),
            "message": "Use a logging framework instead of Console.WriteLine in production code",
            "severity": "info",
            "type": "readability"
        })
    
    try_blocks = re.findall(r'\btry\s*\{', code)
    catch_blocks = re.findall(r'\bcatch\s*\(', code)
    if try_blocks and len(try_blocks) > len(catch_blocks):
        issues.append({
            "line": find_line_number(code, 'try {'),
            "message": "Ensure all exceptions are properly caught and handled",
            "severity": "warning",
            "type": "security"
        })
    
    methods = re.findall(r'(public|private|protected)?\s+\w+\s+(\w+)\s*$$([^)]*)$$', code)
    
    for access, method_name, params in methods:
        if method_name in ['if', 'for', 'while', 'switch']:
            continue
            
        param_list = []
        for p in params.split(','):
            if p.strip():
                parts = p.strip().split()
                if len(parts) > 1:
                    param_list.append(parts[-1])
        
        test_code = generate_csharp_test(method_name, param_list)
        test_cases.append({
            "name": f"Test {method_name}()",
            "code": test_code,
            "description": f"xUnit test for the {method_name} method"
        })
    
    readability_score = calculate_readability_score(code, issues)
    security_score = calculate_security_score(code, issues)
    performance_score = calculate_performance_score(code)
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

def generate_csharp_test(method_name, params):
    return f"""
using Xunit;
using System;

public class {method_name.capitalize()}Tests
{{
    [Fact]
    public void Test{method_name.capitalize()}()
    {{
        // Arrange
        var sut = new YourClass();
        
        // Act
        var result = sut.{method_name}({", ".join(["null" for _ in params])});
        
        // Assert
        Assert.NotNull(result);
    }}
}}
"""

def calculate_readability_score(code, issues):
    base_score = 80

    readability_issues = sum(1 for issue in issues if issue["type"] == "readability")
    
    comment_ratio = len(re.findall(r'\/\/|\/\*|\*\/', code)) / max(1, len(code.split('\n')))
    comment_bonus = min(10, int(comment_ratio * 100))
    
    return max(0, min(100, base_score - (readability_issues * 5) + comment_bonus))

def calculate_security_score(code, issues):
    base_score = 85
    
    security_issues = sum(1 for issue in issues if issue["type"] == "security")
    
    return max(0, min(100, base_score - (security_issues * 10)))

def calculate_performance_score(code):
    return random.randint(70, 90)
