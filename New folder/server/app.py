from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os
import requests
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import traceback
import ast
import astroid
from pylint import epylint as lint
import io
import sys
from contextlib import redirect_stdout
import tempfile
import subprocess
import threading
import queue
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import numpy as np
import logging
import random
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
MODEL_NAME = "microsoft/codebert-base"
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    code_analyzer = pipeline("text-classification", model=model, tokenizer=tokenizer)
    logger.info("AI model loaded successfully")
except Exception as e:
    logger.error(f"Error loading AI model: {e}")
    code_analyzer = None

def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'codeanalyzer'),
        user=os.environ.get('DB_USER', 'nishant'),
        password=os.environ.get('DB_PASSWORD', 'nishant'),
        port=os.environ.get('DB_PORT', '5432')
    )
    conn.autocommit = True
    return conn

def init_db():
    """Initialize the database with required tables."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            language VARCHAR(50) NOT NULL,
            code TEXT NOT NULL,
            result JSONB NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cur.close()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

init_db()

PISTON_API_URL = "https://emkc.org/api/v2/piston/execute"
PISTON_LANGUAGES = {
    'javascript': {'language': 'javascript', 'version': '18.15.0'},
    'python': {'language': 'python', 'version': '3.10.0'},
    'java': {'language': 'java', 'version': '15.0.2'},
    'php': {'language': 'php', 'version': '8.2.3'},
    'cpp': {'language': 'cpp', 'version': '10.2.0'},
    'csharp': {'language': 'csharp', 'version': '6.12.0'}
}

def analyze_with_ai_model(code, language):
    """Analyze code using the AI model."""
    if code_analyzer is None:
        return {
            "ai_analysis": {
                "quality_score": 5.0,
                "confidence": 0.5,
                "suggestions": ["AI model not available. Using rule-based analysis instead."]
            }
        }
    
    try:
        max_length = tokenizer.model_max_length
        code_tokens = tokenizer.tokenize(code)
        if len(code_tokens) > max_length:
            code_tokens = code_tokens[:max_length]
            code = tokenizer.convert_tokens_to_string(code_tokens)
        
        result = code_analyzer(code)
        
        label = result[0]['label']
        score = result[0]['score']
        
        quality_mapping = {
            "LABEL_0": "Poor quality code",
            "LABEL_1": "Average quality code",
            "LABEL_2": "Good quality code"
        }
        
        quality_score = score * 10
        
        suggestions = []
        if quality_score < 5:
            suggestions.append("Consider refactoring this code for better maintainability.")
            suggestions.append("The code structure could be improved for better readability.")
        elif quality_score < 8:
            suggestions.append("Code is decent but could benefit from some improvements.")
        else:
            suggestions.append("Code appears to be well-structured.")
        
        return {
            "ai_analysis": {
                "quality_score": round(quality_score, 2),
                "confidence": round(score, 2),
                "suggestions": suggestions
            }
        }
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return {
            "ai_analysis": {
                "quality_score": 5.0,
                "confidence": 0.5,
                "suggestions": ["Error in AI analysis. Using rule-based analysis instead."]
            }
        }

def analyze_javascript(code):
    """Enhanced JavaScript code analyzer with more detailed analysis."""
    analysis = {
        "complexity": 0,
        "quality": 0,
        "issues": [],
        "suggestions": [],
        "summary": "",
        "metrics": {}
    }
    
    semicolon_issues = re.findall(r'[^;{}\s]\s*$', code, re.MULTILINE)
    if semicolon_issues:
        analysis["issues"].append({
            "type": "style",
            "severity": "warning",
            "message": f"Missing semicolons detected ({len(semicolon_issues)} occurrences)"
        })
    
    console_logs = re.findall(r'console\.log\(', code)
    if console_logs:
        analysis["issues"].append({
            "type": "debug",
            "severity": "info",
            "message": f"Found {len(console_logs)} console.log statements that should be removed in production"
        })
    
    var_usage = re.findall(r'\bvar\b', code)
    if var_usage:
        analysis["issues"].append({
            "type": "modernization",
            "severity": "warning",
            "message": f"Using 'var' instead of 'const' or 'let' ({len(var_usage)} occurrences)"
        })
        analysis["suggestions"].append({
            "message": "Replace 'var' with 'const' for variables that don't change, or 'let' for variables that do"
        })
    
    try_catch_count = len(re.findall(r'\btry\b', code))
    if try_catch_count == 0 and len(code) > 100:
        analysis["issues"].append({
            "type": "robustness",
            "severity": "warning",
            "message": "No error handling (try/catch) found in code"
        })
        analysis["suggestions"].append({
            "message": "Consider adding error handling with try/catch blocks for robust code"
        })
    
    event_listeners = re.findall(r'addEventListener\(', code)
    event_removals = re.findall(r'removeEventListener\(', code)
    if len(event_listeners) > len(event_removals):
        analysis["issues"].append({
            "type": "memory",
            "severity": "warning",
            "message": f"Potential memory leak: {len(event_listeners) - len(event_removals)} event listeners without corresponding removal"
        })
    
    es6_features = {
        "Arrow functions": len(re.findall(r'=>', code)),
        "Template literals": len(re.findall(r'`', code)),
        "Destructuring": len(re.findall(r'\{[^{}]*\}\s*=', code)),
        "Spread operator": len(re.findall(r'\.\.\.', code)),
        "Async/await": len(re.findall(r'\basync\b|\bawait\b', code))
    }
    
    analysis["metrics"] = {
        "lines": len(code.split('\n')),
        "characters": len(code),
        "functions": len(re.findall(r'\bfunction\b|\s=>\s', code)),
        "es6_features": es6_features
    }

    control_structures = len(re.findall(r'\b(if|for|while|switch|catch)\b', code))
    functions = len(re.findall(r'\bfunction\b|\s=>\s', code))
    nesting_level = max([len(line.split('{')) for line in code.split('\n')])
    
    analysis["complexity"] = min(10, (control_structures + functions + nesting_level) / 3)

    issue_count = len(analysis["issues"])
    modern_score = sum(es6_features.values()) / 5
    analysis["quality"] = max(0, 10 - issue_count + min(3, modern_score))
    
    analysis["summary"] = f"Found {issue_count} issues. Code quality: {analysis['quality']:.1f}/10. Complexity: {analysis['complexity']:.1f}/10."
    
    ai_analysis = analyze_with_ai_model(code, "javascript")
    if ai_analysis:
        analysis.update(ai_analysis)
    
    return analysis

def analyze_python(code):
    """Enhanced Python code analyzer with static analysis."""
    analysis = {
        "complexity": 0,
        "quality": 0,
        "issues": [],
        "suggestions": [],
        "summary": "",
        "metrics": {}
    }
    
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if len(line) > 79:
            analysis["issues"].append({
                "type": "style",
                "severity": "info",
                "line": i + 1,
                "message": "Line too long (> 79 characters)"
            })
        
        if re.match(r'^( {1,3}|\t)\w', line):
            analysis["issues"].append({
                "type": "style",
                "severity": "warning",
                "line": i + 1,
                "message": "Inconsistent indentation (use 4 spaces)"
            })
    
    print_statements = re.findall(r'\bprint\(', code)
    if print_statements:
        analysis["issues"].append({
            "type": "debug",
            "severity": "info",
            "message": f"Found {len(print_statements)} print statements that should use logging in production"
        })
    
    try:
        parsed = astroid.parse(code)
        
        functions = [node for node in parsed.nodes_of_class(astroid.FunctionDef)]
        classes = [node for node in parsed.nodes_of_class(astroid.ClassDef)]
        
        missing_docstrings = 0
        for func in functions:
            if not ast.get_docstring(func):
                missing_docstrings += 1
                analysis["issues"].append({
                    "type": "documentation",
                    "severity": "info",
                    "line": func.lineno,
                    "message": f"Function '{func.name}' missing docstring"
                })
        
        for cls in classes:
            if not ast.get_docstring(cls):
                missing_docstrings += 1
                analysis["issues"].append({
                    "type": "documentation",
                    "severity": "info",
                    "line": cls.lineno,
                    "message": f"Class '{cls.name}' missing docstring"
                })
        
        try_blocks = [node for node in parsed.nodes_of_class(astroid.TryExcept)]
        if len(try_blocks) == 0 and len(functions) > 1:
            analysis["issues"].append({
                "type": "robustness",
                "severity": "warning",
                "message": "No exception handling found in code"
            })
            analysis["suggestions"].append({
                "message": "Consider adding try/except blocks for error handling"
            })
        
        analysis["metrics"] = {
            "lines": len(lines),
            "characters": len(code),
            "functions": len(functions),
            "classes": len(classes),
            "complexity": sum(1 + node.max_col_offset // 4 for node in functions)  # Simple complexity metric
        }
        
        control_structures = len(re.findall(r'\b(if|for|while|try|with)\b', code))
        analysis["complexity"] = min(10, (control_structures + len(functions) + len(classes)) / 3)
        
    except Exception as e:
        logger.error(f"Error in Python static analysis: {e}")
        control_structures = len(re.findall(r'\b(if|for|while|try|with)\b', code))
        functions = len(re.findall(r'\bdef\b', code))
        classes = len(re.findall(r'\bclass\b', code))
        analysis["complexity"] = min(10, (control_structures + functions + classes) / 3)
        
        analysis["metrics"] = {
            "lines": len(lines),
            "characters": len(code),
            "functions": functions,
            "classes": classes
        }
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w+', delete=False) as temp:
            temp.write(code)
            temp_filename = temp.name
        
        pylint_output = io.StringIO()
        with redirect_stdout(pylint_output):
            lint.lint([temp_filename])
        
        pylint_score = 0.0
        for line in pylint_output.getvalue().split('\n'):
            if "Your code has been rated at" in line:
                match = re.search(r'(\d+\.\d+)/10', line)
                if match:
                    pylint_score = float(match.group(1))
                    break
        
        os.unlink(temp_filename)
        
        if pylint_score > 0:
            analysis["quality"] = pylint_score
        else:
            issue_count = len(analysis["issues"])
            analysis["quality"] = max(0, 10 - issue_count)
    except Exception as e:
        logger.error(f"Error running pylint: {e}")
        issue_count = len(analysis["issues"])
        analysis["quality"] = max(0, 10 - issue_count)
    
    analysis["summary"] = f"Found {len(analysis['issues'])} issues. Code quality: {analysis['quality']:.1f}/10. Complexity: {analysis['complexity']:.1f}/10."
    
    ai_analysis = analyze_with_ai_model(code, "python")
    if ai_analysis:
        analysis.update(ai_analysis)
    
    return analysis

def analyze_java(code):
    """Enhanced Java code analyzer."""
    analysis = {
        "complexity": 0,
        "quality": 0,
        "issues": [],
        "suggestions": [],
        "summary": "",
        "metrics": {}
    }
    
    if re.search(r'(if|for|while)\s*$$[^)]*$$[^{]*$', code, re.MULTILINE):
        analysis["issues"].append({
            "type": "style",
            "severity": "warning",
            "message": "Control statements without braces detected"
        })

    print_statements = re.findall(r'System\.out\.println', code)
    if print_statements:
        analysis["issues"].append({
            "type": "debug",
            "severity": "info",
            "message": f"Found {len(print_statements)} System.out.println statements that should use logging in production"
        })
    
    try_blocks = re.findall(r'\btry\b', code)
    catch_blocks = re.findall(r'\bcatch\b', code)
    if len(try_blocks) == 0 and len(code) > 200:
        analysis["issues"].append({
            "type": "robustness",
            "severity": "warning",
            "message": "No exception handling found in code"
        })
        analysis["suggestions"].append({
            "message": "Consider adding try/catch blocks for error handling"
        })

    if 'new FileInputStream' in code and 'try-with-resources' not in code and 'close()' not in code:
        analysis["issues"].append({
            "type": "resource",
            "severity": "error",
            "message": "Resources not properly closed (use try-with-resources)"
        })
    
    null_checks = re.findall(r'!= null|== null', code)
    object_creations = re.findall(r'new \w+', code)
    if len(null_checks) < len(object_creations) / 3:
        analysis["issues"].append({
            "type": "robustness",
            "severity": "warning",
            "message": "Insufficient null checks for object references"
        })
    
    classes = re.findall(r'class\s+(\w+)', code)
    methods = re.findall(r'(public|private|protected)\s+\w+\s+(\w+)\s*\(', code)

    analysis["metrics"] = {
        "lines": len(code.split('\n')),
        "characters": len(code),
        "classes": len(classes),
        "methods": len(methods),
        "try_catch_blocks": len(try_blocks)
    }

    control_structures = len(re.findall(r'\b(if|for|while|switch|catch)\b', code))
    nesting_level = max([len(line.split('{')) for line in code.split('\n')])
    
    analysis["complexity"] = min(10, (control_structures + len(methods) + nesting_level) / 3)
    
    issue_count = len(analysis["issues"])
    severe_issues = sum(1 for issue in analysis["issues"] if issue.get("severity") == "error")
    analysis["quality"] = max(0, 10 - issue_count - severe_issues)
    
    analysis["summary"] = f"Found {issue_count} issues. Code quality: {analysis['quality']:.1f}/10. Complexity: {analysis['complexity']:.1f}/10."
    
    ai_analysis = analyze_with_ai_model(code, "java")
    if ai_analysis:
        analysis.update(ai_analysis)
    
    return analysis

def analyze_php(code):
    """Enhanced PHP code analyzer."""
    analysis = {
        "complexity": 0,
        "quality": 0,
        "issues": [],
        "suggestions": [],
        "summary": "",
        "metrics": {}
    }
    
    if re.search(r'[^;{}]\s*$', code, re.MULTILINE):
        analysis["issues"].append({
            "type": "syntax",
            "severity": "error",
            "message": "Missing semicolons detected"
        })

    echo_statements = re.findall(r'\becho\b', code)
    if echo_statements:
        analysis["issues"].append({
            "type": "debug",
            "severity": "info",
            "message": f"Found {len(echo_statements)} echo statements"
        })
    
    try_blocks = re.findall(r'\btry\b', code)
    if len(try_blocks) == 0 and len(code) > 200:
        analysis["issues"].append({
            "type": "robustness",
            "severity": "warning",
            "message": "No exception handling found in code"
        })
        analysis["suggestions"].append({
            "message": "Consider adding try/catch blocks for error handling"
        })

    if 'mysql_query' in code or 'mysqli_query' in code:
        if 'prepare' not in code and 'bindParam' not in code:
            analysis["issues"].append({
                "type": "security",
                "severity": "critical",
                "message": "Potential SQL injection vulnerability (use prepared statements)"
            })
    
    deprecated_functions = ['mysql_', 'ereg', 'split', 'create_function']
    for func in deprecated_functions:
        if func in code:
            analysis["issues"].append({
                "type": "deprecation",
                "severity": "warning",
                "message": f"Using deprecated function '{func}'"
            })
    
    functions = re.findall(r'function\s+(\w+)\s*\(', code)
    classes = re.findall(r'class\s+(\w+)', code)
    
    analysis["metrics"] = {
        "lines": len(code.split('\n')),
        "characters": len(code),
        "functions": len(functions),
        "classes": len(classes)
    }
    
    control_structures = len(re.findall(r'\b(if|for|foreach|while|switch|catch)\b', code))
    nesting_level = max([len(line.split('{')) for line in code.split('\n')])
    
    analysis["complexity"] = min(10, (control_structures + len(functions) + nesting_level) / 3)
    
    issue_count = len(analysis["issues"])
    severe_issues = sum(1 for issue in analysis["issues"] if issue.get("severity") in ["critical", "error"])
    analysis["quality"] = max(0, 10 - issue_count - severe_issues * 2)
    
    analysis["summary"] = f"Found {issue_count} issues. Code quality: {analysis['quality']:.1f}/10. Complexity: {analysis['complexity']:.1f}/10."
    
    ai_analysis = analyze_with_ai_model(code, "php")
    if ai_analysis:
        analysis.update(ai_analysis)
    
    return analysis

def analyze_cpp(code):
    """Enhanced C++ code analyzer."""
    analysis = {
        "complexity": 0,
        "quality": 0,
        "issues": [],
        "suggestions": [],
        "summary": "",
        "metrics": {}
    }
    
    if re.search(r'[^;{}]\s*$', code, re.MULTILINE):
        analysis["issues"].append({
            "type": "syntax",
            "severity": "error",
            "message": "Missing semicolons detected"
        })
    
    cout_statements = re.findall(r'std::cout|cout\s*<<', code)
    if cout_statements:
        analysis["issues"].append({
            "type": "debug",
            "severity": "info",
            "message": f"Found {len(cout_statements)} cout statements"
        })
    
    new_ops = re.findall(r'\bnew\b', code)
    delete_ops = re.findall(r'\bdelete\b', code)
    if len(new_ops) > len(delete_ops):
        analysis["issues"].append({
            "type": "memory",
            "severity": "critical",
            "message": f"Potential memory leak: {len(new_ops) - len(delete_ops)} 'new' operations without corresponding 'delete'"
        })
        analysis["suggestions"].append({
            "message": "Consider using smart pointers (std::unique_ptr, std::shared_ptr) instead of raw pointers"
        })
    
    # Check for exception handling
    try_blocks = re.findall(r'\btry\b', code)
    if len(try_blocks) == 0 and len(code) > 200:
        analysis["issues"].append({
            "type": "robustness",
            "severity": "warning",
            "message": "No exception handling found in code"
        })
    
    # Check for modern C++ features
    modern_features = {
        "auto": len(re.findall(r'\bauto\b', code)),
        "lambda": len(re.findall(r'\[\s*\]', code)),
        "range-for": len(re.findall(r'for\s*\(\s*\w+\s*:\s*', code)),
        "nullptr": len(re.findall(r'\bnullptr\b', code)),
        "smart_pointers": len(re.findall(r'unique_ptr|shared_ptr|weak_ptr', code))
    }
    
    if sum(modern_features.values()) == 0 and len(code) > 100:
        analysis["suggestions"].append({
            "message": "Consider using modern C++ features (auto, lambdas, range-for, nullptr, smart pointers)"
        })
    
    # Extract function information
    functions = re.findall(r'(\w+)\s+(\w+)\s*$$[^)]*$$\s*(?:const)?\s*{', code)
    classes = re.findall(r'class\s+(\w+)', code)
    
    # Add metrics
    analysis["metrics"] = {
        "lines": len(code.split('\n')),
        "characters": len(code),
        "functions": len(functions),
        "classes": len(classes),
        "modern_features": modern_features
    }
    
    # Calculate complexity
    control_structures = len(re.findall(r'\b(if|for|while|switch|catch)\b', code))
    nesting_level = max([len(line.split('{')) for line in code.split('\n')])
    
    analysis["complexity"] = min(10, (control_structures + len(functions) + nesting_level) / 3)
    
    # Calculate quality score
    issue_count = len(analysis["issues"])
    severe_issues = sum(1 for issue in analysis["issues"] if issue.get("severity") in ["critical", "error"])
    modern_score = sum(modern_features.values()) / 5  # Normalize by number of features
    
    analysis["quality"] = max(0, 10 - issue_count - severe_issues * 2 + min(3, modern_score))
    
    # Generate summary
    analysis["summary"] = f"Found {issue_count} issues. Code quality: {analysis['quality']:.1f}/10. Complexity: {analysis['complexity']:.1f}/10."
    
    # Add AI-based analysis if available
    ai_analysis = analyze_with_ai_model(code, "cpp")
    if ai_analysis:
        analysis.update(ai_analysis)
    
    return analysis

def analyze_csharp(code):
    """Enhanced C# code analyzer."""
    analysis = {
        "complexity": 0,
        "quality": 0,
        "issues": [],
        "suggestions": [],
        "summary": "",
        "metrics": {}
    }
    
    # Check for missing semicolons
    if re.search(r'[^;{}]\s*$', code, re.MULTILINE):
        analysis["issues"].append({
            "type": "syntax",
            "severity": "error",
            "message": "Missing semicolons detected"
        })
    
    # Check for Console.WriteLine
    print_statements = re.findall(r'Console\.WriteLine', code)
    if print_statements:
        analysis["issues"].append({
            "type": "debug",
            "severity": "info",
            "message": f"Found {len(print_statements)} Console.WriteLine statements that should use logging in production"
        })
    
    # Check for exception handling
    try_blocks = re.findall(r'\btry\b', code)
    if len(try_blocks) == 0 and len(code) > 200:
        analysis["issues"].append({
            "type": "robustness",
            "severity": "warning",
            "message": "No exception handling found in code"
        })
        analysis["suggestions"].append({
            "message": "Consider adding try/catch blocks for error handling"
        })
    
    # Check for resource management
    using_statements = re.findall(r'\busing\s*\(', code)
    disposable_patterns = re.findall(r'IDisposable|\.Dispose$$$$', code)
    if len(disposable_patterns) > 0 and len(using_statements) == 0:
        analysis["issues"].append({
            "type": "resource",
            "severity": "warning",
            "message": "Disposable resources not properly managed (use 'using' statements)"
        })
    
    # Check for modern C# features
    modern_features = {
        "var": len(re.findall(r'\bvar\b', code)),
        "lambda": len(re.findall(r'=>', code)),
        "linq": len(re.findall(r'\.Where\(|\.Select\(|\.OrderBy\(', code)),
        "async/await": len(re.findall(r'\basync\b|\bawait\b', code)),
        "null_conditional": len(re.findall(r'\?\.|\\?\[', code))
    }
    
    if sum(modern_features.values()) == 0 and len(code) > 100:
        analysis["suggestions"].append({
            "message": "Consider using modern C# features (var, lambdas, LINQ, async/await, null conditional operators)"
        })
    
    # Extract method and class information
    methods = re.findall(r'(public|private|protected|internal)\s+\w+\s+(\w+)\s*\(', code)
    classes = re.findall(r'class\s+(\w+)', code)
    
    # Add metrics
    analysis["metrics"] = {
        "lines": len(code.split('\n')),
        "characters": len(code),
        "methods": len(methods),
        "classes": len(classes),
        "modern_features": modern_features
    }
    
    # Calculate complexity
    control_structures = len(re.findall(r'\b(if|for|foreach|while|switch|catch)\b', code))
    nesting_level = max([len(line.split('{')) for line in code.split('\n')])
    
    analysis["complexity"] = min(10, (control_structures + len(methods) + nesting_level) / 3)
    
    # Calculate quality score
    issue_count = len(analysis["issues"])
    severe_issues = sum(1 for issue in analysis["issues"] if issue.get("severity") in ["critical", "error"])
    modern_score = sum(modern_features.values()) / 5  # Normalize by number of features
    
    analysis["quality"] = max(0, 10 - issue_count - severe_issues * 2 + min(3, modern_score))
    
    # Generate summary
    analysis["summary"] = f"Found {issue_count} issues. Code quality: {analysis['quality']:.1f}/10. Complexity: {analysis['complexity']:.1f}/10."
    
    # Add AI-based analysis if available
    ai_analysis = analyze_with_ai_model(code, "csharp")
    if ai_analysis:
        analysis.update(ai_analysis)
    
    return analysis

