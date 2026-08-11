from unittest.mock import patch

from app.ai_reviewer import review_code


def test_review_code_detects_division_by_zero():
    code = """
def divide(a, b):
    return a / b
"""

    result = review_code(code)

    assert "ZeroDivisionError" in result


def test_review_code_returns_result_for_valid_code():
    code = """
def add(a, b):
    return a + b
"""

    with patch(
        "app.ai_reviewer.ollama.chat",
        return_value={
            "message": {
                "content": "No significant issues found."
            }
        },
    ):
        result = review_code(code)

    assert result == "No significant issues found."


def test_review_code_handles_ollama_failure():
    with patch(
        "app.ai_reviewer.ollama.chat",
        side_effect=Exception("Ollama unavailable"),
    ):
        result = review_code("x = 10 / 2")

    assert "AI REVIEW ERROR" in result
    assert "Ollama unavailable" in result


def test_review_code_detects_out_of_range_index():
    code = """
items = [10, 20, 30]
print(items[10])
"""

    result = review_code(code)

    assert "IndexError" in result
    assert "outside the valid range" in result