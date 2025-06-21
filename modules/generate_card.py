import os
from PIL import Image, ImageDraw, ImageFont
from config import CARD_WIDTH, CARD_HEIGHT, CARD_FONT_PATH, CARD_TEMPLATE_PATH, CARD_OUTPUT_PATH, REDDIT_ICON_PATH

def generate_card(subreddit: str, title: str, output_path: str = CARD_OUTPUT_PATH):
    # Create the base image
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), color=(24, 24, 24))
    draw = ImageDraw.Draw(card)

    # Load fonts
    font_subreddit = ImageFont.truetype(CARD_FONT_PATH, size=48)
    font_title = ImageFont.truetype(CARD_FONT_PATH, size=60)

    # Draw subreddit text
    draw.text((160, 40), f"r/{subreddit}", font=font_subreddit, fill=(255, 255, 255))

    # Wrap and draw title text
    max_width = CARD_WIDTH - 100
    lines = []
    words = title.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if draw.textlength(test_line, font=font_title) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    y_text = 120
    for line in lines:
        draw.text((50, y_text), line, font=font_title, fill=(255, 255, 255))
        y_text += 70

    # Add Reddit icon
    if os.path.exists(REDDIT_ICON_PATH):
        icon = Image.open(REDDIT_ICON_PATH).convert("RGBA")
        icon = icon.resize((96, 96), Image.LANCZOS)
        card.paste(icon, (40, 40), icon)

    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