def generate_test_cases(code, language):
    """Generate more comprehensive test cases for the given code and language."""
    if language == 'javascript':
        # Extract function names and parameters
        function_matches = re.findall(r'function\s+(\w+)\s*$$([^)]*)$$', code)
        if not function_matches:
            function_matches = re.findall(r'const\s+(\w+)\s*=\s*(?:async\s*)?(?:$$[^)]*$$|[^=]*)\s*=>', code)
            if function_matches:
                # Extract parameters for arrow functions
                params_match = re.search(r'const\s+' + re.escape(function_matches[0]) + r'\s*=\s*(?:async\s*)?(?:$$([^)]*)$$|([^=]*))\s*=>', code)
                if params_match:
                    params = params_match.group(1) if params_match.group(1) else params_match.group(2)
                    function_matches = [(function_matches[0], params)]
        
        if function_matches:
            function_name, params = function_matches[0]
            params_list = [p.strip() for p in params.split(',') if p.strip()]
            
            # Analyze function body to generate better test cases
            function_body = ""
            in_function = False
            brace_count = 0
            
            for line in code.split('\n'):
                if re.search(r'function\s+' + re.escape(function_name) + r'\s*\(', line) or re.search(r'const\s+' + re.escape(function_name) + r'\s*=', line):
                    in_function = True
                
                if in_function:
                    function_body += line + '\n'
                    brace_count += line.count('{') - line.count('}')
                    if brace_count == 0 and '{' in function_body and '}' in function_body:
                        break
            
            # Generate test values based on parameter names and function body
            test_values = []
            for param in params_list:
                param = param.strip()
                if 'id' in param.lower() or 'key' in param.lower():
                    test_values.append('"test-id-123"')
                elif 'name' in param.lower():
                    test_values.append('"TestName"')
                elif 'email' in param.lower():
                    test_values.append('"test@example.com"')
                elif 'password' in param.lower():
                    test_values.append('"securePassword123"')
                elif 'age' in param.lower() or 'count' in param.lower() or 'num' in param.lower():
                    test_values.append('25')
                elif 'date' in param.lower():
                    test_values.append('new Date("2023-01-01")')
                elif 'bool' in param.lower() or 'flag' in param.lower() or 'is' in param.lower():
                    test_values.append('true')
                elif 'list' in param.lower() or 'array' in param.lower():
                    test_values.append('[1, 2, 3]')
                elif 'obj' in param.lower() or 'options' in param.lower() or 'config' in param.lower():
                    test_values.append('{ key: "value" }')
                else:
                    test_values.append('"testValue"')
            
            # Generate edge case values
            edge_cases = []
            for param in params_list:
                param = param.strip()
                if 'id' in param.lower() or 'key' in param.lower():
                    edge_cases.append('""')
                elif 'name' in param.lower() or 'email' in param.lower() or 'password' in param.lower():
                    edge_cases.append('""')
                elif 'age' in param.lower() or 'count' in param.lower() or 'num' in param.lower():
                    edge_cases.append('0')
                elif 'date' in param.lower():
                    edge_cases.append('null')
                elif 'bool' in param.lower() or 'flag' in param.lower() or 'is' in param.lower():
                    edge_cases.append('false')
                elif 'list' in param.lower() or 'array' in param.lower():
                    edge_cases.append('[]')
                elif 'obj' in param.lower() or 'options' in param.lower() or 'config' in param.lower():
                    edge_cases.append('{}')
                else:
                    edge_cases.append('null')
            
            # Generate assertions based on function body
            assertions = []
            if 'return' in function_body:
                if any(keyword in function_body for keyword in ['sum', 'add', 'total', 'calculate']):
                    assertions.append('expect(typeof result).toBe("number");')
                elif any(keyword in function_body for keyword in ['name', 'email', 'format', 'concat']):
                    assertions.append('expect(typeof result).toBe("string");')
                elif any(keyword in function_body for keyword in ['array', 'list', 'filter', 'map']):
                    assertions.append('expect(Array.isArray(result)).toBe(true);')
                elif any(keyword in function_body for keyword in ['object', 'json', 'data']):
                    assertions.append('expect(typeof result).toBe("object");')
                else:
                    assertions.append('expect(result).toBeDefined();')
            else:
                assertions.append('expect(true).toBe(true); // Function may not return a value')
            
            test_cases = f"""
// Generated test cases for {function_name}
import { {function_name} } from './yourModule'; // Update import path as needed

describe('{function_name} tests', () => {{
  test('should work with basic inputs', () => {{
    // Test with typical values
    const result = {function_name}({', '.join(test_values)});
    {assertions[0]}
  }});
  
  test('should handle edge cases', () => {{
    // Test with edge cases
    const edgeCaseResult = {function_name}({', '.join(edge_cases)});
    expect(edgeCaseResult).not.toBeUndefined();
  }});
  
  test('should handle invalid inputs', () => {{
    // Test with invalid inputs
    {"// " if len(params_list) == 0 else ""}expect(() => {function_name}({', '.join(['undefined' for _ in params_list])})).not.toThrow();
  }});
}});
"""
            return test_cases
        else:
            return """
// Generated test cases
import { functionToTest } from './yourModule'; // Update import path and function name

describe('Code tests', () => {
  test('should test basic functionality', () => {
    // TODO: Replace with actual function calls and assertions
    expect(typeof functionToTest).toBe('function');
  });
  
  test('should handle edge cases', () => {
    // TODO: Add edge case testing
    expect("value").not.toBeNull();
  });
  
  test('should handle errors gracefully', () => {
    // TODO: Test error handling
    expect(() => {
      // Call function with invalid parameters
    }).not.toThrow();
  });
});
"""
    
    elif language == 'python':
        # Extract function names and parameters
        function_matches = re.findall(r'def\s+(\w+)\s*$$([^)]*)$$', code)
        
        if function_matches:
            function_name, params = function_matches[0]
            params_list = [p.strip().split(':')[0].split('=')[0].strip() for p in params.split(',') if p.strip()]
            # Remove 'self' if it's the first parameter
            if params_list and params_list[0] == 'self':
                params_list = params_list[1:]
            
            # Analyze function body to generate better test cases
            function_body = ""
            in_function = False
            indent_level = 0
            
            for line in code.split('\n'):
                if re.search(r'def\s+' + re.escape(function_name) + r'\s*\(', line):
                    in_function = True
                    indent_level = len(line) - len(line.lstrip())
                
                if in_function:
                    if line.strip() and len(line) - len(line.lstrip()) <= indent_level and line.strip()[0] != '#':
                        if not re.search(r'def\s+' + re.escape(function_name) + r'\s*\(', line):
                            break
                    function_body += line + '\n'
            
            # Generate test values based on parameter names and function body
            test_values = []
            for param in params_list:
                param = param.strip()
                if 'id' in param.lower() or 'key' in param.lower():
                    test_values.append('"test-id-123"')
                elif 'name' in param.lower():
                    test_values.append('"TestName"')
                elif 'email' in param.lower():
                    test_values.append('"test@example.com"')
                elif 'password' in param.lower():
                    test_values.append('"securePassword123"')
                elif 'age' in param.lower() or 'count' in param.lower() or 'num' in param.lower():
                    test_values.append('25')
                elif 'date' in param.lower():
                    test_values.append('"2023-01-01"')
                elif 'bool' in param.lower() or 'flag' in param.lower() or 'is' in param.lower():
                    test_values.append('True')
                elif 'list' in param.lower() or 'array' in param.lower():
                    test_values.append('[1, 2, 3]')
                elif 'dict' in param.lower() or 'options' in param.lower() or 'config' in param.lower():
                    test_values.append('{"key": "value"}')
                else:
                    test_values.append('"test_value"')
            
            # Generate edge case values
            edge_cases = []
            for param in params_list:
                param = param.strip()
                if 'id' in param.lower() or 'key' in param.lower():
                    edge_cases.append('""')
                elif 'name' in param.lower() or 'email' in param.lower() or 'password' in param.lower():
                    edge_cases.append('""')
                elif 'age' in param.lower() or 'count' in param.lower() or 'num' in param.lower():
                    edge_cases.append('0')
                elif 'date' in param.lower():
                    edge_cases.append('None')
                elif 'bool' in param.lower() or 'flag' in param.lower() or 'is' in param.lower():
                    edge_cases.append('False')
                elif 'list' in param.lower() or 'array' in param.lower():
                    edge_cases.append('[]')
                elif 'dict' in param.lower() or 'options' in param.lower() or 'config' in param.lower():
                    edge_cases.append('{}')
                else:
                    edge_cases.append('None')
            
            # Generate assertions based on function body
            assertions = []
            if 'return' in function_body:
                if any(keyword in function_body for keyword in ['sum', 'add', 'total', 'calculate']):
                    assertions.append('self.assertIsInstance(result, (int, float))')
                elif any(keyword in function_body for keyword in ['name', 'email', 'format', 'concat']):
                    assertions.append('self.assertIsInstance(result, str)')
                elif any(keyword in function_body for keyword in ['list', 'filter', 'map']):
                    assertions.append('self.assertIsInstance(result, list)')
                elif any(keyword in function_body for keyword in ['dict', 'json', 'data']):
                    assertions.append('self.assertIsInstance(result, dict)')
                else:
                    assertions.append('self.assertIsNotNone(result)')
            else:
                assertions.append('self.assertTrue(True)  # Function may not return a value')
            
            test_cases = f"""
import unittest
from your_module import {function_name}  # Update import path as needed

# Generated test cases for {function_name}
class Test{function_name.capitalize()}(unittest.TestCase):
    def test_basic_functionality(self):
        # Test with typical values
        result = {function_name}({', '.join(test_values)})
        {assertions[0]}
    
    def test_edge_cases(self):
        # Test with edge cases
        edge_case_result = {function_name}({', '.join(edge_cases)})
        self.assertIsNotNone(edge_case_result)
    
    def test_invalid_inputs(self):
        # Test with invalid inputs
        try:
            result = {function_name}({', '.join(['None' for _ in params_list])})
            # If we get here, the function handled None inputs without errors
            self.assertTrue(True)
        except Exception as e:
            # If an exception is expected for None inputs, uncomment the line below
            # self.assertTrue(True)
            # Otherwise, the test should fail
            self.fail(f"Function raised unexpected exception: {{e}}")

if __name__ == '__main__':
    unittest.main()
"""
            return test_cases
        else:
            return """
import unittest
from your_module import function_to_test  # Update import path and function name

# Generated test cases
class TestCode(unittest.TestCase):
    def test_functionality(self):
        # TODO: Replace with actual function calls and assertions
        self.assertTrue(callable(function_to_test))
    
    def test_edge_cases(self):
        # TODO: Add edge case testing
        self.assertIsNotNone("value")
    
    def test_error_handling(self):
        # TODO: Test error handling
        try:
            # Call function with invalid parameters
            pass
        except Exception as e:
            # If an exception is expected, uncomment the line below
            # self.assertTrue(True)
            # Otherwise, the test should fail
            self.fail(f"Function raised unexpected exception: {e}")

if __name__ == '__main__':
    unittest.main()
"""
    
    elif language == 'java':
        # Extract class and method names
        class_match = re.search(r'class\s+(\w+)', code)
        method_matches = re.findall(r'(public|private|protected)\s+(\w+)\s+(\w+)\s*$$([^)]*)$$', code)
        
        class_name = class_match.group(1) if class_match else "TestClass"
        
        if method_matches:
            access, return_type, method_name, params = method_matches[0]
            params_list = [p.strip() for p in params.split(',') if p.strip()]
            param_types = []
            param_names = []
            
            for param in params_list:
                if param:
                    parts = param.split()
                    if len(parts) >= 2:
                        param_types.append(parts[0])
                        param_names.append(parts[1])
            
            # Generate test values based on parameter types and names
            test_values = []
            for i, (param_type, param_name) in enumerate(zip(param_types, param_names)):
                if param_type == 'int' or param_type == 'Integer':
                    test_values.append('42')
                elif param_type == 'double' or param_type == 'Double' or param_type == 'float' or param_type == 'Float':
                    test_values.append('3.14')
                elif param_type == 'boolean' or param_type == 'Boolean':
                    test_values.append('true')
                elif param_type == 'String':
                    if 'name' in param_name.lower():
                        test_values.append('"TestName"')
                    elif 'email' in param_name.lower():
                        test_values.append('"test@example.com"')
                    elif 'id' in param_name.lower() or 'key' in param_name.lower():
                        test_values.append('"test-id-123"')
                    else:
                        test_values.append('"testValue"')
                elif 'List' in param_type:
                    test_values.append('new ArrayList<>()')
                elif 'Map' in param_type:
                    test_values.append('new HashMap<>()')
                else:
                    test_values.append('null')
            
            # Generate assertions based on return type
            assertions = []
            if return_type == 'void':
                assertions.append('// Method returns void, so we just verify it doesn\'t throw an exception')
            elif return_type == 'int' or return_type == 'Integer':
                assertions.append('assertNotNull(result);')
                assertions.append('assertTrue(result instanceof Integer);')
            elif return_type == 'double' or return_type == 'Double' or return_type == 'float' or return_type == 'Float':
                assertions.append('assertNotNull(result);')
                if return_type == 'double' or return_type == 'Double':
                    assertions.append('assertTrue(result instanceof Double);')
                else:
                    assertions.append('assertTrue(result instanceof Float);')
            elif return_type == 'boolean' or return_type == 'Boolean':
                assertions.append('assertNotNull(result);')
                assertions.append('assertTrue(result instanceof Boolean);')
            elif return_type == 'String':
                assertions.append('assertNotNull(result);')
                assertions.append('assertTrue(result instanceof String);')
            elif 'List' in return_type:
                assertions.append('assertNotNull(result);')
                assertions.append('assertTrue(result instanceof List);')
            elif 'Map' in return_type:
                assertions.append('assertNotNull(result);')
                assertions.append('assertTrue(result instanceof Map);')
            else:
                assertions.append('assertNotNull(result);')
            
            test_cases = f"""
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

// Generated test cases for {class_name}.{method_name}
public class {class_name}Test {{
    
    @Test
    public void test{method_name.capitalize()}BasicFunctionality() {{
        // Create an instance of the class
        {class_name} instance = new {class_name}();
        
        // Test with typical values
        {return_type} result = instance.{method_name}({', '.join(test_values)});
        {assertions[0]}
        {assertions[1] if len(assertions) > 1 else ''}
    }}
    
    @Test
    public void test{method_name.capitalize()}EdgeCases() {{
        // Create an instance of the class
        {class_name} instance = new {class_name}();
        
        // Test with edge cases
        {return_type} edgeCaseResult = instance.{method_name}({', '.join(['0' if t == 'int' or t == 'Integer' else '0.0' if t == 'double' or t == 'Double' or t == 'float' or t == 'Float' else 'false' if t == 'boolean' or t == 'Boolean' else '""' if t == 'String' else 'new ArrayList<>()' if 'List' in t else 'new HashMap<>()' if 'Map' in t else 'null' for t in param_types])});
        assertNotNull(edgeCaseResult);
    }}
    
    @Test
    public void test{method_name.capitalize()}ExceptionHandling() {{
        // Create an instance of the class
        {class_name} instance = new {class_name}();
        
        try {{
            // Test with potentially invalid inputs
            {return_type} result = instance.{method_name}({', '.join(['null' for _ in param_types])});
            // If we get here, the method handled null inputs without errors
            assertTrue(true);
        }} catch (Exception e) {{
            // If an exception is expected for null inputs, uncomment the line below
            // assertTrue(true);
            // Otherwise, the test should fail
            fail("Method threw unexpected exception: " + e.getMessage());
        }}
    }}
}}
"""
            return test_cases
        else:
            return """
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

// Generated test cases
public class CodeTest {
    
    @Test
    public void testBasicFunctionality() {
        // TODO: Create an instance of your class and test its methods
        assertTrue(true);
    }
    
    @Test
    public void testEdgeCases() {
        // TODO: Add edge case testing
        assertNotNull("value");
    }
    
    @Test
    public void testExceptionHandling() {
        try {
            // TODO: Test with invalid inputs
            // Call method with invalid parameters
            assertTrue(true);
        } catch (Exception e) {
            // If an exception is expected, uncomment the line below
            // assertTrue(true);
            // Otherwise, the test should fail
            fail("Method threw unexpected exception: " + e.getMessage());
        }
    }
}
"""
    
    else:
        # Generic test case template for other languages
        return f"""
// Basic test structure for {language}
// TODO: Replace with language-specific testing framework

function testFunctionality() {{
  // Test basic functionality
  console.log("Testing basic functionality");
  
  // TODO: Replace with actual function calls and assertions
  const result = functionToTest("test input");
  
  if (result !== undefined) {{
    console.log("✓ Test passed: Function returned a value");
  }} else {{
    console.log("✗ Test failed: Function returned undefined");
  }}
}}

function testEdgeCases() {{
  // Test edge cases
  console.log("Testing edge cases");
  
  // TODO: Replace with actual edge case tests
  try {{
    const result = functionToTest("");
    console.log("✓ Test passed: Function handled empty input");
  }} catch (error) {{
    console.log("✗ Test failed: Function threw error on empty input");
  }}
}}

function testErrorHandling() {{
  // Test error handling
  console.log("Testing error handling");
  
  // TODO: Replace with actual error handling tests
  try {{
    const result = functionToTest(null);
    console.log("✓ Test passed: Function handled null input");
  }} catch (error) {{
    console.log("✗ Test failed: Function threw error on null input");
  }}
}}

// Run tests
testFunctionality();
testEdgeCases();
testErrorHandling();
"""

