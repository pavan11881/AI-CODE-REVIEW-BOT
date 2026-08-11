from app.ai_reviewer import review_code


def test_review_code_detects_division_by_zero():
    code = """
def calculate_average(total, count):
    return total / count
"""

    result = review_code(code)

    assert result
    assert "division" in result.lower() or "zero" in result.lower()


def test_review_code_returns_result_for_valid_code():
    code = """
def add(a, b):
    return a + b
"""

    result = review_code(code)

    assert result
    
def test_review_code_handles_ollama_failure():
    from unittest.mock import patch

    with patch(
        "app.ai_reviewer.ollama.chat",
        side_effect=Exception("Ollama unavailable"),
    ):
        result = review_code("x = 10 / 2")

    assert "AI REVIEW ERROR" in result
    assert "Ollama unavailable" in result