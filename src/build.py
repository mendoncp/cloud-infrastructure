#!/usr/bin/env python3
"""Assemble index.html and azure-study-guide.md from parts."""
import json, io, os
import markdown

D = "/sessions/upbeat-practical-goldberg/mnt/outputs/src"
OUT = "/sessions/upbeat-practical-goldberg/mnt/outputs"

CATNAMES_ORDER = {"APIM":"API Management","ServiceBus":"Service Bus","RBAC":"RBAC & Governance",
    "Networking":"Networking","ContainerApps":"Container Apps","Auth":"Auth & Identity",
    "Patterns,Exam":"Architecture & Exam","Data":"Data Storage","BCDR":"Business Continuity",
    "Monitor":"Monitoring","Compute":"Compute","Migration":"Migration & Integration",
    "Auth,RBAC,Patterns":"Key Vault, Hybrid & IaC"}

# 1. Assemble markdown study guide
md_parts = []
for p in ["md_part1.md", "md_part2.md", "md_part3.md", "md_part4.md", "md_part5.md",
          "md_part6.md", "md_part7.md", "md_part8.md", "md_part9.md", "md_part10.md"]:
    md_parts.append(open(os.path.join(D, p), encoding="utf-8").read())
md_body = "\n".join(md_parts)

# 1b. Inject per-topic extras (quick check + whiteboards + resources) at end of each section
import re as _re
extras_raw = ""
for p in ["extras_a.md", "extras_b.md"]:
    extras_raw += open(os.path.join(D, p), encoding="utf-8").read() + "\n"
blocks = _re.split(r"%%SECTION (\d+)\|([^%]+)%%", extras_raw)
# blocks: ['', n, cats, content, n, cats, content, ...]
extras = {}
for i in range(1, len(blocks), 3):
    n, cats, content = blocks[i], blocks[i+1].strip(), blocks[i+2]
    quick = (f'\n### 📝 Quick Check — {CATNAMES_ORDER.get(cats, "exam concepts")}\n\n'
             f'<div class="inlinequiz" data-cat="{cats}">Interactive quick check available in the web app. '
             f'Full Q&A with explanations: see the Practice Questions appendix.</div>\n')
    extras[int(n)] = quick + content
for n in sorted(extras, reverse=True):
    m = _re.search(rf"^## {n}\. .*$", md_body, _re.M)
    assert m, f"section {n} heading not found"
    nxt = _re.search(rf"^## {n+1}\. ", md_body[m.end():], _re.M)
    ins = m.end() + (nxt.start() if nxt else len(md_body) - m.end())
    md_body = md_body[:ins] + extras[n] + "\n" + md_body[ins:]
print("Injected extras into sections:", sorted(extras))

# Load quiz + cards
quiz = []
for p in ["quiz_a.json", "quiz_b.json", "quiz_c.json", "quiz_d.json", "quiz_e.json",
          "quiz_f.json", "quiz_g.json", "quiz_h.json"]:
    quiz += json.load(open(os.path.join(D, p), encoding="utf-8"))
cards = []
for p in ["cards_a.json", "cards_b.json", "cards_c.json", "cards_d.json", "cards_e.json"]:
    cards += json.load(open(os.path.join(D, p), encoding="utf-8"))

print(f"Quiz questions: {len(quiz)}  Flashcards: {len(cards)}")

cats = {}
for q in quiz:
    t = q.get("t", "single")
    if t == "single":
        assert len(q["o"]) >= 2 and 0 <= q["a"] < len(q["o"]), q["q"][:50]
    elif t == "multi":
        assert isinstance(q["a"], list) and all(0 <= i < len(q["o"]) for i in q["a"]), q["q"][:50]
    elif t == "order":
        assert len(q["o"]) >= 2, q["q"][:50]
    cats[q["c"]] = cats.get(q["c"], 0) + 1
print("Quiz by category:", cats)
ccats = {}
for c in cards:
    ccats[c["c"]] = ccats.get(c["c"], 0) + 1
print("Cards by category:", ccats)

CATNAMES = {"APIM":"API Management","ServiceBus":"Service Bus","RBAC":"RBAC & Governance",
            "Networking":"Networking","ContainerApps":"Container Apps","Auth":"Auth & Identity",
            "Patterns":"Design Patterns","Exam":"AZ-305 Exam",
            "Data":"Data Storage","BCDR":"Business Continuity","Monitor":"Monitoring",
            "Compute":"Compute","Migration":"Migration & Integration"}

# 2. Q&A appendix + flashcard appendix for the md/pdf version
buf = io.StringIO()
buf.write("\n---\n\n## 18. Practice Questions (Q&A)\n\n")
buf.write(f"{len(quiz)} exam-style questions. Answers immediately follow each question.\n")
cur = None
n = 0
for q in quiz:
    if q["c"] != cur:
        cur = q["c"]
        buf.write(f"\n### {CATNAMES.get(cur, cur)}\n\n")
    n += 1
    t = q.get("t", "single")
    buf.write(f"**Q{n}. {q['q']}**\n\n")
    for i, o in enumerate(q["o"]):
        buf.write(f"- {chr(65+i)}. {o}\n")
    if t == "single":
        buf.write(f"\n> **Answer: {chr(65+q['a'])}.** {q['e']}\n\n")
    elif t == "multi":
        letters = ", ".join(chr(65+i) for i in q["a"])
        buf.write(f"\n> **Answers: {letters}.** {q['e']}\n\n")
    else:
        buf.write(f"\n> **Answer: the steps are listed above in the correct order (A\u2192{chr(65+len(q['o'])-1)}).** {q['e']}\n\n")

buf.write("\n---\n\n## 19. Flashcards\n\n")
buf.write(f"{len(cards)} flashcards — cover the right column and recall.\n")
cur = None
for c in cards:
    if c["c"] != cur:
        cur = c["c"]
        buf.write(f"\n### {CATNAMES.get(cur, cur)}\n\n| Prompt | Answer |\n|---|---|\n")
    f = c["f"].replace("|", "\\|")
    b = c["b"].replace("|", "\\|")
    buf.write(f"| **{f}** | {b} |\n")

md_full = md_body + buf.getvalue()
open(os.path.join(OUT, "azure-study-guide.md"), "w", encoding="utf-8").write(md_full)
print("Wrote azure-study-guide.md:", len(md_full), "chars")

# 3. Build index.html (study content = sections 1-16; quizzes/cards are interactive)
html_content = markdown.markdown(md_body, extensions=["tables", "fenced_code", "sane_lists"])
tpl = open(os.path.join(D, "template.html"), encoding="utf-8").read()
out = tpl.replace("__CONTENT__", html_content)
out = out.replace("__QUIZ__", json.dumps(quiz, ensure_ascii=False))
out = out.replace("__CARDS__", json.dumps(cards, ensure_ascii=False))
assert "__QUIZ__" not in out and "__CARDS__" not in out and "__CONTENT__" not in out
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(out)
print("Wrote index.html:", len(out), "chars")
