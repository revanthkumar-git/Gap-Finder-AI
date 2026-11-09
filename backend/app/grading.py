import re


def grade_answer(kind: str, expected: str, submitted: str, options: list[str]) -> bool:
    normalize = lambda value: " ".join(re.findall(r"[a-z0-9]+", value.casefold()))
    expected_normalized = normalize(expected)
    submitted_normalized = normalize(submitted)
    if kind == "mcq":
        letter = re.match(r"^\s*([a-d])(?:\b|[).:\s-])", expected, re.IGNORECASE)
        if letter:
            expected_normalized = letter.group(1).casefold()
            for index, option in enumerate(options):
                option_letter = chr(ord("a") + index)
                option_text = re.sub(r"^\s*[a-d]\s*[).:\-]\s*", "", option, flags=re.IGNORECASE)
                if normalize(option_text) == submitted_normalized:
                    return option_letter == expected_normalized
            submitted_letter = re.match(r"^\s*([a-d])(?:\b|[).:\s-])", submitted, re.IGNORECASE)
            return bool(submitted_letter and submitted_letter.group(1).casefold() == expected_normalized)
    if expected_normalized == submitted_normalized:
        return bool(expected_normalized)
    expected_terms = set(expected_normalized.split())
    submitted_terms = set(submitted_normalized.split())
    if not expected_terms:
        return False
    return len(expected_terms & submitted_terms) / len(expected_terms) >= 0.6
