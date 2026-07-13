#!/usr/bin/env python3
"""Assemble index.html and azure-study-guide.md from parts."""
import json, io, os
import markdown

D = "/sessions/upbeat-practical-goldberg/mnt/outputs/src"
OUT = "/sessions/upbeat-practical-goldberg/mnt/outputs"

# 1. Assemble markdown study guide
md_parts = []
for p in ["md_part1.md", "md_part2.md", "md_part3.md", "md_part4.md", "md_part5.md", "md_part6.md", "md_part7.md", "md_part8.md"]:
    md_parts.append(open(os.path.join(D, p), encoding="utf-8").read())
md_body = "\n".join(md_parts)

# Load quiz + cards
quiz = []
for p in ["quiz_a.json", "quiz_b.json", "quiz_c.json", "quiz_d.json", "quiz_e.json", "quiz_f.json", "quiz_g.json"]:
    quiz += json.load(open(os.path.join(D, p), encoding="utf-8"))
cards = []
for p in ["cards_a.json", "cards_b.json", "cards_c.json", "cards_d.json"]:
    cards += json.load(open(os.path.join(D, p), encoding="utf-8"))

print(f"Quiz questions: {len(quiz)}  Flashcards: {len(cards)}")

# Validate quiz entries
cats = {}
for q in quiz:
    typ = q.get("t", "single")
    if typ == "single":
        assert len(q["o"]) >= 2 and 0 <= q["a"] < len(q["o"]), q["q"][:50]
    elif typ == "multi":
        assert isinstance(q["a"], list) and all(0 <= i < len(q["o"]) for i in q["a"]), q["q"][:50]
    elif typ == "order":
        assert len(q["o"]) >= 3 and "a" not in q, q["q"][:50]
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
buf.write("\n---\n\n## 17. Practice Questions (Q&A)\n\n")
buf.write(f"{len(quiz)} exam-style questions. Answers immediately follow each question.\n")
cur = None
n = 0
for q in quiz:
    if q["c"] != cur:
        cur = q["c"]
        buf.write(f"\n### {CATNAMES.get(cur, cur)}\n\n")
    n += 1
    typ = q.get("t", "single")
    tag = {"multi": " *(multi-select)*", "order": " *(ordering)*"}.get(typ, "")
    diff = {1: " *[Easy]*", 2: " *[Medium]*", 3: " *[Hard]*"}.get(q.get("d"), "")
    buf.write(f"**Q{n}.{tag}{diff} {q['q']}**\n\n")
    if typ == "order":
        import random as _r
        idx = list(range(len(q["o"])))
        _r.Random(n).shuffle(idx)
        for k, i in enumerate(idx):
            buf.write(f"- {chr(65+k)}. {q['o'][i]}\n")
        correct = " → ".join(chr(65+idx.index(i)) for i in range(len(q["o"])))
        buf.write(f"\n> **Answer: {correct}.** {q['e']}\n\n")
    else:
        for i, o in enumerate(q["o"]):
            buf.write(f"- {chr(65+i)}. {o}\n")
        if typ == "multi":
            ans = ", ".join(chr(65+i) for i in sorted(q["a"]))
            buf.write(f"\n> **Answer: {ans}.** {q['e']}\n\n")
        else:
            buf.write(f"\n> **Answer: {chr(65+q['a'])}.** {q['e']}\n\n")

buf.write("\n---\n\n## 18. Flashcards\n\n")
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

# 3. Build index.html (study content = sections 1-7 only; quizzes/cards are interactive)
html_content = markdown.markdown(md_body, extensions=["tables", "fenced_code", "sane_lists"])
tpl = open(os.path.join(D, "template.html"), encoding="utf-8").read()
out = tpl.replace("__CONTENT__", html_content)
out = out.replace("__QUIZ__", json.dumps(quiz, ensure_ascii=False))
out = out.replace("__CARDS__", json.dumps(cards, ensure_ascii=False))
assert "__QUIZ__" not in out and "__CARDS__" not in out and "__CONTENT__" not in out
assert "</script></script>" not in out
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(out)
print("Wrote index.html:", len(out), "chars")
