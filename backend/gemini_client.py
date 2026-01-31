from google import genai

PROJECT_ID = "effortless-cat-461509-s6"
LOCATION = "us-central1"

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

MODEL_NAME = "gemini-2.5-flash"   # or "gemini-3-pro-preview"


def ask_gemini_batched(question: str, chunks: list):
    prompts = []

    for chunk in chunks:
        prompts.append(
            f"""
You are a helpful assistant.
Answer the question ONLY using the context below.

QUESTION:
{question}

CONTEXT:
{chunk['text']}
"""
        )

    combined_prompt = "\n\n".join(prompts)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=combined_prompt
    )

    answer_text = response.text if response and response.text else ""

    tokens_used = {
        "prompt_tokens": len(combined_prompt.split()),
        "candidates_tokens": len(answer_text.split()),
        "total_tokens": len(combined_prompt.split()) + len(answer_text.split())
    }

    return answer_text, tokens_used, len(prompts)