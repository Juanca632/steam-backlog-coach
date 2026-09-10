"""Validates the LLM output against the real library.

validate_recommendation(appids, known_appids) -> (valid, invalid)

If there are invalid entries, recommend.py retries the prompt once,
including the error. This is what makes "it can't invent games" demonstrable.
"""
