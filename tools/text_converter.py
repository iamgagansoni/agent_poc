from pydantic import BaseModel, Field
from typing import Any, Dict
from langchain_core.tools import tool

class TextConverterInput(BaseModel):
    text: str = Field(description="The text to convert")
    operation: str = Field(
        description="The operation to perform (to_upper or to_lower)",
        enum=["to_upper", "to_lower"]
    )

class TextConverterInputSchema(BaseModel):
    params: TextConverterInput

@tool(args_schema=TextConverterInputSchema)
def text_converter(params: TextConverterInput) -> Dict[str, Any]:
    """Converts text to uppercase or lowercase based on the specified operation."""
    text = params.text
    operation = params.operation

    try:
        if operation == "to_upper":
            result = text.upper()
        elif operation == "to_lower":
            result = text.lower()
        else:
            return {
                "status": "error",
                "message": f"Unknown operation: {operation}",
                "input_text": text
            }

        return {
            "status": "success",
            "result": result,
            "operation": operation,
            "input_text": text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error converting text: {str(e)}",
            "input_text": text
        }
