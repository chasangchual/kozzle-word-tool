# Kozzle Word Tools

A Python project for processing Korean documents, extracting nouns, generating sentences, and creating audio files.

## Features

1. **Document Processing**: Extract text from various formats (TXT, PDF, MS Word)
2. **Korean Noun Extraction**: Uses Komoran/Naver NLP to extract meaningful nouns
3. **Sentence Generation**: Uses Ollama via LangChain to generate 3 sentences per noun
4. **Audio Generation**: Creates audio files with the noun and sentences

## Installation

```bash
pip install -r requirements.txt
```

For Korean language support, you may need Java for konlpy:

```bash
# On macOS with Homebrew
brew install openjdk

# On Ubuntu/Debian
apt-get install default-jdk
```

## Usage

```python
from word_tools import DocumentProcessor

processor = DocumentProcessor(
    ollama_model="llama3:ko",  # or your preferred model
    output_dir="./output"
)

# Process a single document
processor.process_document("document.pdf")

# Or process all documents in a directory
processor.process_directory("./documents")
```

## Output

```json
{
  "id": 1,
  "word": "사과",
  "sentences": [
    "사과는 건강에 좋은 과일입니다.",
    "빨간 사과를 먹으면 비타민을 섭취할 수 있습니다.",
    "사과는 겨울철 간식으로 인기가 많습니다."
  ]
}
```