def fix_code_issues(code, language):
    """Enhanced function to fix common issues in the code based on language."""
    if language == 'javascript':
        # Add missing semicolons
        fixed_code = re.sub(r'([^;{}\s])\s*$', r'\1;', code, flags=re.MULTILINE)
        
        # Replace var with const where appropriate (if the variable is not reassigned)
        var_declarations = re.findall(r'var\s+(\w+)\s*=', fixed_code)
        for var_name in var_declarations:
            # Check if the variable is reassigned
            if not re.search(r'\b' + re.escape(var_name) + r'\s*=', fixed_code[fixed_code.find(f'var {var_name}') + len(f'var {var_name}'):]):
                fixed_code = re.sub(r'\bvar\s+' + re.escape(var_name) + r'\s*=', f'const {var_name} =', fixed_code, count=1)
            else:
                fixed_code = re.sub(r'\bvar\s+' + re.escape(var_name) + r'\s*=', f'let {var_name} =', fixed_code, count=1)
        
        # Add proper spacing around operators
        fixed_code = re.sub(r'(\w+)=(\w+)', r'\1 = \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\+=(\w+)', r'\1 += \2', fixed_code)
        fixed_code = re.sub(r'(\w+)-=(\w+)', r'\1 -= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\*=(\w+)', r'\1 *= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)/=(\w+)', r'\1 /= \2', fixed_code)
        
        # Add proper spacing after commas
        fixed_code = re.sub(r',(\S)', r', \1', fixed_code)
        
        # Add braces to single-line if statements
        fixed_code = re.sub(r'(if\s*$$[^)]*$$)([^{;]*)(?=\n|$)', r'\1 {\2\n}', fixed_code)
        
        # Fix common typos
        fixed_code = fixed_code.replace('lenght', 'length')
        fixed_code = fixed_code.replace('funciton', 'function')
        
        # Add error handling where missing
        if 'try' not in fixed_code and len(fixed_code) > 200:
            # Look for potential error-prone operations
            error_prone_ops = ['fetch(', 'JSON.parse(', 'localStorage.', 'new Promise(']
            for op in error_prone_ops:
                if op in fixed_code:
                    # Find the line with the operation
                    lines = fixed_code.split('\n')
                    for i, line in enumerate(lines):
                        if op in line and 'try' not in line and 'catch' not in line:
                            # Add try-catch block
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * indent
                            lines[i] = f"{indent_str}try {{\n{line}\n{indent_str}}} catch (error) {{\n{indent_str}  console.error('Error:', error);\n{indent_str}}}"
                            fixed_code = '\n'.join(lines)
                            break
                    break
        
        return fixed_code
    
    elif language == 'python':
        lines = code.split('\n')
        fixed_lines = []
        
        # Fix indentation (use 4 spaces)
        for line in lines:
            if re.match(r'^( {1,3}|\t)\w', line):
                indent_level = len(re.match(r'^[ \t]*', line).group(0))
                fixed_line = ' ' * (4 * (indent_level // 4)) + line.lstrip()
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        fixed_code = '\n'.join(fixed_lines)
        
        # Add docstrings if missing
        if not re.match(r'^\s*"""', fixed_code) and re.search(r'\bdef\s+\w+\s*\(', fixed_code):
            function_matches = re.finditer(r'(\s*)(def\s+(\w+)\s*$$[^)]*$$)', fixed_code)
            for match in function_matches:
                indent, func_def, func_name = match.groups()
                if not re.search(r'"""', fixed_code[match.end():match.end() + 100]):
                    docstring = f'{indent}    """\n{indent}    {func_name} function.\n{indent}    \n{indent}    Returns:\n{indent}        Result of the function\n{indent}    """\n'
                    fixed_code = fixed_code.replace(func_def, f'{func_def}:\n{docstring}')
        
        # Add exception handling where missing
        if 'try:' not in fixed_code and len(fixed_code) > 200:
            # Look for potential error-prone operations
            error_prone_ops = ['open(', 'json.loads(', 'requests.', 'subprocess.']
            for op in error_prone_ops:
                if op in fixed_code:
                    # Find the line with the operation
                    lines = fixed_code.split('\n')
                    for i, line in enumerate(lines):
                        if op in line and 'try:' not in line and 'except' not in line:
                            # Add try-except block
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * indent
                            lines[i] = f"{indent_str}try:\n{indent_str}    {line.strip()}\n{indent_str}except Exception as e:\n{indent_str}    print(f\"Error: {e}\")"
                            fixed_code = '\n'.join(lines)
                            break
                    break
        
        # Fix common typos
        fixed_code = fixed_code.replace('lenght', 'length')
        fixed_code = fixed_code.replace('funciton', 'function')
        
        return fixed_code
    
    elif language == 'java':
        # Add missing semicolons
        fixed_code = re.sub(r'([^;{}\s])\s*$', r'\1;', code, flags=re.MULTILINE)
        
        # Add braces to control statements
        fixed_code = re.sub(r'(if|for|while)\s*$$([^)]*)$$([^{]*$)', r'\1 (\2) {\3\n}', fixed_code, flags=re.MULTILINE)
        
        # Add proper spacing around operators
        fixed_code = re.sub(r'(\w+)=(\w+)', r'\1 = \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\+=(\w+)', r'\1 += \2', fixed_code)
        fixed_code = re.sub(r'(\w+)-=(\w+)', r'\1 -= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\*=(\w+)', r'\1 *= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)/=(\w+)', r'\1 /= \2', fixed_code)
        
        # Add proper spacing after commas
        fixed_code = re.sub(r',(\S)', r', \1', fixed_code)
        
        # Add exception handling where missing
        if 'try {' not in fixed_code and len(fixed_code) > 200:
            # Look for potential error-prone operations
            error_prone_ops = ['new FileInputStream', 'new BufferedReader', 'Integer.parseInt', 'Double.parseDouble']
            for op in error_prone_ops:
                if op in fixed_code:
                    # Find the line with the operation
                    lines = fixed_code.split('\n')
                    for i, line in enumerate(lines):
                        if op in line and 'try' not in line and 'catch' not in line:
                            # Add try-catch block
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * indent
                            lines[i] = f"{indent_str}try {{\n{indent_str}    {line.strip()}\n{indent_str}}} catch (Exception e) {{\n{indent_str}    e.printStackTrace();\n{indent_str}}}"
                            fixed_code = '\n'.join(lines)
                            break
                    break
        
        # Fix resource management (add try-with-resources)
        if 'new FileInputStream' in fixed_code and 'try (' not in fixed_code:
            lines = fixed_code.split('\n')
            for i, line in enumerate(lines):
                if 'new FileInputStream' in line and 'try' not in line:
                    # Extract the variable name
                    var_match = re.search(r'(\w+)\s*=\s*new FileInputStream', line)
                    if var_match:
                        var_name = var_match.group(1)
                        indent = len(line) - len(line.lstrip())
                        indent_str = ' ' * indent
                        # Replace with try-with-resources
                        lines[i] = f"{indent_str}try (FileInputStream {var_name} = new FileInputStream{line.split('new FileInputStream')[1]}) {{"
                        # Find the end of the block to add closing brace
                        j = i + 1
                        while j < len(lines) and (j == i + 1 or len(lines[j]) - len(lines[j].lstrip()) > indent):
                            j += 1
                        lines.insert(j, f"{indent_str}}} catch (IOException e) {{\n{indent_str}    e.printStackTrace();\n{indent_str}}}")
                        fixed_code = '\n'.join(lines)
                        break
        
        # Fix common typos
        fixed_code = fixed_code.replace('lenght', 'length')
        fixed_code = fixed_code.replace('funciton', 'function')
        
        return fixed_code
    
    elif language == 'php':
        # Add missing semicolons
        fixed_code = re.sub(r'([^;{}\s])\s*$', r'\1;', code, flags=re.MULTILINE)
        
        # Add proper spacing around operators
        fixed_code = re.sub(r'(\w+)=(\w+)', r'\1 = \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\+=(\w+)', r'\1 += \2', fixed_code)
        fixed_code = re.sub(r'(\w+)-=(\w+)', r'\1 -= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\*=(\w+)', r'\1 *= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)/=(\w+)', r'\1 /= \2', fixed_code)
        
        # Add proper spacing after commas
        fixed_code = re.sub(r',(\S)', r', \1', fixed_code)
        
        # Replace deprecated mysql functions with mysqli
        fixed_code = fixed_code.replace('mysql_connect', 'mysqli_connect')
        fixed_code = fixed_code.replace('mysql_query', 'mysqli_query')
        fixed_code = fixed_code.replace('mysql_fetch_array', 'mysqli_fetch_array')
        fixed_code = fixed_code.replace('mysql_fetch_assoc', 'mysqli_fetch_assoc')
        fixed_code = fixed_code.replace('mysql_num_rows', 'mysqli_num_rows')
        fixed_code = fixed_code.replace('mysql_error', 'mysqli_error')
        
        # Add exception handling where missing
        if 'try {' not in fixed_code and len(fixed_code) > 200:
            # Look for potential error-prone operations
            error_prone_ops = ['file_get_contents', 'json_decode', 'mysqli_query', 'fopen']
            for op in error_prone_ops:
                if op in fixed_code:
                    # Find the line with the operation
                    lines = fixed_code.split('\n')
                    for i, line in enumerate(lines):
                        if op in line and 'try' not in line and 'catch' not in line:
                            # Add try-catch block
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * indent
                            lines[i] = f"{indent_str}try {{\n{indent_str}    {line.strip()}\n{indent_str}}} catch (Exception $e) {{\n{indent_str}    echo 'Error: ' . $e->getMessage();\n{indent_str}}}"
                            fixed_code = '\n'.join(lines)
                            break
                    break
        
        # Fix SQL injection vulnerabilities
        if ('mysqli_query' in fixed_code or 'mysql_query' in fixed_code) and 'prepare' not in fixed_code:
            # Find SQL queries with string concatenation
            query_pattern = r'(\$\w+)\s*=\s*["\']SELECT|UPDATE|INSERT|DELETE.*\$\w+'
            matches = re.finditer(query_pattern, fixed_code, re.IGNORECASE)
            for match in matches:
                var_name = match.group(1)
                # Find the line with the query execution
                lines = fixed_code.split('\n')
                for i, line in enumerate(lines):
                    if f'mysqli_query' in line and var_name in line:
                        # Extract connection variable
                        conn_match = re.search(r'mysqli_query\s*\(\s*(\$\w+)', line)
                        if conn_match:
                            conn_var = conn_match.group(1)
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * indent
                            # Replace with prepared statement
                            query_line = next((l for l in lines[:i] if var_name in l and '=' in l), None)
                            if query_line:
                                # Extract the query
                                query_match = re.search(r'=\s*["\'](.+)["\']', query_line)
                                if query_match:
                                    query = query_match.group(1)
                                    # Replace with prepared statement
                                    param_vars = re.findall(r'\$(\w+)', query)
                                    query = re.sub(r'\$\w+', '?', query)
                                    lines[lines.index(query_line)] = f"{indent_str}{var_name} = \"{query}\";"
                                    # Add prepared statement code
                                    prepared_code = [
                                        f"{indent_str}$stmt = {conn_var}->prepare({var_name});",
                                        f"{indent_str}$stmt->bind_param(\"{'s' * len(param_vars)}\", {', '.join(['$' + p for p in param_vars])});"
                                    ]
                                    lines[i] = f"{indent_str}$stmt->execute();"
                                    lines[i+1:i+1] = prepared_code
                                    fixed_code = '\n'.join(lines)
                                    break
        
        return fixed_code
    
    elif language == 'cpp':
        # Add missing semicolons
        fixed_code = re.sub(r'([^;{}\s])\s*$', r'\1;', code, flags=re.MULTILINE)
        
        # Add proper spacing around operators
        fixed_code = re.sub(r'(\w+)=(\w+)', r'\1 = \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\+=(\w+)', r'\1 += \2', fixed_code)
        fixed_code = re.sub(r'(\w+)-=(\w+)', r'\1 -= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\*=(\w+)', r'\1 *= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)/=(\w+)', r'\1 /= \2', fixed_code)
        
        # Add proper spacing after commas
        fixed_code = re.sub(r',(\S)', r', \1', fixed_code)
        
        # Fix memory management issues (replace raw pointers with smart pointers)
        if 'new ' in fixed_code and ('unique_ptr' not in fixed_code and 'shared_ptr' not in fixed_code):
            # Add include for smart pointers if not present
            if '#include <memory>' not in fixed_code:
                fixed_code = '#include <memory>\n' + fixed_code
            
            # Replace raw pointers with smart pointers
            lines = fixed_code.split('\n')
            for i, line in enumerate(lines):
                if 'new ' in line and '*' in line:
                    # Extract the type and variable name
                    ptr_match = re.search(r'(\w+)\s*\*\s*(\w+)\s*=\s*new\s+(\w+)', line)
                    if ptr_match:
                        type_name, var_name, new_type = ptr_match.groups()
                        # Replace with unique_ptr
                        lines[i] = line.replace(f'{type_name} *{var_name} = new {new_type}', 
                                              f'std::unique_ptr<{type_name}> {var_name} = std::make_unique<{new_type}>')
            
            # Remove delete statements for variables that were converted to smart pointers
            for i, line in enumerate(lines):
                if 'delete ' in line:
                    delete_match = re.search(r'delete\s+(\w+)', line)
                    if delete_match:
                        var_name = delete_match.group(1)
                        # Check if this variable was converted to a smart pointer
                        for j, other_line in enumerate(lines):
                            if f'unique_ptr<' in other_line and f'> {var_name} =' in other_line:
                                lines[i] = '// ' + line + ' // Automatic cleanup with smart pointer'
                                break
            
            fixed_code = '\n'.join(lines)
        
        # Add exception handling where missing
        if 'try {' not in fixed_code and len(fixed_code) > 200:
            # Look for potential error-prone operations
            error_prone_ops = ['new ', 'open(', 'std::stoi', 'std::stod']
            for op in error_prone_ops:
                if op in fixed_code:
                    # Find the line with the operation
                    lines = fixed_code.split('\n')
                    for i, line in enumerate(lines):
                        if op in line and 'try' not in line and 'catch' not in line:
                            # Add try-catch block
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * indent
                            lines[i] = f"{indent_str}try {{\n{indent_str}    {line.strip()}\n{indent_str}}} catch (const std::exception& e) {{\n{indent_str}    std::cerr << \"Error: \" << e.what() << std::endl;\n{indent_str}}}"
                            fixed_code = '\n'.join(lines)
                            break
                    break
        
        return fixed_code
    
    elif language == 'csharp':
        # Add missing semicolons
        fixed_code = re.sub(r'([^;{}\s])\s*$', r'\1;', code, flags=re.MULTILINE)
        
        # Add proper spacing around operators
        fixed_code = re.sub(r'(\w+)=(\w+)', r'\1 = \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\+=(\w+)', r'\1 += \2', fixed_code)
        fixed_code = re.sub(r'(\w+)-=(\w+)', r'\1 -= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)\*=(\w+)', r'\1 *= \2', fixed_code)
        fixed_code = re.sub(r'(\w+)/=(\w+)', r'\1 /= \2', fixed_code)
        
        # Add proper spacing after commas
        fixed_code = re.sub(r',(\S)', r', \1', fixed_code)
        
        # Fix resource management (add using statements)
        if ('StreamReader' in fixed_code or 'StreamWriter' in fixed_code or 'FileStream' in fixed_code) and 'using (' not in fixed_code:
            lines = fixed_code.split('\n')
            for i, line in enumerate(lines):
                if ('StreamReader' in line or 'StreamWriter' in line or 'FileStream' in line) and 'new ' in line and 'using' not in line:
                    # Extract the variable name
                    var_match = re.search(r'(\w+)\s*=\s*new', line)
                    if var_match:
                        var_name = var_match.group(1)
                        indent = len(line) - len(line.lstrip())
                        indent_str = ' ' * indent
                        # Replace with using statement
                        lines[i] = f"{indent_str}using ({line.strip()})"
                        # Check if there's already a block
                        if i + 1 < len(lines) and '{' not in lines[i + 1]:
                            lines.insert(i + 1, f"{indent_str}{{")
                            # Find where to close the block
                            j = i + 2
                            while j < len(lines) and var_name in lines[j]:
                                j += 1
                            lines.insert(j, f"{indent_str}}}")
                        fixed_code = '\n'.join(lines)
                        break
        
        # Add exception handling where missing
        if 'try {' not in fixed_code and 'try\n' not in fixed_code and len(fixed_code) > 200:
            # Look for potential error-prone operations
            error_prone_ops = ['File.', 'Convert.', 'Parse', 'new StreamReader', 'new StreamWriter']
            for op in error_prone_ops:
                if op in fixed_code:
                    # Find the line with the operation
                    lines = fixed_code.split('\n')
                    for i, line in enumerate(lines):
                        if op in line and 'try' not in line and 'catch' not in line:
                            # Add try-catch block
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * indent
                            lines[i] = f"{indent_str}try\n{indent_str}{{\n{indent_str}    {line.strip()}\n{indent_str}}}\n{indent_str}catch (Exception ex)\n{indent_str}{{\n{indent_str}    Console.WriteLine($\"Error: {{ex.Message}}\");\n{indent_str}}}"
                            fixed_code = '\n'.join(lines)
                            break
                    break
        
        return fixed_code
    
    else:
        # For unsupported languages, return the original code
        return code

def run_code_analysis_in_thread(code, language, result_queue):
    """Run code analysis in a separate thread to avoid blocking."""
    try:
        if language == 'javascript':
            result = analyze_javascript(code)
        elif language == 'python':
            result = analyze_python(code)
        elif language == 'java':
            result = analyze_java(code)
        elif language == 'php':
            result = analyze_php(code)
        elif language == 'cpp':
            result = analyze_cpp(code)
        elif language == 'csharp':
            result = analyze_csharp(code)
        else:
            result = {"error": "Unsupported Language"}
        
        result_queue.put(result)
    except Exception as e:
        logger.error(f"Error in analysis thread: {traceback.format_exc()}")
        result_queue.put({"error": str(e)})

@app.route('/api/signup', methods=['POST'])
def signup():
    """Endpoint for user registration."""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    password_hash = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (username, email, password_hash)
        )

        user_id = cur.fetchone()[0]
        cur.close()
        conn.close()

        return jsonify({"message": "User created successfully", "userId": user_id}), 201

    except psycopg2.IntegrityError as e:
        return jsonify({"error": "Username or email already exists"}), 400
    except Exception as e:
        logger.error(f"Error in signup: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint for user authentication."""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            return jsonify({"message": "Login successful", "userId": user['id']}), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        logger.error(f"Error in login: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Endpoint to reset user password."""
    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')

    if not email or not new_password:
        return jsonify({"error": "Email and new password are required"}), 400

    password_hash = generate_password_hash(new_password)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash, email)
        )

        if cur.rowcount == 0:
            return jsonify({"error": "Email not found"}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        logger.error(f"Error in forgot_password: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-code', methods=['POST'])
def analyze_code_endpoint():
    """Enhanced endpoint to analyze code and provide insights in real-time."""
    try:
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'javascript')
        user_id = data.get('userId')
        
        # Create a queue for thread communication
        result_queue = queue.Queue()
        
        # Start analysis in a separate thread to avoid blocking
        analysis_thread = threading.Thread(
            target=run_code_analysis_in_thread,
            args=(code, language, result_queue)
        )
        analysis_thread.start()
        
        # Wait for the analysis to complete with a timeout
        analysis_thread.join(timeout=10)
        
        if analysis_thread.is_alive():
            # Analysis is taking too long, return a partial result
            return jsonify({
                "warning": "Analysis is taking longer than expected. Returning partial results.",
                "partial_result": True,
                "complexity": 5,
                "quality": 5,
                "issues": [{"type": "performance", "message": "Code analysis timeout - try with a smaller code sample"}],
                "summary": "Analysis timeout. Try with a smaller code sample."
            })
        
        # Get the result from the queue
        result = result_queue.get()
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        # Round floating point values for better display
        def round_floats(obj):
            if isinstance(obj, float):
                return round(obj, 2)
            if isinstance(obj, dict):
                return {k: round_floats(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [round_floats(element) for element in obj]
            return obj
        
        rounded_result = round_floats(result)
        
        # Save analysis to database if user is logged in
        if user_id:
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                
                cur.execute(
                    "INSERT INTO analyses (user_id, language, code, result) VALUES (%s, %s, %s, %s) RETURNING id",
                    (user_id, language, code, json.dumps(rounded_result))
                )
                
                analysis_id = cur.fetchone()[0]
                cur.close()
                conn.close()
                
                rounded_result['id'] = analysis_id
            except Exception as e:
                logger.error(f"Error Saving Analysis: {e}")
        
        return jsonify(rounded_result)
    
    except Exception as e:
        logger.error(f"Error in analyze_code_endpoint: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-test-cases', methods=['POST'])
def generate_test_cases_endpoint():
    """Enhanced endpoint to generate test cases for code."""
    try:
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'javascript')
        
        # Generate test cases based on language and code
        test_cases = generate_test_cases(code, language)
        
        return jsonify({
            "testCases": test_cases,
            "message": "Test cases generated successfully"
        })
    
    except Exception as e:
        logger.error(f"Error in generate_test_cases_endpoint: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fix-issues', methods=['POST'])
def fix_issues_endpoint():
    """Enhanced endpoint to fix common issues in code."""
    try:
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'javascript')
        
        fixed_code = fix_code_issues(code, language)
        
        # Calculate improvement metrics
        original_lines = len(code.split('\n'))
        fixed_lines = len(fixed_code.split('\n'))
        changes = abs(fixed_lines - original_lines)
        
        # Identify specific improvements made
        improvements = []
        
        if language == 'javascript':
            if 'var ' in code and 'var ' not in fixed_code:
                improvements.append("Replaced 'var' with 'const' or 'let'")
            if code.count(';') < fixed_code.count(';'):
                improvements.append(f"Added {fixed_code.count(';') - code.count(';')} missing semicolons")
            if 'try {' in fixed_code and 'try {' not in code:
                improvements.append("Added error handling with try/catch blocks")
        
        elif language == 'python':
            if '"""' in fixed_code and '"""' not in code:
                improvements.append("Added missing docstrings")
            if 'try:' in fixed_code and 'try:' not in code:
                improvements.append("Added exception handling with try/except blocks")
        
        elif language == 'java' or language == 'csharp':
            if code.count(';') < fixed_code.count(';'):
                improvements.append(f"Added {fixed_code.count(';') - code.count(';')} missing semicolons")
            if ('try {' in fixed_code and 'try {' not in code) or ('try\n' in fixed_code and 'try\n' not in code):
                improvements.append("Added exception handling with try/catch blocks")
            if 'using (' in fixed_code and 'using (' not in code:
                improvements.append("Improved resource management with using statements")
        
        elif language == 'cpp':
            if 'unique_ptr' in fixed_code and 'unique_ptr' not in code:
                improvements.append("Replaced raw pointers with smart pointers")
            if code.count(';') < fixed_code.count(';'):
                improvements.append(f"Added {fixed_code.count(';') - code.count(';')} missing semicolons")
        
        elif language == 'php':
            if 'mysqli_' in fixed_code and 'mysql_' in code:
                improvements.append("Replaced deprecated mysql_ functions with mysqli_")
            if 'prepare' in fixed_code and 'prepare' not in code:
                improvements.append("Added SQL injection protection with prepared statements")
        
        if not improvements:
            improvements.append("Applied general code formatting and style improvements")
        
        return jsonify({
            "modifiedCode": fixed_code,
            "improvements": improvements,
            "changedLines": changes,
            "message": "Code issues fixed successfully"
        })
    
    except Exception as e:
        logger.error(f"Error in fix_issues_endpoint: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/execute', methods=['POST'])
def execute_code():
    """Endpoint to execute code using the Piston API."""
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'javascript')
    
    start_time = time.time()
    
    if os.environ.get('MOCK_EXECUTION') == 'true':
        time.sleep(1.5)
        
        mock_outputs = {
            'javascript': "Console output mock",
            'python': "Print output mock",
            'java': "System.out output mock",
            'php': "echo output mock",
            'cpp': "cout output mock",
            'csharp': "Console.WriteLine output mock"
        }
        
        output = mock_outputs.get(language, "Mock execution output")
        error = None
        if random.random() < 0.2:
            error = f"Mock {language} runtime error"
        
        return jsonify({
            "output": output,
            "error": error,
            "executionTime": round((time.time() - start_time) * 1000, 2)
        })
    
    try:
        lang_config = PISTON_LANGUAGES.get(language)
        if not lang_config:
            return jsonify({"error": "Unsupported language"}), 400
        
        payload = {
            "language": lang_config['language'],
            "version": lang_config['version'],
            "files": [{"content": code}]
        }
        
        response = requests.post(PISTON_API_URL, json=payload)
        
        if response.status_code != 200:
            return jsonify({
                "output": "",
                "error": f"Execution API error: {response.text}",
                "executionTime": 0
            }), 500
        
        result = response.json()
        execution_time = (time.time() - start_time) * 1000
        
        run_output = result.get('run', {}).get('output', '')
        compile_error = result.get('compile', {}).get('stderr', '')
        runtime_error = result.get('run', {}).get('stderr', '')
        
        output = run_output.strip()
        error = (compile_error or runtime_error).strip() or None
        
        return jsonify({
            "output": output,
            "error": error,
            "executionTime": round(execution_time, 2)
        })
        
    except Exception as e:
        logger.error(f"Error in execute_code: {traceback.format_exc()}")
        return jsonify({
            "output": "",
            "error": f"Error executing code: {str(e)}",
            "executionTime": 0
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Endpoint to retrieve user's code analysis history."""
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            "SELECT id, language, code, result, created_at FROM analyses "
            "WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        
        analyses = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(analyses)
    except Exception as e:
        logger.error(f"Error in get_history: {traceback.format_exc()}")
        return jsonify({
            "error": f"Error fetching history: {str(e)}"
        }), 500

@app.route('/api/enhance-code', methods=['POST'])
def enhance_code_endpoint():
    """Endpoint to enhance code with better practices and optimizations."""
    try:
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'javascript')
        
        # First fix any issues
        fixed_code = fix_code_issues(code, language)
        
        # Then apply additional enhancements based on language
        if language == 'javascript':
            # Add modern ES6+ features
            enhanced_code = fixed_code
            
            # Replace traditional functions with arrow functions where appropriate
            if 'function(' in enhanced_code:
                enhanced_code = re.sub(r'function\s*$$([^)]*)$$\s*{([^}]*return\s+[^;]*;)\s*}', 
                                      r'(\1) => \2', enhanced_code)
            
            # Replace string concatenation with template literals
            enhanced_code = re.sub(r'([\'"])\s*\+\s*(\w+)\s*\+\s*([\'"])', r'`${' + r'\2' + r'}`', enhanced_code)
            
            # Add async/await for promises
            if '.then(' in enhanced_code and 'async' not in enhanced_code:
                # Find functions with promises
                lines = enhanced_code.split('\n')
                for i, line in enumerate(lines):
                    if '.then(' in line and 'function' in lines[i-1]:
                        # Add async to the function
                        lines[i-1] = lines[i-1].replace('function', 'async function')
                        # Find the promise chain
                        j = i
                        chain_start = j
                        while j < len(lines) and ('.then(' in lines[j] or '.catch(' in lines[j]):
                            j += 1
                        chain_end = j
                        
                        # Extract the promise chain
                        promise_chain = '\n'.join(lines[chain_start:chain_end])
                        # Extract the initial promise
                        promise_match = re.search(r'(\w+$$[^)]*$$)', lines[chain_start])
                        if promise_match:
                            promise_call = promise_match.group(1)
                            # Replace with await
                            await_code = f"try {{\n  const result = await {promise_call};\n  // Handle result\n}} catch (error) {{\n  // Handle error\n}}"
                            lines[chain_start:chain_end] = [await_code]
                
                enhanced_code = '\n'.join(lines)
            
        elif language == 'python':
            # Add type hints
            enhanced_code = fixed_code
            
            # Add type hints to function parameters and return values
            function_matches = re.finditer(r'def\s+(\w+)\s*$$([^)]*)$$:', enhanced_code)
            for match in function_matches:
                func_name, params = match.groups()
                if ':' not in params and '-> ' not in enhanced_code[match.end():match.end() + 10]:
                    # Add type hints to parameters
                    typed_params = []
                    for param in params.split(','):
                        param = param.strip()
                        if param:
                            if 'self' in param:
                                typed_params.append(param)
                            elif 'id' in param or 'index' in param or 'count' in param:
                                typed_params.append(f"{param}: int")
                            elif 'name' in param or 'text' in param or 'str' in param:
                                typed_params.append(f"{param}: str")
                            elif 'list' in param or 'array' in param:
                                typed_params.append(f"{param}: list")
                            elif 'dict' in param or 'map' in param:
                                typed_params.append(f"{param}: dict")
                            elif 'bool' in param or 'flag' in param:
                                typed_params.append(f"{param}: bool")
                            else:
                                typed_params.append(f"{param}: Any")
                    
                    # Add return type hint
                    return_type = " -> Any"
                    
                    # Replace the function definition
                    old_def = f"def {func_name}({params}):"
                    new_def = f"def {func_name}({', '.join(typed_params)}){return_type}:"
                    enhanced_code = enhanced_code.replace(old_def, new_def)
            
            # Add typing import if type hints were added
            if ': int' in enhanced_code or ': str' in enhanced_code or ': list' in enhanced_code or ': Any' in enhanced_code:
                if 'from typing import' not in enhanced_code:
                    enhanced_code = 'from typing import Any, List, Dict, Optional, Union\n\n' + enhanced_code
            
            # Use f-strings instead of .format() or %
            enhanced_code = re.sub(r'"%$$(\w+)$$s"', r'f"{\1}"', enhanced_code)
            enhanced_code = re.sub(r'"{0}".format$$(\w+)$$', r'f"{\1}"', enhanced_code)
            
        elif language == 'java':
            # Add modern Java features
            enhanced_code = fixed_code
            
            # Replace explicit types with var where appropriate (Java 10+)
            enhanced_code = re.sub(r'(\w+)<\w+>\s+(\w+)\s*=\s*new\s+\w+<>', r'var \2 = new \1<>', enhanced_code)
            
            # Add stream operations for collections
            if 'for (' in enhanced_code and ('List' in enhanced_code or 'ArrayList' in enhanced_code):
                # Find for loops that iterate over collections
                for_loop_pattern = r'for\s*$$\s*\w+\s+(\w+)\s*:\s*(\w+)\s*$$\s*{'
                for_loops = re.finditer(for_loop_pattern, enhanced_code)
                for match in for_loops:
                    var_name, collection_name = match.groups()
                    # Check if the loop is doing filtering or mapping
                    loop_start = match.end()
                    # Find the end of the loop
                    brace_count = 1
                    loop_end = loop_start
                    while brace_count > 0 and loop_end < len(enhanced_code):
                        if enhanced_code[loop_end] == '{':
                            brace_count += 1
                        elif enhanced_code[loop_end] == '}':
                            brace_count -= 1
                        loop_end += 1
                    
                    loop_body = enhanced_code[loop_start:loop_end-1]
                    
                    # Check if it's a filter operation
                    if 'if (' in loop_body and 'continue' in loop_body:
                        # Replace with stream filter
                        stream_code = f"{collection_name}.stream()\n    .filter(item -> /* Add filter condition */)\n    .collect(Collectors.toList());"
                        enhanced_code = enhanced_code[:match.start()] + "// Using streams instead of for loop\n" + stream_code + enhanced_code[loop_end:]
                        break
            
        elif language == 'csharp':
            # Add modern C# features
            enhanced_code = fixed_code
            
            # Replace explicit types with var where appropriate
            enhanced_code = re.sub(r'(\w+)\s+(\w+)\s*=\s*new\s+\w+\(', r'var \2 = new \1(', enhanced_code)
            
            # Add LINQ for collections
            if 'foreach' in enhanced_code and ('List<' in enhanced_code or 'IEnumerable<' in enhanced_code):
                # Find foreach loops
                foreach_pattern = r'foreach\s*$$\s*\w+\s+(\w+)\s+in\s+(\w+)\s*$$\s*{'
                foreach_loops = re.finditer(foreach_pattern, enhanced_code)
                for match in for_loops:
                    var_name, collection_name = match.groups()
                    # Check if the loop is doing filtering or mapping
                    loop_start = match.end()
                    # Find the end of the loop
                    brace_count = 1
                    loop_end = loop_start
                    while brace_count > 0 and loop_end < len(enhanced_code):
                        if enhanced_code[loop_end] == '{':
                            brace_count += 1
                        elif enhanced_code[loop_end] == '}':
                            brace_count -= 1
                        loop_end += 1
                    
                    loop_body = enhanced_code[loop_start:loop_end-1]
                    
                    # Check if it's a filter operation
                    if 'if (' in loop_body and 'continue' in loop_body:
                        # Replace with LINQ
                        linq_code = f"var filtered{collection_name} = {collection_name}.Where(item => /* Add filter condition */);"
                        enhanced_code = enhanced_code[:match.start()] + "// Using LINQ instead of foreach loop\n" + linq_code + enhanced_code[loop_end:]
                        break
        
        else:
            # For other languages, just use the fixed code
            enhanced_code = fixed_code
        
        # Calculate improvement metrics
        original_lines = len(code.split('\n'))
        enhanced_lines = len(enhanced_code.split('\n'))
        changes = abs(enhanced_lines - original_lines)
        
        # Identify specific improvements made
        improvements = []
        
        if language == 'javascript':
            if 'async' in enhanced_code and 'async' not in code:
                improvements.append("Added async/await for better promise handling")
            if '`${' in enhanced_code and '`${' not in code:
                improvements.append("Replaced string concatenation with template literals")
            if '=>' in enhanced_code and '=>' not in code:
                improvements.append("Replaced traditional functions with arrow functions")
        
        elif language == 'python':
            if ': int' in enhanced_code or ': str' in enhanced_code:
                improvements.append("Added type hints for better code documentation")
            if 'f"' in enhanced_code and 'f"' not in code:
                improvements.append("Replaced string formatting with f-strings")
        
        elif language == 'java':
            if 'var ' in enhanced_code and 'var ' not in code:
                improvements.append("Used 'var' for local variable type inference")
            if '.stream()' in enhanced_code and '.stream()' not in code:
                improvements.append("Added stream operations for collection processing")
        
        elif language == 'csharp':
            if 'var ' in enhanced_code and 'var ' not in code:
                improvements.append("Used 'var' for implicit typing")
            if '.Where(' in enhanced_code and '.Where(' not in code:
                improvements.append("Added LINQ for collection processing")
        
        if not improvements:
            improvements.append("Applied general code enhancements and optimizations")
        
        return jsonify({
            "enhancedCode": enhanced_code,
            "improvements": improvements,
            "changedLines": changes,
            "message": "Code enhanced successfully"
        })
    
    except Exception as e:
        logger.error(f"Error in enhance_code_endpoint: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', 
            port=int(os.environ.get('PORT', 5000)))