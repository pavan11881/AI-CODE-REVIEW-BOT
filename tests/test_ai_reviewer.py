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