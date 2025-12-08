#!/usr/bin/env python3
"""
Fix markdown links and images by replacing spaces with hyphens in file paths
"""

import re
import sys

def fix_markdown_paths(content):
    """Replace spaces with hyphens in markdown links and images"""

    # Fix markdown links: [text](path with spaces.pdf)
    def fix_link(match):
        text = match.group(1)
        path = match.group(2)
        # Replace spaces with hyphens in the path only
        fixed_path = path.replace(' ', '-')
        return f'[{text}]({fixed_path})'

    # Fix markdown images: ![alt](path with spaces.jpg)
    def fix_image(match):
        alt = match.group(1)
        path = match.group(2)
        # Replace spaces with hyphens in the path only
        fixed_path = path.replace(' ', '-')
        return f'![{alt}]({fixed_path})'

    # Apply fixes
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', fix_link, content)
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_image, content)

    return content

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: fix-markdown-links.py <file.md>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed_content = fix_markdown_paths(content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"Fixed markdown paths in {file_path}")
