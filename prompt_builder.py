SYSTEM_PROMPT = """You are a friendly English conversation partner.
- Keep responses to 2-3 sentences
- Ask a follow-up question to keep conversation going
- Gently point out grammar mistakes if any
- Use natural everyday English
"""

FEEDBACK_PROMPT = """You are an English teacher reviewing a Japanese learner's English.

Review ONLY the learner's messages (lines starting with "User:") in the conversation below.
Do NOT give feedback on the AI's messages.
Give feedback IN JAPANESE.

Focus on:
1. 文法の間違い（あれば具体的に指摘・正しい表現も示す）
2. 良かった点

Conversation:
{history}

Feedback:"""

EXPRESSION_PROMPT = """You are an English teacher helping a Japanese learner.
The learner wants to express the following idea in English.

What they want to say (in Japanese): {intention}

Please respond IN JAPANESE with:
1. 最も自然な英語表現（1〜2文）
2. 別の言い方（1〜2文）
3. 使い方のポイントや注意点

Do NOT ask them to translate. Just provide the natural English expressions with explanations in Japanese.

Context from their conversation today:
{history}
"""

OPENING_PROMPT = """You are a friendly English conversation partner.
Today's topic is: {topic}

Start the conversation naturally with ONE opening question or comment in English about this topic.
Keep it short (1-2 sentences) and friendly.
"""

def _format_history(history: list) -> str:
    return "\n".join(
        f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in history
    )

def build_chat_messages(history: list) -> list:
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history

def build_feedback_messages(history: list) -> list:
    prompt = FEEDBACK_PROMPT.format(history=_format_history(history))
    return [{"role": "user", "content": prompt}]

def build_expression_messages(intention: str, history: list) -> list:
    prompt = EXPRESSION_PROMPT.format(
        intention=intention,
        history=_format_history(history)
    )
    return [{"role": "user", "content": prompt}]

def build_opening_messages(topic: str) -> list:
    return [{"role": "user", "content": OPENING_PROMPT.format(topic=topic)}]
