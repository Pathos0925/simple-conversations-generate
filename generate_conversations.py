import random
import itertools
import json
import hashlib
import re
import os
import time
import anthropic
import concurrent.futures
from tqdm import tqdm
from datetime import datetime

from conversation_data import (
    topics, tones, grammars, word_types, letter_frequencies, subjects,
    CONVERSATION_MODES, ALLOWED_NAMES, NAMES_PER_CONVERSATION,
    MIN_CHARS, MAX_CHARS, MAX_TOKENS,
    topic_categories,
    story_themes, story_styles, story_features, story_personas,
    story_endings,
)

SYSTEM_PROMPT = (
    "You write simple conversations between two people using only very basic words. "
    "Mark each person's speech with <person1> and <person2> tags. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas. "
    "Not every conversation needs a happy ending. Sometimes things are sad, "
    "unresolved, or just ordinary. Reflect real life."
)


def get_random_params():
    letters = list(letter_frequencies.keys())
    weights = list(letter_frequencies.values())
    random_letter = random.choices(letters, weights=weights, k=1)[0]

    mode = random.choices(
        [m[0] for m in CONVERSATION_MODES],
        weights=[m[1] for m in CONVERSATION_MODES],
        k=1,
    )[0]

    grammar = random.choice(grammars) if random.random() < 0.5 else ""

    params = {
        "topic": random.choice(topics),
        "subject": random.choice(subjects),
        "tone": random.choice(tones),
        "mode": mode,
        "starter": random.choice([1, 2]),
        "names": random.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "initial_letter": random_letter,
        "initial_word_type": random.choice(word_types),
        "grammar": grammar,
        "min_chars": MIN_CHARS,
        "max_chars": MAX_CHARS,
    }

    ending = random.choices(
        [e[0] for e in story_endings],
        weights=[e[1] for e in story_endings],
        k=1,
    )[0]
    params["story_ending"] = ending

    if mode == "storytelling":
        params["story_theme"] = random.choice(story_themes)
        params["story_style"] = random.choice(story_styles)
        params["story_feature"] = random.choice(story_features)
        params["story_persona"] = random.choice(story_personas) if random.random() < 0.33 else ""

    return params


def iterate_params(seed=42):
    random.seed(seed)

    letter_pool = [
        letter
        for letter, frequency in letter_frequencies.items()
        for _ in range(int(frequency * 997 / 100))
    ]
    random.shuffle(letter_pool)

    mode_labels = [m[0] for m in CONVERSATION_MODES]
    mode_weights = [m[1] for m in CONVERSATION_MODES]

    combinations = list(itertools.product(topics, tones))
    random.shuffle(combinations)

    shuffled_subjects = list(subjects)
    random.shuffle(shuffled_subjects)

    assert len(grammars) % 2 != 0, "Number of grammars should be odd"

    k = 0
    while True:
        topic, tone = combinations[k % len(combinations)]
        random_letter = letter_pool[k % len(letter_pool)]
        subject = shuffled_subjects[k % len(shuffled_subjects)]

        grammar = grammars[k % len(grammars)] if k % 2 == 0 else ""

        mode = random.choices(mode_labels, weights=mode_weights, k=1)[0]

        params = {
            "topic": topic,
            "subject": subject,
            "tone": tone,
            "mode": mode,
            "starter": 1 + (k % 2),
            "names": random.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
            "initial_letter": random_letter,
            "initial_word_type": word_types[k % len(word_types)],
            "grammar": grammar,
            "min_chars": MIN_CHARS,
            "max_chars": MAX_CHARS,
        }

        ending = random.choices(
            [e[0] for e in story_endings],
            weights=[e[1] for e in story_endings],
            k=1,
        )[0]
        params["story_ending"] = ending

        if mode == "storytelling":
            params["story_theme"] = story_themes[k % len(story_themes)]
            params["story_style"] = story_styles[k % len(story_styles)]
            params["story_feature"] = story_features[k % len(story_features)]
            params["story_persona"] = story_personas[k % len(story_personas)] if k % 3 == 0 else ""

        yield params
        k += 1


