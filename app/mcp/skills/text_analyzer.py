"""
Text statistics analyzer skill.

Computes document-level metrics: word/sentence/paragraph counts, unique
words, average word length, and basic readability indicators.
"""

from __future__ import annotations

from app.mcp.skills.base import Skill


class TextAnalyzerSkill(Skill):
    name = "text_analyzer"
    description = "Analyze text for word count, readability, and linguistic statistics."

    async def run(self, text: str) -> dict:
        """Analyze text and return statistics."""
        if not text or not text.strip():
            return {"error": "Text is empty"}

        text = text.strip()
        words = text.split()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        unique_words = set(w.lower() for w in words)
        word_lengths = [len(w) for w in words]

        avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0

        return {
            "character_count": len(text),
            "word_count": len(words),
            "unique_word_count": len(unique_words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "vocabulary_richness": round(len(unique_words) / len(words), 2) if words else 0,
        }
