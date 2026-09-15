"""광고의 표현 형식을 정리한다. 사실 여부를 판단하는 코드는 아니다."""
import re


# 일반적인 이모지 영역과 조합 문자. 숫자·# 자체는 보존한다.
EMOJI = re.compile(
    r"[#*0-9]\ufe0f?\u20e3|"
    r"[\U0001f000-\U0001faff\u2600-\u27bf\u2300-\u23ff"
    r"\u200d\ufe0e\ufe0f\u20e3\U000e0020-\U000e007f]"
)


def clean_text(text: str) -> str:
    text = EMOJI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    # 코드 울타리, 제목·목록 기호를 제거하고 문구는 남긴다.
    text = re.sub(r"(?m)^\s*(```|~~~)[^\n]*$", "", text)
    text = re.sub(r"(?m)^[ \t]*(?:#{1,6}\s+|>\s*|[-*+•]\s+|\d+[.)]\s+)", "", text)
    text = re.sub(r"!?\[([^\]]+)\]\([^\n)]*\)", r"\1", text)
    for marker in ("**", "__", "~~", "*", "_", "`"):
        escaped = re.escape(marker)
        text = re.sub(escaped + r"(\S(?:.*?\S)?)" + escaped, r"\1", text)
    text = "\n".join(re.sub(r"[^\S\n]+", " ", line).strip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_ad_data(data: dict) -> dict:
    cleaned = dict(data)
    for key, limit in (("headline", 100), ("body", 1000), ("cta", 100)):
        if isinstance(cleaned.get(key), str):
            text = clean_text(cleaned[key])
            if key != "body":
                text = " ".join(text.split())
            cleaned[key] = text[:limit].rstrip()

    tags = cleaned.get("hashtags")
    # 잘못된 자료형은 그대로 두어 AdCopy 검증에서 거절한다.
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        normalized = []
        seen = set()
        for tag in tags:
            tag = re.sub(r"[^\w]", "", clean_text(tag))
            if tag and tag.casefold() not in seen:
                seen.add(tag.casefold())
                normalized.append("#" + tag)
        cleaned["hashtags"] = normalized[:5]
    return cleaned
