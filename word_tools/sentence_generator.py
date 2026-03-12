"""Sentence generator using Ollama via LangChain."""

from typing import List

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


class SentenceGenerator:
    """Generate sentences using a language model."""

    def __init__(self, model: str = "exaone3.5:latest"):
        """
        Initialize the sentence generator.

        Args:
            model: Ollama model name (e.g., "llama3:ko", "megrez-3b-ita")
        """
        self.model = model
        self.llm = ChatOllama(
            model=model,
            temperature=0.7,
            max_tokens=512,
        )

        # Korean prompt template for sentence generation
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """당신은 한국어로 유능한 문장을 생성하는 어시스턴트입니다.
                    주어진 명사를 사용하여 자연스러운 한국어 문장 3개를 생성하세요.
                    각 문장은 다음과 같은 조건을 만족해야 합니다:
                    1. 주어로 해당 명사를 사용하거나 자연스럽게 포함해야 함
                    2. 문법적으로 올바른 문장
                    3. 일상적인 표현이거나 설명적인 문장
                    4. 각 문장은 10자에서 30자 사이가 적당함

                    응답은 JSON 형식으로만 제공하세요:
                    {{
                        "sentences": ["문장1", "문장2", "문장3"]
                    }}""",
                ),
                (
                    "human",
                    "다음 명사를 사용하여 한국어 문장 3개를 생성하세요: {word}",
                ),
            ]
        )

        self.chain = self.prompt | self.llm

    def generate_sentences(self, word: str) -> List[str]:
        """
        Generate 3 sentences using the given word.

        Args:
            word: The word (usually a noun) to use in sentences

        Returns:
            List of 3 generated sentences
        """
        try:
            response = self.chain.invoke({"word": word})

            # Parse the response to extract sentences
            content = response.content

            # Try to parse JSON from response
            import json

            try:
                # Try to parse as JSON directly
                data = json.loads(content)
                return data.get("sentences", [])
            except json.JSONDecodeError:
                # If not valid JSON, try to extract sentences from text
                sentences = []
                # Look for sentence patterns
                for line in content.split("\n"):
                    line = line.strip().strip("- ").strip('"').strip(",")
                    if line and len(line) > 5:
                        sentences.append(line)
                    if len(sentences) >= 3:
                        break

                # Fallback: generate simple sentences if model output is malformed
                if len(sentences) < 3:
                    sentences = [
                        f"{word}에 대해 알아보겠습니다.",
                        f"{word}는 중요한 개념입니다.",
                        f"{word}를 잘 이해해보겠습니다.",
                    ]

                return sentences

        except Exception as e:
            print(f"Error generating sentences for '{word}': {e}")
            # Return fallback sentences
            return [
                f"{word}에 대해 알아보겠습니다.",
                f"{word}는 중요한 개념입니다.",
                f"{word}를 잘 이해해보겠습니다.",
            ]


if __name__ == "__main__":
    # Test the sentence generator
    generator = SentenceGenerator()
    test_word = "사과"
    sentences = generator.generate_sentences(test_word)
    print(f"Word: {test_word}")
    for i, s in enumerate(sentences, 1):
        print(f"{i}. {s}")
