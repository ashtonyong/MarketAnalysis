import os
import re

def remove_emojis_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to match emojis
    # We match typical emoji ranges. This is a broad range but safe for our known python strings.
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27BF]')
    new_content = emoji_pattern.sub('', content)

    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Removed emojis from: {filepath}")

for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            remove_emojis_from_file(filepath)
print("Done")
