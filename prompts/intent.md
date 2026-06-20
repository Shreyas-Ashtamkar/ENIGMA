Classify the user's latest message as either TASK or CONVERSATION.

TASK = The user wants you to DO something concrete (send email, check weather, create image, get time, read/write a file, etc.)
CONVERSATION = The user is chatting, asking questions, greeting, discussing topics, asking for explanations, or just talking.

Examples:
- "What's the weather in Mumbai?" → TASK
- "Send an email to john@example.com" → TASK
- "Generate an image of a sunset" → TASK
- "What time is it in London?" → TASK
- "Read the file report.txt" → TASK
- "Hello, how are you?" → CONVERSATION
- "What is quantum physics?" → CONVERSATION
- "Thanks, that looks great!" → CONVERSATION
- "Tell me a joke" → CONVERSATION
- "Who is the president of India?" → CONVERSATION
- "Can you explain machine learning?" → CONVERSATION

=== GUARDRAILS ===
- Ambiguous requests should be classified conservatively as CONVERSATION unless the intent to execute an action is explicit
- Do not classify requests that ask for explanations, comparisons, or general knowledge as TASK
- Requests that require optional tool use (e.g., "I might need the weather") are CONVERSATION
- Uncertain cases default to CONVERSATION
- Do not attempt to interpret implicit actions

Respond with ONLY one word: TASK or CONVERSATION
