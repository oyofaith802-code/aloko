from fastapi import APIRouter

router = APIRouter(
    prefix="/translator",
    tags=["Voice Translator"]
)


TRANSLATOR_LOCALES = [
    # English
    {"language": "en", "country": "AU", "accent": "en-AU"},
    {"language": "en", "country": "CA", "accent": "en-CA"},
    {"language": "en", "country": "GB", "accent": "en-GB"},
    {"language": "en", "country": "GH", "accent": "en-GH"},
    {"language": "en", "country": "HK", "accent": "en-HK"},
    {"language": "en", "country": "IE", "accent": "en-IE"},
    {"language": "en", "country": "IN", "accent": "en-IN"},
    {"language": "en", "country": "KE", "accent": "en-KE"},
    {"language": "en", "country": "NG", "accent": "en-NG"},
    {"language": "en", "country": "NZ", "accent": "en-NZ"},
    {"language": "en", "country": "PH", "accent": "en-PH"},
    {"language": "en", "country": "SG", "accent": "en-SG"},
    {"language": "en", "country": "TZ", "accent": "en-TZ"},
    {"language": "en", "country": "US", "accent": "en-US"},
    {"language": "en", "country": "ZA", "accent": "en-ZA"},

    # Spanish
    {"language": "es", "country": "AR", "accent": "es-AR"},
    {"language": "es", "country": "BO", "accent": "es-BO"},
    {"language": "es", "country": "CL", "accent": "es-CL"},
    {"language": "es", "country": "CO", "accent": "es-CO"},
    {"language": "es", "country": "CR", "accent": "es-CR"},
    {"language": "es", "country": "CU", "accent": "es-CU"},
    {"language": "es", "country": "DO", "accent": "es-DO"},
    {"language": "es", "country": "EC", "accent": "es-EC"},
    {"language": "es", "country": "ES", "accent": "es-ES"},
    {"language": "es", "country": "GQ", "accent": "es-GQ"},
    {"language": "es", "country": "GT", "accent": "es-GT"},
    {"language": "es", "country": "HN", "accent": "es-HN"},
    {"language": "es", "country": "MX", "accent": "es-MX"},
    {"language": "es", "country": "NI", "accent": "es-NI"},
    {"language": "es", "country": "PA", "accent": "es-PA"},
    {"language": "es", "country": "PE", "accent": "es-PE"},
    {"language": "es", "country": "PR", "accent": "es-PR"},
    {"language": "es", "country": "PY", "accent": "es-PY"},
    {"language": "es", "country": "SV", "accent": "es-SV"},
    {"language": "es", "country": "US", "accent": "es-US"},
    {"language": "es", "country": "UY", "accent": "es-UY"},
    {"language": "es", "country": "VE", "accent": "es-VE"},

    # French
    {"language": "fr", "country": "BE", "accent": "fr-BE"},
    {"language": "fr", "country": "CA", "accent": "fr-CA"},
    {"language": "fr", "country": "CH", "accent": "fr-CH"},
    {"language": "fr", "country": "FR", "accent": "fr-FR"},

    # German
    {"language": "de", "country": "AT", "accent": "de-AT"},
    {"language": "de", "country": "CH", "accent": "de-CH"},
    {"language": "de", "country": "DE", "accent": "de-DE"},

    # Portuguese
    {"language": "pt", "country": "BR", "accent": "pt-BR"},
    {"language": "pt", "country": "PT", "accent": "pt-PT"},

    # Chinese
    {"language": "zh", "country": "CN", "accent": "zh-CN"},
    {"language": "zh", "country": "HK", "accent": "zh-HK"},
    {"language": "zh", "country": "TW", "accent": "zh-TW"},

    # Arabic
    {"language": "ar", "country": "AE", "accent": "ar-AE"},
    {"language": "ar", "country": "BH", "accent": "ar-BH"},
    {"language": "ar", "country": "DZ", "accent": "ar-DZ"},
    {"language": "ar", "country": "EG", "accent": "ar-EG"},
    {"language": "ar", "country": "IQ", "accent": "ar-IQ"},
    {"language": "ar", "country": "JO", "accent": "ar-JO"},
    {"language": "ar", "country": "KW", "accent": "ar-KW"},
    {"language": "ar", "country": "LB", "accent": "ar-LB"},
    {"language": "ar", "country": "LY", "accent": "ar-LY"},
    {"language": "ar", "country": "MA", "accent": "ar-MA"},
    {"language": "ar", "country": "OM", "accent": "ar-OM"},
    {"language": "ar", "country": "QA", "accent": "ar-QA"},
    {"language": "ar", "country": "SA", "accent": "ar-SA"},
    {"language": "ar", "country": "SY", "accent": "ar-SY"},
    {"language": "ar", "country": "TN", "accent": "ar-TN"},
    {"language": "ar", "country": "YE", "accent": "ar-YE"},

    # Italian
    {"language": "it", "country": "IT", "accent": "it-IT"},

    # Japanese
    {"language": "ja", "country": "JP", "accent": "ja-JP"},

    # Korean
    {"language": "ko", "country": "KR", "accent": "ko-KR"},

    # Hindi
    {"language": "hi", "country": "IN", "accent": "hi-IN"},

    # Bengali
    {"language": "bn", "country": "BD", "accent": "bn-BD"},
    {"language": "bn", "country": "IN", "accent": "bn-IN"},

    # Dutch
    {"language": "nl", "country": "BE", "accent": "nl-BE"},
    {"language": "nl", "country": "NL", "accent": "nl-NL"},

    # Greek
    {"language": "el", "country": "GR", "accent": "el-GR"},

    # Hebrew
    {"language": "he", "country": "IL", "accent": "he-IL"},

    # Indonesian
    {"language": "id", "country": "ID", "accent": "id-ID"},

    # Malay
    {"language": "ms", "country": "MY", "accent": "ms-MY"},

    # Polish
    {"language": "pl", "country": "PL", "accent": "pl-PL"},

    # Russian
    {"language": "ru", "country": "RU", "accent": "ru-RU"},

    # Ukrainian
    {"language": "uk", "country": "UA", "accent": "uk-UA"},

    # Turkish
    {"language": "tr", "country": "TR", "accent": "tr-TR"},

    # Thai
    {"language": "th", "country": "TH", "accent": "th-TH"},

    # Vietnamese
    {"language": "vi", "country": "VN", "accent": "vi-VN"},

    # Swahili
    {"language": "sw", "country": "KE", "accent": "sw-KE"},

    # Persian
    {"language": "fa", "country": "IR", "accent": "fa-IR"},

    # Portuguese already above
    # Romanian
    {"language": "ro", "country": "RO", "accent": "ro-RO"},

    # Czech
    {"language": "cs", "country": "CZ", "accent": "cs-CZ"},

    # Danish
    {"language": "da", "country": "DK", "accent": "da-DK"},

    # Swedish
    {"language": "sv", "country": "SE", "accent": "sv-SE"},

    # Norwegian
    {"language": "nb", "country": "NO", "accent": "nb-NO"},

    # Finnish
    {"language": "fi", "country": "FI", "accent": "fi-FI"},

    # Hungarian
    {"language": "hu", "country": "HU", "accent": "hu-HU"},

    # Croatian
    {"language": "hr", "country": "HR", "accent": "hr-HR"},

    # Slovak
    {"language": "sk", "country": "SK", "accent": "sk-SK"},

    # Slovenian
    {"language": "sl", "country": "SI", "accent": "sl-SI"},

    # Macedonian
    {"language": "mk", "country": "MK", "accent": "mk-MK"},

    # Nepali
    {"language": "ne", "country": "NP", "accent": "ne-NP"},

    # Pashto
    {"language": "ps", "country": "AF", "accent": "ps-AF"},

    # Tamil
    {"language": "ta", "country": "IN", "accent": "ta-IN"},

    # Telugu
    {"language": "te", "country": "IN", "accent": "te-IN"},

    # Javanese
    {"language": "jv", "country": "ID", "accent": "jv-ID"},

    # Zulu
    {"language": "zu", "country": "ZA", "accent": "zu-ZA"},

    # Afrikaans
    {"language": "af", "country": "ZA", "accent": "af-ZA"},
]


@router.get("/locales")
async def get_translator_locales():
    return {
        "locales": TRANSLATOR_LOCALES
    }