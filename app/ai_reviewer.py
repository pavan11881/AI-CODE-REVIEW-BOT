import ollama


def review_code(code_diff: str) -> str:
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

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response["message"]["content"]







