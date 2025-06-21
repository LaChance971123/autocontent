import re

def save_ass_subtitles(segments, path):
    header = """[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 608
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Bangers,110,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,0,5,10,10,540,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def to_ass_timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds - int(seconds)) * 100)
        return f"{hours:d}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def remove_punctuation(text):
        return re.sub(r'[^\w\s]', '', text)

    body = ""
    for segment in segments:
        start = to_ass_timestamp(segment["start"])
        end = to_ass_timestamp(segment["end"])
        clean_word = remove_punctuation(segment["word"])
        text = clean_word.replace('\\', '\\\\').replace('{', '\{').replace('}', '\}')
        body += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\\N\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(header + body)
