from app.chunking.recursive import RecursiveChunkingStrategy
from app.chunking.sentence_window import SentenceWindowChunkingStrategy
from app.parsing.interfaces import ParsedDocument, ParsedElement


def _make_document(text: str) -> ParsedDocument:
    return ParsedDocument(
        document_id="doc-1",
        filename="sample.txt",
        elements=[ParsedElement(kind="text", content=text, page=1)],
    )


def test_recursive_chunking_respects_size(sample_text):
    strategy = RecursiveChunkingStrategy(chunk_size=60, chunk_overlap=10)
    chunks = strategy.chunk(_make_document(sample_text))

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.text) <= 80


def test_recursive_chunking_preserves_document_id(sample_text):
    strategy = RecursiveChunkingStrategy(chunk_size=1000, chunk_overlap=0)
    chunks = strategy.chunk(_make_document(sample_text))

    assert all(chunk.metadata.document_id == "doc-1" for chunk in chunks)


def test_sentence_window_produces_one_chunk_per_sentence(sample_text):
    strategy = SentenceWindowChunkingStrategy(window_size=1)
    chunks = strategy.chunk(_make_document(sample_text))

    sentence_count = sample_text.count(".")
    assert len(chunks) == sentence_count
