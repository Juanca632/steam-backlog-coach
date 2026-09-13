"""Validates the LLM output against the real library.

validate_recommendation(appids, known_appids) -> (valid, invalid)

If there are invalid entries, recommend.py retries the prompt once,
including the error. This is what makes "it can't invent games" demonstrable.
"""


def validate_recommendation(
    appids: list[int], known_appids: set[int]
) -> tuple[list[int], list[int]]:
    """Split `appids` into (valid, invalid) against the real library."""
    valid = [appid for appid in appids if appid in known_appids]
    invalid = [appid for appid in appids if appid not in known_appids]
    return valid, invalid
