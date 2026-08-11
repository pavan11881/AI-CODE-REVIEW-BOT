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


def _detect_obvious_index_error_risk(code: str) -> str | None:
    """
    Detect obvious constant list/tuple indexing errors.

    This intentionally handles only cases that can be proven directly
    from the source code. It does not attempt general static analysis.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    known_lengths = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            value = node.value

            if isinstance(value, (ast.List, ast.Tuple)):
                known_lengths[target.id] = len(value.elts)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue

        if not isinstance(node.value, ast.Name):
            continue

        collection_name = node.value.id

        if collection_name not in known_lengths:
            continue

        index = node.slice

        if isinstance(index, ast.Constant):
            if isinstance(index.value, int):
                length = known_lengths[collection_name]

                if index.value >= length or index.value < -length:
                    return (
                        "### BUG\n\n"
                        f"**Problem:** `{collection_name}[{index.value}]` "
                        f"accesses an index outside the valid range for "
                        f"a collection containing {length} elements.\n\n"
                        "**Why it matters:** This will raise "
                        "`IndexError` at runtime.\n\n"
                        f"**Recommendation:** Use a valid index between "
                        f"`0` and `{length - 1}`, or validate the index "
                        "before accessing the collection."
                    )

    return None


def review_code(code_diff: str) -> str:
    """
    Review changed code using deterministic checks and Ollama.

    Deterministic checks take priority over the LLM because they provide
    higher-confidence findings for problems that can be proven directly
    from the source code.
    """
    code = _normalize_code(code_diff)

    deterministic_reviews = []

    division_review = _detect_division_by_zero_risk(code)

    if division_review:
        deterministic_reviews.append(division_review)

    index_review = _detect_obvious_index_error_risk(code)

    if index_review:
        deterministic_reviews.append(index_review)

    deterministic_review = "\n\n".join(deterministic_reviews)

    # Deterministic findings are authoritative.
    # Do not allow the LLM to override or distort a proven finding.
    if deterministic_review:
        return deterministic_review

    prompt = f"""
You are a strict senior Python code reviewer.

Review ONLY the changed code below.

CODE:
{code_diff}

CRITICAL RULES:

- Never invent a bug.
- Every reported BUG must be directly supported by the supplied code.
- Do not report problems based on speculation.
- Do not report hypothetical behavior that is not applicable to this code.
- Do not criticize normal Python syntax or formatting as a runtime bug.

- The supplied code may be only part of a larger project.
- Do not assume that the supplied snippet is a complete program.
- Functions, variables, classes, and imports may be defined elsewhere.
- Never report a NameError merely because a function, variable, class,
  or module is not defined in the supplied snippet.
- Only report an undefined-name problem when the supplied code itself
  clearly proves that the name cannot be resolved in the shown execution
  context.
- Do not call an undefined-name problem a SyntaxError.
- A missing definition in an isolated snippet is not sufficient evidence
  of a bug.
- Do not invent missing imports or missing project context.

- A normal newline at the end of a Python file is valid and is NOT a bug.
- Do not claim that a trailing newline causes a syntax error.
- Do not claim that an editor will execute a line differently because
  of a newline.
- Do not invent interactions with editors, IDEs, terminals, or operating
  systems.

- Do not report a bug merely because code could theoretically be improved.
- Preserve the intended behavior of the program.
- Distinguish actual runtime errors from style or documentation
  suggestions.

IMPORTANT PYTHON SEMANTICS:

- `a / 0` raises `ZeroDivisionError`.
- `a / b` can raise `ZeroDivisionError` when `b == 0`.
- `/` and `//` are not interchangeable.
- `items[10]` raises `IndexError` when `items` contains fewer than
  11 elements.
- Accessing a list or tuple with an out-of-range constant index is a
  real runtime bug.
- A newline at the end of a Python source file is valid.
- An undefined variable or function generally causes `NameError` at
  runtime, not `SyntaxError`.

REVIEW CATEGORIES:

1. BUG
2. SECURITY
3. PERFORMANCE
4. QUALITY

Only report an issue when there is sufficient evidence in the supplied
code.

For every real issue use exactly:

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
        return (
            "AI REVIEW ERROR: "
            f"Ollama review failed: {e}"
        )

    return ai_review