# Agent Instructions

## Session Start
At the start of a session, review `.agent/context_snapshot.md`, `.agent/memory.json`, `.agent/daily.md`, `.agent/tasks.md`, and `.agent/lessons.md` for context. Query the SQLite DB (`.agent/ai_worker.db`) if you need active tasks or recent decisions. Consult these files on-demand during work rather than before every response.

## Core Rules
- Generate programs, not manual output
- novel-ai is the root project directory
- Keep responses brief and actionable
- After meaningful work, update `.agent/` files and the SQLite DB via `ai_db.py` / `memory_manager.py`
- All novel content should be in Urdu (اردو) unless otherwise specified
- English for opencode chat, Urdu only for novel content — never mix them
- Never generate Quranic ayahs from memory — always source from quran.com or a saved verified copy
- Maintain character profiles, plot outlines, and chapter drafts as structured files
- Use consistent Urdu script (Nastaliq-friendly) — avoid Arabic-only characters where Urdu differs

## Project Context: Urdu Novel Writing
This project is for creating Urdu novels with AI assistance. Workflows include:
- Brainstorming plots, characters, and settings
- Writing chapter-by-chapter in Urdu
- Maintaining character bibles and story bibles
- Generating and refining narrative prose
- Translating or adapting content where needed
- Managing multiple novel projects simultaneously

## Reference Library
Before writing any novel content, review the relevant files in `Novels/Analysis/` for writing style guidance:
- `profile_Umera_Ahmed.md` — spiritual depth, dual protagonist arcs, strong moral framework
- `profile_Nimra_Ahmed.md` — accessible Urdu, modern heroines, genre-blending, suspense-romance
- `profile_Noor_Rajpoot.md` — emotional intensity, plot twists, redemption arcs
- `profile_Sadia_Rajpoot.md` — philosophical depth, sacrifice themes, psychological realism
- `master_analysis.md` — aggregated emotion/frequency data
- `WritingGuide.md` — complete Urdu novel writing framework
- `EmotionPatterns.md` — character interaction and emotional arc templates
- `AddictionMechanics.md` — chapter-level retention hooks, tension cycles, whiplash design
- `PlotGenerator.md` — structured concept generation, logline formulas, novel outlining
- `SceneBuilder.md` — per-scene planning template with archetypes, pacing, dialogue ratio
- `RevisionWorkflow.md` — four-pass systematic self-editing process
- `CharacterBible.md` — deep character profiles (psychology, backstory, voice card, arc tracker)
- `OpeningHookBank.md` — killer first-line templates by genre
- `VocabularyBank.md` — 10-category idiom/expression bank by emotion and scene type
- `BetaReaderChecklist.md` — structured evaluation form for test readers

### Reference Novels (online research)
- **Aangan** (Khadija Mastur) — feminist Partition novel, domestic space as political metaphor, spare prose, female POV
- **Udas Naslain** (Abdullah Hussain) — epic historical realism, episodic structure spanning 1910-1947, war and Partition trauma
- **Paras** (Nimra Ahmed) — short murder mystery, suspense through flashbacks, wealth vs worth theme
- **Hasil** (Umera Ahmed) — condensed spiritual-romance template, faith crisis and rediscovery, interfaith conflict
- **Zindagi Gulzar Hai** (Umera Ahmed) — epistolary format (dual diary POVs), class-divide enemies-to-lovers, strong female lead struggling against poverty
- **Beli Rajputan Ki Malika** (Nimra Ahmed) — historical mystery-romance, Rajput setting, love triangle, twist ending
- **Namal** (Nimra Ahmed) — epic crime-thriller (1400pp), Quranic Surah-inspired theme, multiple POVs, grey characters, courtroom drama, legal system critique

## Addiction Mechanics
Before writing any chapter, review `Novels/AddictionMechanics.md` for:
- 7-Page Tension Cycle — micro-hooks every 7 pages
- Hook Taxonomy — 7 types of chapter-ending hooks
- Emotional Whiplash Design — alternating emotion pairs
- Information Release Strategy — what to reveal, what to withhold
- Cliffhanger Engineering — page-turner sentence templates
- Multi-Thread Cutting — switching plotlines at peak tension
- Genre-specific addiction patterns
- Reader Psychology Principles — curiosity gap, Zeigarnik effect, variable reward

## Writing Quality Standards
- **Show, don't tell:** Use action, dialogue, and internal monologue to convey emotions
- **Dialogue:** Keep natural and character-appropriate; use Urdu idioms and cultural references
- **Pacing:** Alternate between tense and calm scenes; apply 7-page tension cycle
- **Emotional depth:** Map every scene to an emotional beat; use whiplash pairs
- **Character consistency:** Maintain voice, motivation, and growth arc
- **Islamic/Urdu cultural context:** Integrate naturally, not preachy
- **Chapter hooks:** Every chapter must end with one of 7 hook types — no exceptions

## Novel Structure Template
1. **Introduce flawed protagonist** with relatable modern struggles
2. **Introduce hero/mentor** who challenges their worldview
3. **Rising conflict** — external (society/family) + internal (faith/identity)
4. **Crisis/breaking point** — lowest emotional point
5. **Transformation** — guided by faith, love, or self-realization
6. **Resolution** — character achieves peace/fulfillment, not necessarily material success
