"""Convert all novels to Hugo content files."""
import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NOVELS = [
    {
        "slug": "raqm",
        "title": "Raqm",
        "desc": "A quantum error correction researcher discovers a mysterious pattern in her simulations—one that seems to be replying from across spacetime. A story of science, faith, and love written in the stars.",
        "source_dir": "Novels/Raqm/chapters",
        "file_pattern": re.compile(r"^(\d+)\.md$"),
        "chapter_re": re.compile(r"^#\s+باب\s+(\d+)\s*[:]\s*(.+)$"),
        "num_fn": int,
    },
    {
        "slug": "chirag-e-taufeeq",
        "title": "Chirag-e-Taufeeq",
        "desc": "A principled architect is blacklisted after refusing to sign fraudulent blueprints. She retreats to a historic town where a library, its keeper, and an ancient waqf deed give her a reason to fight back.",
        "source_dir": "Novels/Chirag-e-Taufeeq",
        "file_pattern": re.compile(r"^Chapter_(\d+)\.md$"),
        "chapter_re": re.compile(r"^##\s+باب\s+(\w+)\s*[:]\s*(.+)$"),
        "num_fn": lambda s: {"اول":1,"دوم":2,"سوم":3,"چہارم":4,"پنجم":5,"ششم":6,"ہفتم":7,"ہشتم":8,"نہم":9,"دہم":10,"یازدہم":11,"دوازدہم":12,"سیزدہم":13,"چہاردہم":14,"پانزدہم":15}.get(s, 0),
    },
    {
        "slug": "ghalat-bahan",
        "title": "Ghalat-Bahan",
        "desc": "A story of secrets, mistaken identities, and the fragile bonds that hold families together. Ten chapters of emotional depth and unexpected revelations.",
        "source_dir": "Novels/Ghalat-Bahan/chapters",
        "file_pattern": re.compile(r"^(\d+)-.+\.md$"),
        "chapter_re": re.compile(r"^#\s+باب\s+(\d+)\s*[:]\s*(.+)$"),
        "num_fn": int,
    },
    {
        "slug": "khamosh-ehad",
        "title": "Khamosh-Ehad",
        "desc": "An artist haunted by her past finds that some silences speak louder than words. Six chapters exploring memory, trauma, and the courage to begin again.",
        "source_dir": "Novels/Khamosh-Ehad/chapters",
        "file_pattern": re.compile(r"^(\d+)-.+\.md$"),
        "chapter_re": re.compile(r"^#\s+باب\s+(\d+)\s*[:]\s*(.+)$"),
        "num_fn": int,
    },
]

def convert():
    for info in NOVELS:
        src = os.path.join(BASE_DIR, info["source_dir"])
        dst = os.path.join(BASE_DIR, "content", info["slug"])
        os.makedirs(dst, exist_ok=True)

        # _index.md
        with open(os.path.join(dst, "_index.md"), "w", encoding="utf-8") as f:
            f.write(f"""---
title: "{info['title']}"
description: "{info['desc']}"
---
""")

        files = sorted(
            [f for f in os.listdir(src) if info["file_pattern"].match(f)],
            key=lambda x: int(info["file_pattern"].match(x).group(1)),
        )

        for fname in files:
            with open(os.path.join(src, fname), "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            num = int(info["file_pattern"].match(fname).group(1))
            name = ""

            for line in lines:
                m = info["chapter_re"].match(line.strip())
                if m:
                    raw_num = m.group(1)
                    name = m.group(2).strip()
                    num = info["num_fn"](raw_num)
                    break

            title = f"Chapter {num}"
            if name:
                title += f" — {name}"

            filtered = []
            for line in lines:
                s = line.strip()
                if info["chapter_re"].match(s):
                    continue
                if s.startswith("*آگے:") or s.startswith("_آگے:"):
                    continue
                filtered.append(line)

            body = "\n".join(filtered).strip()
            body = re.sub(r"\n---\s*$", "", body)

            dst_name = f"ch-{num:02d}.md"
            with open(os.path.join(dst, dst_name), "w", encoding="utf-8") as f:
                f.write(f"""---
title: "{title}"
weight: {num}
---

{body}
""")

            print(f"  {info['slug']}/{dst_name}")

    print("\nDone!")

if __name__ == "__main__":
    convert()
