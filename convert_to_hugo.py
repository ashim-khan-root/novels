"""Convert existing novel chapters to Hugo content files."""
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PERSIAN_NUMS = {
    "اول": 1, "دوم": 2, "سوم": 3, "چہارم": 4, "پنجم": 5,
    "ششم": 6, "ہفتم": 7, "ہشتم": 8, "نہم": 9, "دہم": 10,
    "یازدہم": 11, "دوازدہم": 12, "سیزدہم": 13, "چہاردہم": 14, "پانزدہم": 15,
}

def persian_to_int(s):
    return PERSIAN_NUMS.get(s, 0)

NOVELS = [
    {
        "slug": "raqm",
        "title": "رقم",
        "desc": "ایک ایسی محبت کی کہانی جو غلطی سے شروع ہوئی، سچ سے گزری، اور اللہ کے بھروسے پر ختم ہوئی۔",
        "source_dir": "Novels/Raqm/chapters",
        "file_pattern": re.compile(r"^(\d+)\.md$"),
        "chapter_title_re": re.compile(r"^#\s+باب\s+(\d+)\s*[:]\s*(.+)$"),
        "skip_heading_re": re.compile(r"^#\s+"),
    },
    {
        "slug": "chirag-e-taufeeq",
        "title": "چراغِ توفیق",
        "desc": "ایک ایسی محبت کی کہانی جو سچ سے شروع ہوئی، صبر سے گزری، اور اللہ کے بھروسے پر ختم ہوئی۔",
        "source_dir": "Novels/Chirag-e-Taufeeq",
        "file_pattern": re.compile(r"^Chapter_(\d+)\.md$"),
        "chapter_title_re": re.compile(r"^##\s+باب\s+(\w+)\s*[:]\s*(.+)$"),
        "skip_heading_re": re.compile(r"^#\s+"),
    },
]

def convert():
    for info in NOVELS:
        src = os.path.join(BASE_DIR, info["source_dir"])
        dst = os.path.join(BASE_DIR, "content", info["slug"])
        os.makedirs(dst, exist_ok=True)

        # Create _index.md
        index_path = os.path.join(dst, "_index.md")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(f"""---
title: "{info['title']}"
description: "{info['desc']}"
---
""")

        # Convert chapters
        files = sorted(
            (f for f in os.listdir(src) if info["file_pattern"].match(f)),
            key=lambda x: int(info["file_pattern"].match(x).group(1)),
        )

        for fname in files:
            src_path = os.path.join(src, fname)
            with open(src_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")

            # Extract chapter number and name
            num = int(info["file_pattern"].match(fname).group(1))
            name = ""

            for line in lines:
                m = info["chapter_title_re"].match(line.strip())
                if m:
                    raw_num = m.group(1)
                    name = m.group(2).strip()
                    if name.endswith("**"):
                        name = name.rstrip("*")
                    name = name.strip()
                    if info["slug"] == "chirag-e-taufeeq":
                        num = persian_to_int(raw_num)
                    break

            title = f"باب {num}"
            if name:
                title += f" — {name}"

            # Filter content: skip headings, skip "آگے" line
            filtered = []
            for line in lines:
                stripped = line.strip()
                if info["skip_heading_re"].match(stripped):
                    continue
                if info["chapter_title_re"].match(stripped):
                    continue
                if stripped.startswith("*آگے:") or stripped.startswith("_آگے:"):
                    continue
                if stripped == "---" and any(l.strip().startswith("*آگے:") or l.strip().startswith("_آگے:") for l in lines):
                    # Only remove the --- that precedes آگے
                    pass
                else:
                    filtered.append(line)

            # Better approach: remove trailing --- + آگے
            body = "\n".join(filtered).strip()
            # Remove trailing --- that was before آگے
            body = re.sub(r"\n---\s*$", "", body)

            # Write Hugo content file
            dst_name = f"ch-{num:02d}.md"
            dst_path = os.path.join(dst, dst_name)
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(f"""---
title: "{title}"
weight: {num}
---

{body}
""")

            print(f"  {info['slug']}/{dst_name} <- {fname}")

    print("\nDone!")

if __name__ == "__main__":
    convert()
