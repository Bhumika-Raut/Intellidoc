import re


_WHITESPACE = re.compile(r"[ \t]+")
_MULTI_NL = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE.sub(" ", text)
    text = _MULTI_NL.sub("\n\n", text)
    return text.strip()
