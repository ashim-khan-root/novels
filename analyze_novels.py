"""Extract text from Urdu novel PDFs, analyze writing style, and generate author profiles."""
import os
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

try:
    import fitz
except ImportError:
    fitz = None

BASE = Path(__file__).parent / "Novels" / "References"
OUT = Path(__file__).parent / "Novels"

NOVEL_DIRS = [
    "Sulphite", "Peer-e-Kamil", "Jannat-Kay-Pattay",
    "Haalim", "Mushaf", "Alif", "Mala", "Ishq-Aatish",
]

AUTHOR_MAP = {
    "Sulphite": "Noor Rajpoot",
    "Peer-e-Kamil": "Umera Ahmed",
    "Jannat-Kay-Pattay": "Nimra Ahmed",
    "Haalim": "Nimra Ahmed",
    "Mushaf": "Nimra Ahmed",
    "Alif": "Umera Ahmed",
    "Mala": "Nimra Ahmed",
    "Ishq-Aatish": "Sadia Rajpoot",
}

GENRE_MAP = {
    "Sulphite": "Romantic / Spiritual / Suspense",
    "Peer-e-Kamil": "Spiritual / Islamic / Romance",
    "Jannat-Kay-Pattay": "Romantic / Spiritual / Self-discovery",
    "Haalim": "Fantasy / Time-travel / Romantic",
    "Mushaf": "Islamic / Spiritual / Romance",
    "Alif": "Spiritual / Artistic / Romance",
    "Mala": "Socio-romantic / Suspense",
    "Ishq-Aatish": "Romantic / Social / Philosophical",
}

URDU_EMOTION_WORDS = {
    "محبت": "love", "عشق": "passion", "پیار": "love",
    "درد": "pain", "غم": "sorrow", "خوشی": "happiness",
    "آنسو": "tears", "تنہائی": "loneliness", "وفا": "loyalty",
    "جدائی": "separation", "ملن": "union", "التجا": "plea",
    "التفات": "attention", "نفرت": "hate", "حسد": "jealousy",
    "ایمان": "faith", "توکل": "trust_in_Allah", "صبر": "patience",
    "سکون": "peace", "بے_چینی": "restlessness", "خوف": "fear",
    "امید": "hope", "مایوسی": "despair", "شکوہ": "complaint",
    "احساس": "feeling", "جذبات": "emotions", "خیال": "thought",
    "سپنا": "dream", "خواب": "dream", "یقین": "certainty",
    "شک": "doubt", "قربانی": "sacrifice", "انتظار": "waiting",
}

URDU_DIALOGUE_MARKERS = re.compile(r'["\u201C\u201D\u2018\u2019\u00AB\u00BB'+"'"+']+')

def extract_text_pymupdf(pdf_path):
    if fitz is None:
        return ""
    try:
        doc = fitz.open(pdf_path)
        all_text = []
        for page in doc:
            txt = page.get_text("text")
            if txt.strip():
                all_text.append(txt)
        doc.close()
        return "\n".join(all_text)
    except Exception as e:
        return f""

def analyze_text(text, novel_name, author):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    total_chars = len(text)

    words = re.findall(r'[\w\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+', text)
    word_count = len(words)
    urdu_words = [w for w in words if re.match(r'[\u0600-\u06FF]', w)]
    urdu_word_count = len(urdu_words)

    unique_words = len(set(w.lower() for w in urdu_words))
    
    para_breaks = text.count("\n\n")
    sentences = len(re.split(r'[.!?\u060C\u061F]+', text))

    emotion_hits = Counter()
    for uw, emotion in URDU_EMOTION_WORDS.items():
        c = text.count(uw)
        if c:
            emotion_hits[emotion] += c

    dialogue_count = len(URDU_DIALOGUE_MARKERS.findall(text)) // 2

    question_marks = text.count("؟") + text.count("?")
    exclamation_marks = text.count("!") + text.count("!")

    lines_with_colon = sum(1 for l in lines if ":" in l or ":" in l)
    narrative_lines = max(1, len(lines) - lines_with_colon)

    avg_sentence_len = word_count / max(sentences, 1)
    dialogue_density = dialogue_count / max(sentences, 1)
    question_density = question_marks / max(sentences, 1)
    unique_ratio = unique_words / max(urdu_word_count, 1)

    top_emotions = [e for e, c in emotion_hits.most_common(8) if c > 0]

    return {
        "novel": novel_name,
        "author": author,
        "genre": GENRE_MAP.get(novel_name, "Unknown"),
        "stats": {
            "total_chars": total_chars,
            "total_words": word_count,
            "urdu_words": urdu_word_count,
            "unique_urdu_words": unique_words,
            "sentences": sentences,
            "paragraphs": para_breaks,
            "avg_sentence_length": round(avg_sentence_len, 1),
            "lexical_diversity": round(unique_ratio, 3),
            "dialogue_markers": dialogue_count,
            "dialogue_density": round(dialogue_density, 3),
            "questions_asked": question_marks,
            "exclamations": exclamation_marks,
        },
        "emotions_detected": top_emotions,
        "emotion_counts": dict(emotion_hits.most_common(15)),
    }

