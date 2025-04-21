import re
from typing import Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class CalculatorInput(BaseModel):
    expression: str = Field(
        description="The mathematical expression to evaluate (e.g., '2+2', '(3+4)*5')"
    )


@tool(args_schema=CalculatorInput)
def calculator(expression: str) -> Dict[str, any]:
    """
    Evaluate a basic mathematical expression and return the result.
    Supports +, -, *, /, parentheses.
    """
    try:
        sanitized_expression = re.sub(r'\s+', '', expression)
        if not re.match(r'^[0-9+\-*/().]+$', sanitized_expression):
            raise ValueError("Expression contains invalid characters")

        result = eval(sanitized_expression, {"__builtins__": {}}, {})

        return {
            "status": "success",
            "result": result,
            "input_expression": expression
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error evaluating expression: {str(e)}",
            "input_expression": expression
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error evaluating expression: {str(e)}",
            "input_expression": expression
        }
