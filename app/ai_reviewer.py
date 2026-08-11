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
    Detect obvious division operations where the denominator could be zero.
    This is deterministic and does not depend on the LLM.
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
                        "**Why it matters:** The program will crash when "
                        "this division is executed.\n\n"
                        "**Recommendation:** Validate the denominator before "
                        "performing the division and handle the zero case "
                        "according to the intended application behavior."
                    )

            if isinstance(denominator, ast.Name):
                return (
                    "### BUG\n\n"
                    f"**Problem:** Division using `{denominator.id}` can "
                    "raise `ZeroDivisionError` if the denominator is zero.\n\n"
                    "**Why it matters:** The program can crash at runtime "
                    "when the denominator has a value of zero.\n\n"
                    f"**Recommendation:** Validate `{denominator.id}` "
                    "before performing the division and handle the zero "
                    "case explicitly."
                )

    return None


def review_code(code_diff: str) -> str:
    """
    Review changed code using deterministic checks and Ollama.
    """
    if not code_diff or not code_diff.strip():
        return "No significant issues found."

    code = _normalize_code(code_diff)

    deterministic_review = _detect_division_by_zero_risk(code)

    prompt = f"""
You are a strict senior Python code reviewer.

Review ONLY the changed code in this diff.

CODE DIFF:
{code_diff}

Your goal is to find REAL defects, not to invent issues.

IMPORTANT:

- Analyze the actual programming language and behavior.
- Do not make claims unless you are confident they are technically correct.
- Never change the intended behavior of the code just to make it different.
- Do not recommend "/" -> "//" unless the code clearly requires integer division.
- "/" performs true division. "//" performs floor division. They are NOT interchangeable.
- In Python, division by zero using "/" raises ZeroDivisionError.
- Do not call a ZeroDivisionError an AttributeError.
- Do not report hypothetical problems without explaining why they apply to this exact code.
- Do not report performance issues unless there is a meaningful performance impact.
- Do not invent security vulnerabilities.
- Do not recommend unnecessary changes.
- If you are uncertain whether something is a real issue, do not report it.

Review categories:

1. BUG
2. SECURITY
3. PERFORMANCE
4. QUALITY

For every real issue use:

### CATEGORY

**Problem:** Specific technical problem.

**Why it matters:** Concrete consequence.

**Recommendation:** Specific fix that preserves the intended behavior.

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

        ai_review = (
            response.get("message", {})
            .get("content", "")
            .strip()
        )

        if not ai_review:
            ai_review = "No significant issues found."

    except Exception as e:
        ai_review = (
            "### AI REVIEW ERROR\n\n"
            "**Problem:** The AI reviewer could not complete the "
            "Ollama analysis.\n\n"
            f"**Reason:** `{type(e).__name__}: {e}`\n\n"
            "**Recommendation:** Verify that Ollama is running and "
            "the configured model is available."
        )

    if deterministic_review:
        if ai_review == "No significant issues found.":
            return deterministic_review

        return (
            f"{deterministic_review}\n\n"
            "---\n\n"
            f"### AI Review\n\n{ai_review}"
        )

    return ai_review