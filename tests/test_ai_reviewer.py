from app.ai_reviewer import review_code
from app.review_service import is_reviewable_file


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


def test_is_reviewable_file():
    assert is_reviewable_file("app/main.py") is True
    assert is_reviewable_file("tests/test_ai_reviewer.py") is True
    assert is_reviewable_file("README.md") is False
    assert is_reviewable_file(".env") is False
    assert is_reviewable_file("image.png") is False