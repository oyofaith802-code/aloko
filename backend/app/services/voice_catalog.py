import edge_tts


async def get_all_voices():
    """
    Fetch all currently available Microsoft Edge TTS voices.
    """

    voices = await edge_tts.list_voices()

    catalog = []

    for voice in voices:
        locale = voice.get("Locale", "")
        short_language = locale.split("-")[0] if locale else ""

        gender = voice.get("Gender", "Unknown")

        catalog.append({
            "id": voice.get("ShortName"),
            "name": voice.get("FriendlyName", voice.get("ShortName")),
            "language": short_language,
            "language_code": locale,
            "country": locale.split("-")[1] if "-" in locale else "",
            "accent": locale,
            "tts_voice": voice.get("ShortName"),
            "voice_type": "builtin",
            "gender": gender.lower(),
            "content_categories": voice.get(
                "VoiceTag", {}
            ).get("ContentCategories", []),
            "personalities": voice.get(
                "VoiceTag", {}
            ).get("VoicePersonalities", []),
        })

    return catalog