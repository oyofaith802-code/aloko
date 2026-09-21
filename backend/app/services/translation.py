def translate_text(
    text: str,
    from_language: str,
    to_language: str
):
    if not text.strip():
        raise ValueError("Text cannot be empty.")

    if from_language == to_language:
        return text

    from argostranslate import translate

    translated = translate.translate(
        text,
        from_language,
        to_language
    )

    return translated
