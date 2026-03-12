"""Document processor for Korean text extraction and processing."""

import json
import os
import re
from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pypdf import PdfReader
from docx import Document
from konlpy.tag import Komoran

from .sentence_generator import SentenceGenerator
from .audio_generator import AudioGenerator


class DocumentProcessor:
    """Process Korean documents to extract nouns and generate content."""

    def __init__(
        self,
        ollama_model: str = "exaone3.5:latest",
        output_dir: str = "./output",
        extract_noun_limit: int = 20,
    ):
        """
        Initialize the document processor.

        Args:
            ollama_model: Ollama model name (e.g., "llama3:ko", "megrez-3b-ita")
            output_dir: Directory to save output files
            extract_noun_limit: Maximum number of nouns to extract per document
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Korean noun extractor using Komoran
        self.komoran = Komoran()

        # Sentence generator using Ollama via LangChain
        self.sentence_generator = SentenceGenerator(model=ollama_model)

        # Audio generator
        self.audio_generator = AudioGenerator(output_dir=str(self.output_dir))

        self.extract_noun_limit = extract_noun_limit

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various document formats."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".txt":
            return self._read_txt(path)
        elif ext == ".pdf":
            return self._read_pdf(path)
        elif ext == ".docx":
            return self._read_docx(path)
        elif ext == ".epub":
            return self._read_epub(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _read_txt(self, path: Path) -> str:
        """Read text from a text file, trying common Korean encodings."""
        for encoding in ("utf-8", "euc-kr", "cp949"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        # Last resort: use cp949 ignoring undecodable bytes
        with open(path, "r", encoding="cp949", errors="ignore") as f:
            return f.read()

    def _read_pdf(self, path: Path) -> str:
        """Read text from PDF file."""
        reader = PdfReader(str(path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    def _read_docx(self, path: Path) -> str:
        """Read text from MS Word document."""
        doc = Document(str(path))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text

    def _read_epub(self, path: Path) -> str:
        """Read text from EPUB file."""
        book = epub.read_epub(str(path))
        texts = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            texts.append(soup.get_text())
        return "\n".join(texts)

    def extract_nouns(self, text: str) -> list[str]:
        """Extract nouns from Korean text, chunking large inputs for Komoran."""
        chunk_size = 5000
        nouns = []
        seen = set()

        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            try:
                pos_tags = self.komoran.pos(chunk)
            except Exception:
                continue

            for word, tag in pos_tags:
                if tag.startswith("N") and len(word) > 1 and word not in seen:
                    seen.add(word)
                    nouns.append(word)

            if len(nouns) >= self.extract_noun_limit:
                break

        return nouns[: self.extract_noun_limit]

    def process_document(
        self, file_path: str, output_filename: Optional[str] = None
    ) -> list[dict]:
        """
        Process a single document and generate output.

        Args:
            file_path: Path to the document file
            output_filename: Optional custom output filename (without extension)

        Returns:
            List of result dictionaries with id, word, and sentences
        """
        print(f"Processing: {file_path}")

        # Extract text
        text = self.extract_text_from_file(file_path)
        print(f"Extracted text length: {len(text)} characters")

        # Extract nouns
        nouns = self.extract_nouns(text)
        print(f"Extracted {len(nouns)} nouns")

        results = []
        for i, noun in enumerate(nouns, start=1):
            print(f"Processing noun {i}/{len(nouns)}: {noun}")

            # Generate 3 sentences
            sentences = self.sentence_generator.generate_sentences(noun)

            result = {
                "id": i,
                "word": noun,
                "sentences": sentences,
            }
            results.append(result)

            # Generate audio for this entry
            audio_file = self.audio_generator.generate_audio(noun, sentences)
            if audio_file:
                result["audio_file"] = audio_file

        # Save results to JSON
        if output_filename is None:
            output_filename = Path(file_path).stem

        json_path = self.output_dir / f"{output_filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Saved results to: {json_path}")
        return results

    def process_directory(self, directory: str) -> list[dict]:
        """
        Process all supported files in a directory.

        Args:
            directory: Path to directory containing documents

        Returns:
            Combined list of all results from all documents
        """
        directory_path = Path(directory)
        supported_extensions = {".txt", ".pdf", ".docx", ".epub"}

        all_results = []
        for file_path in sorted(directory_path.iterdir()):
            if file_path.suffix.lower() in supported_extensions:
                results = self.process_document(str(file_path))
                all_results.extend(results)

        return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Process Korean documents and generate sentence data"
    )
    parser.add_argument(
        "input", help="Input file or directory path"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./output",
        help="Output directory for JSON and audio files",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="exaone3.5:latest",
        help="Ollama model name",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=20,
        help="Maximum number of nouns to extract",
    )

    args = parser.parse_args()

    processor = DocumentProcessor(
        ollama_model=args.model,
        output_dir=args.output,
        extract_noun_limit=args.limit,
    )

    input_path = Path(args.input)
    if input_path.is_file():
        processor.process_document(str(input_path))
    elif input_path.is_dir():
        processor.process_directory(str(input_path))
    else:
        print(f"Error: Path not found: {args.input}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process Korean documents and generate sentence data"
    )
    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument(
        "-o",
        "--output",
        default="./output",
        help="Output directory for JSON and audio files",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="exaone3.5:latest",
        help="Ollama model name",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=20,
        help="Maximum number of nouns to extract",
    )

    args = parser.parse_args()

    processor = DocumentProcessor(
        ollama_model=args.model,
        output_dir=args.output,
        extract_noun_limit=args.limit,
    )

    input_path = Path(args.input)
    if input_path.is_file():
        processor.process_document(str(input_path))
    elif input_path.is_dir():
        processor.process_directory(str(input_path))
    else:
        print(f"Error: Path not found: {args.input}")
