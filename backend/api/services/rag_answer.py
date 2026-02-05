import re

def build_context(results):
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    items = []
    for doc, meta, dist in zip(docs, metas, dists):
        items.append({
            "text": doc or "",
            "page": meta.get("page"),
            "distance": dist
        })

    # Lower distance = better match
    items.sort(key=lambda x: x["distance"] if x["distance"] is not None else 999999)
    return items


def _split_sentences(text):
    text = (text or "").replace("\n", " ").strip()
    return re.split(r'(?<=[.!?])\s+', text)


def _keywords(question):
    stop = {
        "what","is","the","a","an","of","about","does","do","in","on","to","and",
        "how","many","pages","pdf","have","has","tell","me","explain","define"
    }
    words = re.findall(r"[a-zA-Z]+", question.lower())
    return {w for w in words if w not in stop and len(w) > 2}


def answer_from_context(question, items):
    if not items:
        return "I couldn't find that in the PDF.", []

    keywords = _keywords(question)
    best_text = items[0]["text"]

    sentences = _split_sentences(best_text)
    scored = []

    for s in sentences:
        score = sum(1 for k in keywords if k in s.lower())
        scored.append((score, s))

    scored.sort(reverse=True, key=lambda x: x[0])

    if scored and scored[0][0] > 0:
        answer = scored[0][1]
    else:
        answer = sentences[0] if sentences else "I couldn't find that in the PDF."

    sources = [
        {
            "page": items[0]["page"],
            "snippet": best_text[:300].replace("\n", " ")
        }
    ]

    return answer, sources
