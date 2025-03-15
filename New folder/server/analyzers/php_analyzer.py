import re
import random

def analyze_php(code):
    issues = []
    suggestions = []
    test_cases = []
    
    if 'mysql_query' in code and '$_' in code:
        issues.append({
            "line": find_line_number(code, 'mysql_query'),
            "message": "Potential SQL injection vulnerability. Use prepared statements instead.",
            "severity": "error",
            "type": "security"
        })
        
        if '$query' in code:
            suggestions.append({
                "description": "Use prepared statements to prevent SQL injection",
                "originalCode": "mysql_query($query);",
                "improvedCode": "$stmt = $pdo->prepare($query);\n$stmt->execute($params);"
            })
    
    if 'error_reporting(E_ALL)' in code:
        issues.append({
            "line": find_line_number(code, 'error_reporting'),
            "message": "Displaying all errors in production can reveal sensitive information",
            "severity": "warning",
            "type": "security"
        })
    
    functions = re.findall(r'function\s+(\w+)\s*$$([^)]*)$$', code)
    
    for func_name, params in functions:
        param_list = [p.strip().split('$')[-1] for p in params.split(',') if p.strip()]
        
        test_code = generate_php_test(func_name, param_list)
        test_cases.append({
            "name": f"Test {func_name}()",
            "code": test_code,
            "description": f"PHPUnit test for the {func_name} function"
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

def generate_php_test(func_name, params):
    return f"""
<?php
use PHPUnit\Framework\TestCase;

class {func_name.capitalize()}Test extends TestCase
{{
    public function test{func_name.capitalize()}()
    {{
        // Arrange
        $expected = 'expected_result';
        
        // Act
        $result = {func_name}({", ".join(["null" for _ in params])});
        
        // Assert
        $this->assertEquals($expected, $result);
    }}
}}
"""

def calculate_readability_score(code, issues):
    base_score = 75
    
    readability_issues = sum(1 for issue in issues if issue["type"] == "readability")
    
    return max(0, min(100, base_score - (readability_issues * 5)))

def calculate_security_score(code, issues):
    base_score = 80
    
    security_issues = sum(1 for issue in issues if issue["type"] == "security")
    security_errors = sum(1 for issue in issues if issue["type"] == "security" and issue["severity"] == "error")
    
    return max(0, min(100, base_score - (security_issues * 5) - (security_errors * 15)))

def calculate_performance_score(code):
    return random.randint(65, 85)
