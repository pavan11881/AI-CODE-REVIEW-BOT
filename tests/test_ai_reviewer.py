from app.ai_reviewer import review_code


def test_review_code_returns_review():
    code_diff = """
+def divide(a, b):
+    return a / b
+
+result = divide(10, 0)
"""

    result = review_code(code_diff)

    assert isinstance(result, str)
    assert len(result) > 0