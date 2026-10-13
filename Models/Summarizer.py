"""Summarize text of any length.

Use as a module:
    from summarize import summarize
    print(summarize(text))

    from summarize import load_document
    print(summarize(load_document("paper.pdf")))

Or from the command line:
    python summarize.py paper.pdf
    python summarize.py paper.pdf -o summary.txt
    some_program | python summarize.py   (plain text on stdin)
"""

import argparse
import re
import sys
from pathlib import Path

from transformers import pipeline

MODEL = "sshleifer/distilbart-cnn-12-6"
MAX_INPUT_TOKENS = 900  # model limit is ~1024; leave headroom for special tokens

_summarizer = None


def _get_summarizer():
    """Load the model once, on first use."""
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline("summarization", model=MODEL)
    return _summarizer


def _count_tokens(text):
    tok = _get_summarizer().tokenizer
    return len(tok.encode(text, add_special_tokens=False))


def _chunk_text(text, max_tokens=MAX_INPUT_TOKENS):
    """Split text into chunks under max_tokens, breaking on sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, current, current_tokens = [], [], 0

    for sentence in sentences:
        n = _count_tokens(sentence)
        if current and current_tokens + n > max_tokens:
            chunks.append(" ".join(current))
            current, current_tokens = [], 0
        current.append(sentence)
        current_tokens += n

    if current:
        chunks.append(" ".join(current))
    return chunks


def _summarize_chunk(chunk, max_length, min_length):
    # Don't ask for a summary longer than the input
    n = _count_tokens(chunk)
    max_len = min(max_length, max(int(n * 0.8), 10))
    min_len = min(min_length, max_len - 1)
    result = _get_summarizer()(
        chunk, max_length=max_len, min_length=min_len, do_sample=False, truncation=True
    )
    return result[0]["summary_text"]


def _load_pdf(path):
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    text = re.sub(r"-\n(?=[a-z])", "", text)  # rejoin words hyphenated across lines
    text = re.sub(r"\s*\n\s*", " ", text)  # line breaks -> spaces
    text = re.sub(r"\s{2,}", " ", text)
    if not text.strip():
        raise ValueError(f"No text found in {path}. It may be a scanned PDF that needs OCR.")
    return text.strip()


def load_document(path):
    """Read a PDF file and return plain text."""
    if Path(path).suffix.lower() != ".pdf":
        raise ValueError(f"Unsupported file type: {Path(path).suffix}. Only PDFs are supported.")
    return _load_pdf(path)


def summarize(text, max_length=120, min_length=30):
    """Return a summary of `text`, however long it is.

    Long text is split into chunks, each chunk is summarized, and the
    combined partial summaries are summarized again until they fit in one pass.
    """
    text = text.strip()
    if not text:
        return ""

    chunks = _chunk_text(text)
    while len(chunks) > 1:
        partials = [_summarize_chunk(c, 80, 20) for c in chunks]
        chunks = _chunk_text(" ".join(partials))

    return _summarize_chunk(chunks[0], max_length, min_length)


def main():
    parser = argparse.ArgumentParser(description="Summarize a PDF (or plain text from stdin).")
    parser.add_argument("input", nargs="?", help="input PDF file (default: plain text on stdin)")
    parser.add_argument("-o", "--output", help="write summary to this file (default: stdout)")
    parser.add_argument("--max-length", type=int, default=120)
    parser.add_argument("--min-length", type=int, default=30)
    args = parser.parse_args()

    if args.input:
        text = load_document(args.input)
    else:
        text = sys.stdin.read()

    if not text.strip():
        sys.exit("No input text provided.")

    summary = summarize(text, args.max_length, args.min_length)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary + "\n")
    else:
        print(summary)


if __name__ == "__main__":
    main()