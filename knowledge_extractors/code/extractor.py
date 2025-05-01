from typing import Dict, Any, Union, List
from ..base.extractor import BaseExtractor
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.token import Token
import os

class CodeExtractor(BaseExtractor):
    """Extractor for source code files"""
    
    def __init__(self):
        pass
    def _get_lexer(self, code: str):
        """Get appropriate lexer for the code"""
        # Try to guess the language from the code content
        try:
            lexer = guess_lexer(code)
        except Exception as e:
            # If guessing fails, try to get lexer from file extension
            try:
                if isinstance(code, str):
                    extension = os.path.splitext(code)[1].lower()
                    if extension:
                        lexer = get_lexer_by_name(extension[1:])
            except Exception as e:
                # If all else fails, use a basic text lexer
                lexer = get_lexer_by_name('text')
                print(f"Warning: Could not determine lexer: {str(e)}")
        return lexer
    
    def extract(self, code_source: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extract information from source code
        :param code_source: Can be file path (str) or bytes
        :return: Dictionary containing extracted information
        """
        try:
            if isinstance(code_source, bytes):
                code = code_source.decode('utf-8')
            else:
                with open(code_source, 'r', encoding='utf-8') as f:
                    code = f.read()
            
            # Get lexer
            lexer = self._get_lexer(code)
            
            # Process tokens in a single pass
            comments = []
            function_names = []
            imports = []
            docstrings = []
            
            # Convert generator to list to prevent exhaustion
            tokens = list(lexer.get_tokens(code))
            
            # Process tokens
            for token_type, value in tokens:
                if token_type in Token.Comment:
                    comments.append(value.strip())
                elif token_type in Token.Name.Function:
                    function_names.append(value)
                elif token_type in Token.Name.Namespace:
                    imports.append(value)
                elif token_type in Token.String.Doc:
                    docstrings.append(value.strip())
            
            return {
                # "content": code,
                # "metadata": {
                    "language": lexer.name,
                    "tokens": len(tokens),
                    "lines": len(code.split('\n')),
                    "functions": function_names,
                    "imports": imports,
                    "comments": comments,
                    "docstrings": docstrings,
                    "code_complexity": self._calculate_complexity(tokens, code)
                # }
            }
        except SyntaxError as e:
            return {"error": f"Syntax error: {str(e)}"}
        except Exception as e:
            return {"error": f"Failed to extract code: {str(e)}"}
    
    def _calculate_complexity(self, tokens: List[tuple[Token, str]], code: str) -> Dict[str, Any]:
        """Calculate code complexity metrics using lexer"""
        try:
            # Initialize counters
            metrics = {
                "if_statements": 0,
                "loops": 0,
                "functions": 0,
                "classes": 0,
                "parameters": 0,
                "comments": 0,
                "docstrings": 0,
                "max_line_length": 0,
                "cyclomatic_complexity": 1,  # Start with 1 for base complexity
                "nesting_depth": 0,
                "current_depth": 0
            }
            
            # Process tokens
            for token_type, value in tokens:
                if token_type in Token.Comment:
                    metrics["comments"] += 1
                elif token_type in Token.String.Doc:
                    metrics["docstrings"] += 1
                elif token_type in Token.Keyword and value.lower() in ['if', 'elif', 'else']:
                    metrics["if_statements"] += 1
                    metrics["cyclomatic_complexity"] += 1
                elif token_type in Token.Keyword and value.lower() in ['for', 'while', 'do']:
                    metrics["loops"] += 1
                    metrics["cyclomatic_complexity"] += 1
                elif token_type in Token.Name.Function:
                    metrics["functions"] += 1
                elif token_type in Token.Name.Class:
                    metrics["classes"] += 1
                elif token_type in Token.Punctuation and value == '(':
                    metrics["parameters"] += 1
                
                # Track nesting depth
                if token_type in Token.Punctuation and value in ['{', '(']:
                    metrics["current_depth"] += 1
                    metrics["nesting_depth"] = max(metrics["nesting_depth"], metrics["current_depth"])
                elif token_type in Token.Punctuation and value in ['}', ')']:
                    metrics["current_depth"] = max(0, metrics["current_depth"] - 1)
            
            # Calculate additional metrics
            lines = code.split('\n')
            metrics["max_line_length"] = max(len(line) for line in lines)
            metrics["lines_of_code"] = len([line for line in lines if line.strip()])
            metrics["comment_ratio"] = metrics["comments"] / metrics["lines_of_code"] if metrics["lines_of_code"] else 0
            
            # Calculate overall complexity score
            metrics["total_complexity"] = (
                metrics["cyclomatic_complexity"] * 2 +
                metrics["nesting_depth"] * 1.5 +
                metrics["parameters"] / 2 +
                metrics["lines_of_code"] / 10
            )
            
            return metrics
        except Exception as e:
            return {"error": f"Failed to calculate complexity: {str(e)}"}
