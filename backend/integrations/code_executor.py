"""
Code Execution Engine for SMARTII
Safely executes Python code for calculations and data analysis
"""

import logging
import sys
import io
import contextlib
from typing import Dict, Any, Optional
import ast
import math
import statistics
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Safe Python code execution engine"""
    
    def __init__(self):
        self.safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bin': bin,
            'bool': bool,
            'chr': chr,
            'dict': dict,
            'divmod': divmod,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'format': format,
            'hex': hex,
            'int': int,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'oct': oct,
            'ord': ord,
            'pow': pow,
            'range': range,
            'reversed': reversed,
            'round': round,
            'set': set,
            'slice': slice,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
            # Math functions
            'math': math,
            'statistics': statistics,
            # Date/time
            'datetime': datetime,
            'timedelta': timedelta,
        }
        
    def execute_python(self, code: str, timeout: int = 5) -> Dict[str, Any]:
        """
        Execute Python code safely
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with success, output, and error
        """
        try:
            logger.info(f"Executing Python code: {code[:100]}...")
            
            # Check for dangerous imports/operations
            if not self._is_safe_code(code):
                return {
                    "success": False,
                    "output": "",
                    "error": "Code contains unsafe operations. Only math, calculations, and data analysis are allowed."
                }
            
            # Capture stdout
            output_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer):
                # Create safe namespace
                namespace = {
                    '__builtins__': self.safe_builtins,
                    'print': print,
                }
                
                try:
                    # Execute code
                    exec(code, namespace)
                    
                    # Get output
                    output = output_buffer.getvalue()
                    
                    # If no output, try to get last expression value
                    if not output:
                        try:
                            result = eval(code, namespace)
                            if result is not None:
                                output = str(result)
                        except:
                            pass
                    
                    return {
                        "success": True,
                        "output": output.strip() if output else "Code executed successfully (no output)",
                        "error": None
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "output": output_buffer.getvalue(),
                        "error": f"Execution error: {str(e)}"
                    }
                    
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "success": False,
                "output": "",
                "error": f"Failed to execute code: {str(e)}"
            }
    
    def _is_safe_code(self, code: str) -> bool:
        """Check if code is safe to execute"""
        try:
            # Parse code into AST
            tree = ast.parse(code)
            
            # Check for dangerous operations
            # Note: ast.Exec doesn't exist in Python 3.x, removed that check
            dangerous_nodes = (ast.Import, ast.ImportFrom, ast.Global)
            
            for node in ast.walk(tree):
                # Block dangerous imports
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Allow only safe imports
                    if isinstance(node, ast.ImportFrom):
                        if node.module not in ['math', 'statistics', 'datetime']:
                            return False
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name not in ['math', 'statistics', 'datetime']:
                                return False
                
                # Block file operations
                if isinstance(node, ast.Name):
                    if node.id in ['open', 'file', 'eval', 'exec', '__import__', 'compile']:
                        return False
            
            return True
            
        except SyntaxError:
            return False
        except Exception as e:
            logger.error(f"Code safety check error: {e}")
            return False
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Evaluate mathematical expression
        
        Args:
            expression: Math expression to calculate
            
        Returns:
            Dictionary with result
        """
        try:
            logger.info(f"Calculating: {expression}")
            
            # Clean expression
            expression = expression.strip()
            
            # Create safe namespace with math functions
            namespace = {
                '__builtins__': {},
                'abs': abs,
                'pow': pow,
                'round': round,
                'sum': sum,
                'min': min,
                'max': max,
                # Math module functions
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'log10': math.log10,
                'exp': math.exp,
                'pi': math.pi,
                'e': math.e,
            }
            
            # Evaluate expression
            result = eval(expression, namespace)
            
            return {
                "success": True,
                "result": result,
                "formatted": f"{expression} = {result}",
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            return {
                "success": False,
                "result": None,
                "formatted": "",
                "error": f"Calculation error: {str(e)}"
            }
    
    def analyze_data(self, data: list, operation: str = "stats") -> Dict[str, Any]:
        """
        Perform data analysis
        
        Args:
            data: List of numbers
            operation: Type of analysis (stats, sum, average, etc.)
            
        Returns:
            Analysis results
        """
        try:
            logger.info(f"Analyzing data: {operation}")
            
            if not data or not all(isinstance(x, (int, float)) for x in data):
                return {
                    "success": False,
                    "error": "Invalid data: must be a list of numbers"
                }
            
            results = {}
            
            if operation == "stats" or operation == "all":
                results.update({
                    "count": len(data),
                    "sum": sum(data),
                    "mean": statistics.mean(data),
                    "median": statistics.median(data),
                    "mode": statistics.mode(data) if len(data) > 1 else data[0],
                    "min": min(data),
                    "max": max(data),
                    "range": max(data) - min(data),
                })
                
                if len(data) > 1:
                    results["stdev"] = statistics.stdev(data)
                    results["variance"] = statistics.variance(data)
            
            elif operation == "sum":
                results["sum"] = sum(data)
            
            elif operation == "average" or operation == "mean":
                results["average"] = statistics.mean(data)
            
            elif operation == "median":
                results["median"] = statistics.median(data)
            
            elif operation == "min":
                results["min"] = min(data)
            
            elif operation == "max":
                results["max"] = max(data)
            
            return {
                "success": True,
                "results": results,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Data analysis error: {e}")
            return {
                "success": False,
                "error": f"Analysis error: {str(e)}"
            }


# Global instance
_code_executor = None


def get_code_executor() -> CodeExecutor:
    """Get or create global code executor instance"""
    global _code_executor
    if _code_executor is None:
        _code_executor = CodeExecutor()
    return _code_executor
