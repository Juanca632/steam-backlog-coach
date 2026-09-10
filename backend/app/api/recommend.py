"""Recommendation endpoint.

POST /recommend  { available_time_min: int, mood: str }
  1. build the candidate backlog from the DB
  2. build the prompt (llm/prompt.py) and call the LLM (llm/client.py)
  3. validate that the returned appid(s) exist in the library (llm/validate.py);
     if not, retry once.
"""
