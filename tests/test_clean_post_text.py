"""
test_clean_post_text.py
───────────────────────
Verifies that clean_llm_post_text() strips all chatbot conversational preambles,
bot greetings, code fences, and intro labels from drafted posts.
"""

import os
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from core.llm_processor import clean_llm_post_text

TEST_CASES = [
    (
        "Here's the post:\n\nGoogle Photos launched a new virtual closet feature today.\n\nIt runs entirely on-device.",
        "Google Photos launched a new virtual closet feature today.\n\nIt runs entirely on-device."
    ),
    (
        "Here is the post:\n\nAnthropic updated their Claude 3.5 Sonnet model benchmarks.",
        "Anthropic updated their Claude 3.5 Sonnet model benchmarks."
    ),
    (
        "Key developments in AI infrastructure:\n\nNVIDIA revealed a new Blackwell server cluster architecture.",
        "NVIDIA revealed a new Blackwell server cluster architecture."
    ),
    (
        "Sure, here is the LinkedIn post:\n\nMeta continues its open weights strategy with Llama 3.2.",
        "Meta continues its open weights strategy with Llama 3.2."
    ),
    (
        "Certainly! Here's a draft:\n\nOpenAI expands its real-time voice API.",
        "OpenAI expands its real-time voice API."
    ),
    (
        "```markdown\nHere's your post:\n\nGoogle DeepMind publishes new research on multi-agent reasoning.\n```",
        "Google DeepMind publishes new research on multi-agent reasoning."
    ),
    (
        "Post:\n\nCohere releases Command R+ fine-tuning.",
        "Cohere releases Command R+ fine-tuning."
    ),
    (
        "\"Amazon Web Services announces custom silicon chips.\"",
        "Amazon Web Services announces custom silicon chips."
    )
]

def main():
    print("═" * 60)
    print("TESTING POST TEXT CLEANING & BOT PREAMBLE STRIPPING")
    print("═" * 60)
    
    for idx, (raw_input, expected_clean) in enumerate(TEST_CASES, 1):
        cleaned = clean_llm_post_text(raw_input)
        assert cleaned == expected_clean, f"Test {idx} failed!\nExpected:\n{expected_clean}\nGot:\n{cleaned}"
        print(f"   ✅ Test {idx} passed: Stripped '{raw_input.splitlines()[0][:35]}...'")

    print("\n" + "═" * 60)
    print("🎉 ALL PREAMBLE STRIPPING TESTS PASSED SUCCESSFULLY!")
    print("═" * 60)

if __name__ == "__main__":
    main()
