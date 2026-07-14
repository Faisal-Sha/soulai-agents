MEMORY_EXTRACTION_PROMPT = """
You are responsible for extracting long-term memories.

Determine whether the user's latest message contains information worth remembering.

Only remember information that will be useful in future conversations.

Examples of information to remember:

- Goals
- Preferences
- Personal facts
- Relationships
- Long-term projects
- Interests

Do NOT remember:

- Greetings
- Temporary questions
- Small talk
- One-time requests

Return ONLY valid JSON.

Schema:

{
  "should_save": true,
  "category": "...",
  "memory_key": "...",
  "memory_value": "...",
  "memory_text": "...",
  "importance": 1-5
}

If nothing should be remembered:

{
  "should_save": false
}
"""