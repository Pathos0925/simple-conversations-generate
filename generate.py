import random
import hashlib
import json
import os
import time
import anthropic
import concurrent.futures
from tqdm import tqdm
from datetime import datetime

from formats import FORMAT_NAMES, FORMAT_WEIGHTS, get_format
from formats.shared import (
    letter_frequencies, word_types, grammars, tones, subjects,
    story_endings, MIN_CHARS, MAX_CHARS, MAX_TOKENS,
)


def get_random_params(rng=None):
    rng = rng or random

    if rng.random() < 0.2:
        letters = list(letter_frequencies.keys())
        weights = list(letter_frequencies.values())
        random_letter = rng.choices(letters, weights=weights, k=1)[0]
        random_word_type = rng.choice(word_types)
    else:
        random_letter = ""
        random_word_type = ""

    format_name = rng.choices(FORMAT_NAMES, weights=FORMAT_WEIGHTS, k=1)[0]
    fmt = get_format(format_name)

    grammar = rng.choice(grammars) if rng.random() < 0.5 else ""

    ending = rng.choices(
        [e[0] for e in story_endings],
        weights=[e[1] for e in story_endings],
        k=1,
    )[0]

    params = {
        "format": format_name,
        "topic": rng.choice(fmt.TOPICS),
        "topic_category": "",
        "subject": rng.choice(subjects),
        "tone": rng.choice(tones),
        "initial_letter": random_letter,
        "initial_word_type": random_word_type,
        "grammar": grammar,
        "story_ending": ending,
        "introduce_names": rng.random() < 0.33,
        "min_chars": MIN_CHARS,
        "max_chars": MAX_CHARS,
    }
    params["topic_category"] = fmt.TOPIC_CATEGORIES.get(params["topic"], "")
    params.update(fmt.get_extra_params(rng.randint(0, 9999), rng=rng))

    return params


def iterate_params(seed=42):
    rng = random.Random(seed)

    letter_pool = [
        letter
        for letter, frequency in letter_frequencies.items()
        for _ in range(int(frequency * 997 / 100))
    ]
    rng.shuffle(letter_pool)

    shuffled_subjects = list(subjects)
    rng.shuffle(shuffled_subjects)

    shuffled_tones = list(tones)
    rng.shuffle(shuffled_tones)

    shuffled_grammars = list(grammars)
    rng.shuffle(shuffled_grammars)

    format_order = list(FORMAT_NAMES)
    rng.shuffle(format_order)

    k = 0
    while True:
        if k > 0 and k % len(format_order) == 0:
            rng.shuffle(format_order)
        format_name = format_order[k % len(format_order)]
        fmt = get_format(format_name)

        topic = fmt.TOPICS[k % len(fmt.TOPICS)]
        topic_category = fmt.TOPIC_CATEGORIES.get(topic, "")

        if k % 5 == 0:
            random_letter = letter_pool[k % len(letter_pool)]
            random_word_type = word_types[k % len(word_types)]
        else:
            random_letter = ""
            random_word_type = ""
        subject = shuffled_subjects[k % len(shuffled_subjects)]
        grammar = shuffled_grammars[k % len(shuffled_grammars)] if k % 2 == 0 else ""

        formats_with_endings = {"story", "conversation", "summary", "letter", "diary", "assistant"}
        if format_name in formats_with_endings:
            ending = rng.choices(
                [e[0] for e in story_endings],
                weights=[e[1] for e in story_endings],
                k=1,
            )[0]
        else:
            ending = ""

        params = {
            "format": format_name,
            "topic": topic,
            "topic_category": topic_category,
            "subject": subject,
            "tone": shuffled_tones[k % len(shuffled_tones)],
            "initial_letter": random_letter,
            "initial_word_type": random_word_type,
            "grammar": grammar,
            "story_ending": ending,
            "introduce_names": k % 3 == 0,
            "min_chars": MIN_CHARS,
            "max_chars": MAX_CHARS,
        }

        params.update(fmt.get_extra_params(k, rng=rng))

        yield params
        k += 1


def create_prompt(params):
    fmt = get_format(params["format"])
    return fmt.create_prompt(params)


def process_result(completion, params, gen_model):
    fmt = get_format(params["format"])
    completion = fmt.normalize(completion.strip())
    metrics = fmt.validate(completion)

    generation_id = hashlib.md5(completion.encode()).hexdigest()

    result = {
        "generation_id": generation_id,
        "text": completion,
        "format": params["format"],
        "model": gen_model,
        "topic": params.get("topic", ""),
        "subject": params.get("subject", ""),
        "topic_category": params.get("topic_category", ""),
        "tone": params.get("tone", ""),
        "grammar": params.get("grammar", ""),
        "initial_word_type": params.get("initial_word_type", ""),
        "initial_letter": params.get("initial_letter", ""),
        "story_ending": params.get("story_ending", ""),
        **metrics,
    }

    format_keys = set(result.keys())
    skip_keys = {"min_chars", "max_chars", "names", "format", "topic", "subject",
                 "topic_category", "tone", "grammar", "initial_word_type",
                 "initial_letter", "story_ending"}
    for key, value in params.items():
        if key not in format_keys and key not in skip_keys:
            result[key] = value

    return result


class RateLimitException(Exception):
    pass


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


def generate_single(gen_model, params):
    system_prompt, user_prompt = create_prompt(params)
    try:
        completion = generate_content(gen_model, system_prompt, user_prompt)
        return process_result(completion, params, gen_model)
    except anthropic.RateLimitError as e:
        raise RateLimitException(e)


def worker_thread(gen_model, params, formatted_time):
    while True:
        try:
            result = generate_single(gen_model, params)
            filename = f"data/generations-{gen_model}-{formatted_time}.jsonl"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(f"[{result['format']}] {result['topic']} | "
                  f"chars={result['character_count']} valid={result['valid']}")
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

    rng = random.Random(42)
    all_params = [get_random_params(rng) for _ in range(num_completions)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_idx = {
            executor.submit(worker_thread, model, p, formatted_time): i
            for i, p in enumerate(all_params)
        }

        for future in tqdm(
            concurrent.futures.as_completed(future_to_idx),
            total=num_completions,
            desc="Generating texts",
        ):
            try:
                future.result()
            except Exception as e:
                print(f"Generation failed: {e}")


if __name__ == "__main__":
    NUM_COMPLETIONS = 2
    main(NUM_COMPLETIONS, num_threads=2, model="claude-sonnet-4-6")
