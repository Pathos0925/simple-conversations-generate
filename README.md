# SimpleConversations

Generate synthetic conversation data for training small language models, using the Anthropic Batch API with Claude Sonnet.

Built on the [SimpleStories](https://arxiv.org/abs/2504.09184) framework for parameterized synthetic text generation.

## Overview

This repo generates simple two-person conversations in `<person1> ... <person2> ...` format. The dataset is narrowly scoped with basic vocabulary, suitable for training small/interpretable LLMs.

**Two conversation modes:**
- **Storytelling (75%)** - One person tells a story to another. Uses SimpleStories machinery (themes, styles, features, personas) for narrative diversity.
- **Dialogue (25%)** - Back-and-forth conversation on a topic.

## Quick Start

```bash
# Install dependencies
pip install anthropic python-dotenv pandas unidecode tqdm

# Add your API key to .env
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Generate 100 conversations via batch API (50% off)
python run_batch.py run -n 100

# Re-process an existing batch
python run_batch.py process data/conv_batches_2026-...

# Download results from a previous batch ID
python run_batch.py download msgbatch_...
```

## Output Format

Each conversation is a single string with `<person1>` and `<person2>` tags:

```
<person1> Hi! I am Leo. I just moved here. <person2> Hello Leo! I am Mia. Welcome to our street. <person1> Thank you! Do you live in that big house? <person2> Yes, with my family. We have a dog too.
```

Output JSONL includes metadata: topic, subject, tone, mode, grammar, story_ending, character count, turn counts, etc.

## Data Diversity

Conversations are parameterized to prevent repetition:

| Parameter | Count | Description |
|-----------|-------|-------------|
| Topics | 84 | Across 12 categories (math, science, history, fiction, casual, work, technology, social, imagination, grounded, nature, practical, introductions) |
| Subjects | 120+ | Concrete nouns/objects injected to anchor each conversation |
| Tones | 20 | Positive, neutral, and negative moods |
| Grammars | 11 | Tense/structure constraints (50% of the time) |
| Starting letter | A-Z | Weighted by English frequency |
| Starting word type | 4 | Noun, adjective, adverb, preposition |
| Story endings | 3 | Happy (70%), neutral (20%), sad (10%) |

For storytelling mode, additional SimpleStories parameters:
- 68 themes (Friendship, Courage, Loss, Grief, etc.)
- 23 styles (whimsical, minimalist, tragic, etc.)
- 26 features (twist ending, foreshadowing, moral lesson, etc.)
- 23 personas (a child, a philosopher, the everyman, etc.)

## Simplicity Constraints

- Very basic vocabulary only (enforced via system prompt)
- Short sentences
- No complex ideas or nuanced explanations
- Names restricted to: Mia, Alex, Jean, Samuel, Lily, Leo, Jose, Kim, Alice, Lena, Rita, Emmanuel, Anne, Peter, Maria, Luis
- Math is basic arithmetic, science is one-sentence explanations, history covers only major events

## File Structure

| File | Purpose |
|------|---------|
| `run_batch.py` | CLI for batch generation, processing, and cost estimation |
| `generate_conversations.py` | Core logic: params, prompts, validation, normalization |
| `conversation_data.py` | All configuration: topics, subjects, tones, story params |
| `anthropic_batch.ipynb` | Notebook version of the batch pipeline |
| `text_data.py` | Original SimpleStories config (themes, styles, features) |
| `generate_stories.py` | Original SimpleStories story generation |
| `oai_batch.ipynb` | Original OpenAI batch pipeline for stories |

## Cost

Uses the Anthropic Message Batches API (50% off standard pricing).

Approximate costs with Claude Sonnet:
- 1,000 conversations: ~$6
- 10,000 conversations: ~$58
- 50,000 conversations: ~$290

Cost summary is printed after each `run_batch.py run` or `process` command.

## Post-Processing

The pipeline automatically:
1. Strips closing `</person>` tags
2. Removes preamble text before the first `<person>` tag
3. Normalizes smart quotes to ASCII
4. Filters by character count (1024-2048)
5. Filters by minimum turns (>=3)
6. Shuffles with fixed seed for reproducibility

## Credits

Based on the SimpleStories framework:

```
@article{finke2025parameterized,
  title={Parameterized Synthetic Text Generation with SimpleStories},
  author={Finke, Lennart and Dooms, Thomas and Allen, Mat and Rodriguez, Juan Diego and Nabeshima, Noa and Braun, Dan},
  journal={arXiv preprint arXiv:2504.09184},
  year={2025}
}
```
