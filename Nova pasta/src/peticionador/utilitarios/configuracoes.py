from decouple import config

GEMINI_API_KEY: str = config("GEMINI_API_KEY", default="__MISSING__")
