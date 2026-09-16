import pymorphy3
import json

def debug_word(word, morph):
    parses = morph.parse(word)
    results = []
    for parse in parses:
        results.append({
            "word": word,
            "lemma": parse.normal_form,
            "pos": parse.tag.POS,
            "score": parse.score,
            "tags": str(parse.tag),
            "is_lemma": parse.word == parse.normal_form
        })
    return results

def main():
    morph = pymorphy3.MorphAnalyzer()
    words = [
        "холодный", "холодно",
        "счастье",
        "фрукт", "фрукты",
        "газированный", "газировать",
        "ушёл", "уйти",
        "гольфы", "гольф",
        "шлёпки"
    ]
    all_results = []
    for word in words:
        all_results.extend(debug_word(word, morph))
    
    print(json.dumps(all_results, ensure_ascii=False, indent=2))
    
    with open("/tmp/pymorphy_debug.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()