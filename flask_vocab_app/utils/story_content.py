"""The content contract shared by generation, saving and title migrations."""


def validate_story_title(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A story title is required.")
    title = value.strip()
    if len(title) > 100 or any(char in title for char in "\r\n<>"):
        raise ValueError("Use a plain-text story title of at most 100 characters.")
    return title


def story_schema(include_text=True):
    properties = {
        "title": {"type": "string", "description": "A short, meaningful Russian title, not an excerpt or opening sentence."},
        "title_en": {"type": "string", "description": "A natural English version of the Russian title, naming the same subject or event."},
        "questions": {"type": "array", "items": {"type": "string"}, "minItems": 5, "maxItems": 5},
    }
    if include_text:
        properties["text"] = {"type": "string", "description": "The complete Russian story, without its title."}
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def validate_story_content(data, include_text=True):
    if not isinstance(data, dict):
        raise ValueError("Story generation returned an invalid object.")
    title = validate_story_title(data.get("title"))
    title_en = validate_story_title(data.get("title_en"))
    questions = data.get("questions")
    if not isinstance(questions, list) or len(questions) != 5:
        raise ValueError("A story needs five comprehension questions.")
    if not all(isinstance(question, str) and question.strip() for question in questions):
        raise ValueError("Comprehension questions must be non-empty text.")
    questions = [question.strip() for question in questions]
    if len(set(questions)) != 5:
        raise ValueError("Comprehension questions must be distinct.")
    result = {"title": title, "title_en": title_en, "questions": questions}
    if include_text:
        text = data.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("A story needs its complete text.")
        result["text"] = text.strip()
    return result