def create_conversation_prompt(params):
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))

    grammar_instruction = ""
    if params["grammar"]:
        grammar_instruction = (
            f"\n- Where it fits naturally, demonstrate the use of {params['grammar']}."
        )

    ending = params.get("story_ending", "happy")
    ending_instruction = ""
    if ending == "sad":
        ending_instruction = "\n- The conversation should end on a sad or difficult note, without forcing a happy resolution"
    elif ending == "neutral":
        ending_instruction = "\n- The conversation should end in a matter-of-fact or unresolved way, not everything needs to be wrapped up neatly"

    starter = params.get("starter", 1)
    other = 2 if starter == 1 else 1
    s_tag = f"<person{starter}>"
    o_tag = f"<person{other}>"

    if params["mode"] == "storytelling":
        theme = params.get("story_theme", "")
        style = params.get("story_style", "")
        feature = params.get("story_feature", "")
        persona = params.get("story_persona", "")

        story_direction = f"The story should be about {theme}" if theme else ""
        if style:
            story_direction += f", told in a {style} way"
        story_direction += "."
        if feature:
            story_direction += f" Try to include {feature}."
        persona_instruction = ""
        if persona:
            persona_instruction = f"\n- Tell the story from the perspective of {persona}"

        user_prompt = (
            f"Write a conversation where one person tells a story to another person about "
            f"{params['topic']}. The story must involve {params['subject']}. "
            f"The conversation should be {params['tone']} in tone and "
            f"at least {params['min_chars']} characters long.\n\n"
            f"{story_direction}\n\n"
            f"Rules:\n"
            f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
            f"- Person {starter} is the storyteller. Person {other} listens and sometimes asks questions or reacts\n"
            f"- Person {other} should speak much less than Person {starter}\n"
            f"- The story should be simple enough for a young child to understand\n"
            f"- Use very basic, simple words only\n"
            f"- Keep all explanations to one or two short sentences\n"
            f"- No big or unusual words\n"
            f"- If using names in the story, pick from: {names_str}\n"
            f"- Start the conversation with {params['initial_word_type']} that begins with "
            f"the letter {params['initial_letter']}"
            f"{grammar_instruction}"
            f"{persona_instruction}"
            f"{ending_instruction}\n\n"
            f"Format example:\n"
            f"{s_tag} Want to hear a story? {o_tag} Yes please! {s_tag} Once there "
            f"was a little cat who lived near a big tree...\n\n"
            f"Write the conversation now:"
        )
    else:
        user_prompt = (
            f"Write a conversation between two people about {params['topic']}. "
            f"The conversation must involve {params['subject']}. "
            f"The conversation should be {params['tone']} in tone and at least "
            f"{params['min_chars']} characters long.\n\n"
            f"Rules:\n"
            f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
            f"- Person {starter} speaks first\n"
            f"- Use very basic, simple words only\n"
            f"- Keep all explanations to one or two short sentences\n"
            f"- No big or unusual words\n"
            f"- If using names, pick from: {names_str}\n"
            f"- Start the conversation with {params['initial_word_type']} that begins with "
            f"the letter {params['initial_letter']}"
            f"{grammar_instruction}"
            f"{ending_instruction}\n\n"
            f"Format example:\n"
            f"{s_tag} Hello! Do you want to talk about something? {o_tag} Sure! "
            f"What should we talk about?\n\n"
            f"Write the conversation now:"
        )

    return SYSTEM_PROMPT, user_prompt


def validate_conversation(text):
    errors = []

    p1_count = text.count("<person1>")
    p2_count = text.count("<person2>")

    if p1_count == 0:
        errors.append("missing_person1_tag")
    if p2_count == 0:
        errors.append("missing_person2_tag")
    if p1_count + p2_count < 3:
        errors.append("too_few_turns")

    char_count = len(text)
    word_count = len(text.split())

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "person1_turns": p1_count,
        "person2_turns": p2_count,
        "total_turns": p1_count + p2_count,
        "character_count": char_count,
        "word_count": word_count,
    }


def normalize_text(text):
    table = str.maketrans({
        "\u201c": "\"",
        "\u201d": "\"",
        "\u2018": "'",
        "\u2019": "'",
        "\u2014": "-",
        "\u2026": "...",
    })
    text = text.translate(table)

    text = re.sub(r"</person[12]>", "", text)

    first_tag = re.search(r"<person[12]>", text)
    if first_tag:
        text = text[first_tag.start():]

    return text.strip()


def process_conversation(completion, params, gen_model):
    completion = normalize_text(completion.strip())
    metrics = validate_conversation(completion)

    generation_id = hashlib.md5(completion.encode()).hexdigest()

    return {
        "generation_id": generation_id,
        "conversation": completion,
        "model": gen_model,
        "topic": params.get("topic", ""),
        "subject": params.get("subject", ""),
        "topic_category": topic_categories.get(params.get("topic", ""), ""),
        "tone": params.get("tone", ""),
        "mode": params.get("mode", ""),
        "grammar": params.get("grammar", ""),
        "initial_word_type": params.get("initial_word_type", ""),
        "initial_letter": params.get("initial_letter", ""),
        "story_ending": params.get("story_ending", ""),
        "story_theme": params.get("story_theme", ""),
        "story_style": params.get("story_style", ""),
        "story_feature": params.get("story_feature", ""),
        "story_persona": params.get("story_persona", ""),
        **metrics,
    }


def generate_content(gen_model, system_prompt, user_prompt):
    client = anthropic.Anthropic()
    completion = client.messages.create(
        model=gen_model,
        max_tokens=MAX_TOKENS,
        top_p=0.9,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return completion.content[0].text


class RateLimitException(Exception):
    pass


def generate_conversation(gen_model, params):
    system_prompt, user_prompt = create_conversation_prompt(params)
    try:
        completion = generate_content(gen_model, system_prompt, user_prompt)
        return process_conversation(completion, params, gen_model)
    except anthropic.RateLimitError as e:
        raise RateLimitException(e)


def worker_thread(gen_model, params, formatted_time):
    while True:
        try:
            result = generate_conversation(gen_model, params)
            filename = f"data/conversations-{gen_model}-{formatted_time}.jsonl"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(f"[{result['mode']}] {result['topic']} | "
                  f"chars={result['character_count']} turns={result['total_turns']} "
                  f"valid={result['valid']}")
            return result
        except RateLimitException:
            print("Rate limit hit, backing off for 5 seconds...")
            time.sleep(5)
            continue


def main(num_completions, num_threads=20, model="claude-sonnet-4-6"):
    if not os.path.exists("data"):
        os.makedirs("data")
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    random.seed(42)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_idx = {
            executor.submit(worker_thread, model, get_random_params(), formatted_time): i
            for i in range(num_completions)
        }

        for future in tqdm(
            concurrent.futures.as_completed(future_to_idx),
            total=num_completions,
            desc="Generating conversations",
        ):
            try:
                future.result()
            except Exception as e:
                print(f"Generation failed: {e}")


if __name__ == "__main__":
    NUM_COMPLETIONS = 2
    main(NUM_COMPLETIONS, num_threads=2, model="claude-sonnet-4-6")