def generate_writing_analysis(analysis):
    novel = analysis["novel"]
    author = analysis["author"]
    s = analysis["stats"]
    emotions = analysis["emotions_detected"]
    ec = analysis["emotion_counts"]

    lines = []
    lines.append(f"## {novel} by {author}")
    lines.append("")
    lines.append(f"**Genre:** {analysis['genre']}")
    lines.append(f"**Words:** {s['total_words']:,}  |  **Urdu words:** {s['urdu_words']:,}  |  **Unique:** {s['unique_urdu_words']:,}")
    lines.append(f"**Avg sentence length:** {s['avg_sentence_length']} words  |  **Lexical diversity:** {s['lexical_diversity']}")
    lines.append(f"**Dialogue density:** {s['dialogue_density']}  |  **Questions:** {s['questions_asked']}  |  **Exclamations:** {s['exclamations']}")
    lines.append("")
    lines.append("**Dominant emotions:** " + ", ".join(emotions[:6]))
    lines.append("")
    lines.append("**Emotion frequency:**")
    for em, ct in sorted(ec.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"  - {em}: {ct}")
    lines.append("")
    return "\n".join(lines)

def generate_profile(author, novels_data):
    relevant = [n for n in novels_data if n["author"] == author]
    if not relevant:
        return ""

    lines = []
    lines.append(f"# Author Profile: {author}")
    lines.append("")
    
    # Aggregate stats
    total_words = sum(n["stats"]["total_words"] for n in relevant)
    avg_sent_len = sum(n["stats"]["avg_sentence_length"] for n in relevant) / len(relevant)
    avg_lex_div = sum(n["stats"]["lexical_diversity"] for n in relevant) / len(relevant)
    avg_dialogue = sum(n["stats"]["dialogue_density"] for n in relevant) / len(relevant)

    all_emotions = Counter()
    for n in relevant:
        for e, c in n["emotion_counts"].items():
            all_emotions[e] += c

    lines.append(f"**Novels analyzed:** {', '.join(n['novel'] for n in relevant)}")
    lines.append(f"**Total words:** {total_words:,}")
    lines.append(f"**Avg sentence length:** {avg_sent_len:.1f} words")
    lines.append(f"**Avg lexical diversity:** {avg_lex_div:.3f}")
    lines.append(f"**Avg dialogue density:** {avg_dialogue:.3f}")
    lines.append("")
    lines.append("**Signature emotions:**")
    for e, c in all_emotions.most_common(10):
        lines.append(f"  - {e}: {c}")
    lines.append("")
    lines.append("**Writing style notes:**")
    
    style_notes = []
    if avg_sent_len < 12:
        style_notes.append("- Short, punchy sentences — fast-paced narrative")
    elif avg_sent_len < 18:
        style_notes.append("- Moderate sentence length — balanced narrative flow")
    else:
        style_notes.append("- Long, elaborate sentences — descriptive, immersive style")
    if avg_dialogue > 0.25:
        style_notes.append("- Heavy dialogue use — character-driven storytelling")
    elif avg_dialogue > 0.15:
        style_notes.append("- Moderate dialogue — balanced between narration and conversation")
    else:
        style_notes.append("- Narrative-heavy — descriptive prose dominates")
    if avg_lex_div > 0.25:
        style_notes.append("- Rich vocabulary — diverse word choice")
    else:
        style_notes.append("- Accessible vocabulary — reader-friendly")
    if "faith" in all_emotions or "patience" in all_emotions:
        style_notes.append("- Strong spiritual/Islamic thematic undercurrent")
    if "love" in all_emotions or "passion" in all_emotions:
        style_notes.append("- Romance-centered emotional core")
    if "pain" in all_emotions or "sorrow" in all_emotions:
        style_notes.append("- Emotional depth with melancholy undertones")

    lines.extend(style_notes)
    lines.append("")
    return "\n".join(lines)


def main():
    all_analyses = []

    for novel_dir_name in NOVEL_DIRS:
        folder = BASE / novel_dir_name
        pdfs = list(folder.glob("*.pdf"))
        if not pdfs:
            print(f"[SKIP] {novel_dir_name} — no PDF found")
            continue
        
        pdf_path = pdfs[0]
        print(f"[ANALYZE] {novel_dir_name} ({pdf_path.name})...")
        
        text = extract_text_pymupdf(pdf_path)
        if not text or len(text.strip()) < 100:
            print(f"  Text extraction limited ({len(text)} chars)")
        
        analysis = analyze_text(text, novel_dir_name, AUTHOR_MAP.get(novel_dir_name, "Unknown"))
        all_analyses.append(analysis)

    analysis_dir = OUT / "Analysis"
    analysis_dir.mkdir(exist_ok=True)

    # Write individual analyses
    combined = []
    profiles = defaultdict(list)
    
    for a in all_analyses:
        analysis_text = generate_writing_analysis(a)
        combined.append(analysis_text)
        profiles[a["author"]].append(a)

        with open(analysis_dir / f"{a['novel']}_analysis.md", "w", encoding="utf-8") as f:
            f.write(analysis_text)
        
        with open(analysis_dir / f"{a['novel']}_data.json", "w", encoding="utf-8") as f:
            json.dump(a, f, ensure_ascii=False, indent=2)
        
        print(f"  Written: {a['novel']}_analysis.md")

    # Write master analysis
    with open(analysis_dir / "master_analysis.md", "w", encoding="utf-8") as f:
        f.write("# Urdu Novel Analysis — Master Reference\n\n")
        f.write("Comprehensive analysis of reference Urdu novels for AI training.\n\n")
        f.write("---\n\n".join(combined))

    # Write author profiles
    for author, data in profiles.items():
        profile = generate_profile(author, data)
        with open(analysis_dir / f"profile_{author.replace(' ', '_')}.md", "w", encoding="utf-8") as f:
            f.write(profile)
        print(f"  Profile: {author}")

    print(f"\nDone. Analysis written to {analysis_dir}")
    
    analysis_json = analysis_dir / "analyses.json"
    with open(analysis_json, "w", encoding="utf-8") as f:
        json.dump(all_analyses, f, ensure_ascii=False, indent=2)
    print(f"  JSON: {analysis_json}")

if __name__ == "__main__":
    main()
