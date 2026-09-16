"""One activity menu for the Flask pages and native activity workspace."""
from utils.i18n import translate_ui


def activity_navigation(language="en"):
    def link(page, href, key, boost=True):
        return {"page": page, "href": href, "label": translate_ui(key, language), "boost": boost}

    return {
        "title": translate_ui("nav.activity_tools", language),
        "more": translate_ui("nav.more_tools", language),
        "activities": [
            link("native_flashcards", "/post/#flashcards", "nav.flashcards", False),
            link("comprehension", "/comprehension", "nav.comprehension"),
            link("writing", "/writing", "nav.writing"),
            link("lessons", "/lessons", "nav.lessons"),
            link("word_jumble", "/word_jumble", "nav.word_jumble"),
            link("sentences", "/sentences", "nav.sentences"),
            link("vocab", "/vocab", "nav.vocab"),
        ],
        "tools": [link("flashcards", "/", "nav.anki_tools")],
    }
