import ast

import ollama


def _normalize_code(code_diff: str) -> str:
    """
    Convert a Git diff or normal Python source into Python-like code
    that can be analyzed by the AST parser.
    """
    lines = code_diff.splitlines()

    cleaned_lines = []

    for line in lines:
        if line.startswith(("+++", "---", "@@")):
            continue

        if line.startswith("+"):
            cleaned_lines.append(line[1:])
        elif line.startswith("-"):
            continue
        else:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _detect_division_by_zero_risk(code: str) -> str | None:
    """
    Detect obvious Python division operations where the denominator
    could be zero.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            denominator = node.right

            if isinstance(denominator, ast.Constant):
                if denominator.value == 0:
                    return (
                        "### BUG\n\n"
                        "**Problem:** Division by zero will raise "
                        "`ZeroDivisionError`.\n\n"
                        "**Why it matters:** The program will terminate "
                        "with an exception when this division is executed.\n\n"
                        "**Recommendation:** Validate the denominator "
                        "before performing the division and handle the "
                        "zero case according to the application's "
                        "intended behavior."
                    )

            if isinstance(denominator, ast.Name):
                return (
                    "### BUG\n\n"
                    f"**Problem:** Division using `{denominator.id}` "
                    "can raise `ZeroDivisionError` if the denominator "
                    "is zero.\n\n"
                    "**Why it matters:** The program can terminate "
                    "with an exception at runtime.\n\n"
                    f"**Recommendation:** Validate `{denominator.id}` "
                    "before performing the division and handle the "
                    "zero case explicitly."
                )

    return None


def review_code(code_diff: str) -> str:
    """
    Review changed code using deterministic checks and Ollama.
    """
    code = _normalize_code(code_diff)

    deterministic_review = _detect_division_by_zero_risk(code)

    prompt = f"""
You are a strict senior Python code reviewer.

Review ONLY the changed code below.

CODE:
{code_diff}

CRITICAL PYTHON FACTS:

- Python true division uses `/`.
- `a / 0` raises `ZeroDivisionError`.
- `a / b` can raise `ZeroDivisionError` when `b == 0`.
- Never claim that `/` avoids ZeroDivisionError.
- Never call a division-by-zero problem an AttributeError.
- Do not recommend replacing `/` with `//` unless integer floor division
  is explicitly required.
- `/` and `//` are NOT interchangeable.
- Do not invent bugs.
- Do not report hypothetical issues unless they directly apply to this code.
- Preserve the intended behavior of the program.

Review categories:

1. BUG
2. SECURITY
3. PERFORMANCE
4. QUALITY

For every real issue use:

### CATEGORY

**Problem:** Specific technical problem.

**Why it matters:** Concrete consequence.

**Recommendation:** Specific fix that preserves intended behavior.

If there are no significant issues, output exactly:

No significant issues found.

Be concise and technically accurate.
"""

    try:
        response = ollama.chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        ai_review = response["message"]["content"].strip()

    except Exception as e:
        if deterministic_review:
            return deterministic_review

        return (
            "AI REVIEW ERROR: "
            f"Ollama review failed: {e}"
        )
    if deterministic_review:
        if ai_review == "No significant issues found.":
            return deterministic_review

        return (
            f"{deterministic_review}\n\n"
            "---\n\n"
            "### AI Review\n\n"
            f"{ai_review}"
        )

    return ai_review