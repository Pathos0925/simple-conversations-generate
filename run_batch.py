import argparse
import json
import os
import re
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import anthropic
import pandas as pd
from unidecode import unidecode

from generate_conversations import (
    create_conversation_prompt,
    iterate_params,
    process_conversation,
)
from conversation_data import MAX_TOKENS


MODEL_PARAMETERS = {"top_p": 0.9}

# Anthropic batch API pricing (50% off standard) per million tokens
BATCH_PRICING = {
    "claude-sonnet-4-6": {"input": 1.50, "output": 7.50},
    "claude-sonnet-4-5-20250514": {"input": 1.50, "output": 7.50},
    "claude-haiku-4-5-20251001": {"input": 0.40, "output": 2.00},
}


def get_batch_requests(num_completions, model, offset=0):
    params_iterator = iterate_params()
    for _ in range(offset):
        next(params_iterator)

    requests = []
    params_lookup = {}
    for i in range(num_completions):
        params = next(params_iterator)
        system_prompt, user_prompt = create_conversation_prompt(params)
        custom_id = f"conv_{i + offset}"

        params_lookup[custom_id] = params
        requests.append({
            "custom_id": custom_id,
            "params": {
                "model": model,
                "max_tokens": MAX_TOKENS,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
                **MODEL_PARAMETERS,
            },
        })

    return requests, params_lookup


def submit_and_poll(client, requests, directory, batch_number):
    print(f"Submitting batch {batch_number} with {len(requests)} requests...")
    message_batch = client.messages.batches.create(requests=requests)
    batch_id = message_batch.id

    with open(os.path.join(directory, "batch_ids.txt"), "a") as f:
        f.write(f"{batch_id}\n")

    while True:
        status = client.messages.batches.retrieve(batch_id)
        counts = status.request_counts
        print(
            f"  [{status.processing_status}] "
            f"succeeded={counts.succeeded} errored={counts.errored} "
            f"processing={counts.processing}"
        )
        if status.processing_status == "ended":
            break
        time.sleep(60)

    output_file = os.path.join(directory, f"batch_results_{batch_number}.jsonl")
    result_count = 0
    with open(output_file, "w", encoding="utf-8") as f:
        for result in client.messages.batches.results(batch_id):
            f.write(json.dumps(result.model_dump(), ensure_ascii=False) + "\n")
            result_count += 1

    print(f"  Downloaded {result_count} results to {output_file}")
    return result_count


def process_batch_file(input_file, params_lookup):
    results = []
    skipped = {"no_params": 0, "not_succeeded": 0, "invalid_format": 0}

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            custom_id = data["custom_id"]

            params = params_lookup.get(custom_id)
            if not params:
                skipped["no_params"] += 1
                continue

            result_data = data["result"]
            if result_data["type"] != "succeeded":
                skipped["not_succeeded"] += 1
                continue

            completion = result_data["message"]["content"][0]["text"]
            gen_model = result_data["message"]["model"]

            processed = process_conversation(completion, params, gen_model)
            if not processed["valid"]:
                skipped["invalid_format"] += 1
                continue

            results.append(processed)

    return results, skipped


def print_cost_summary(directory):
    input_files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".jsonl") and f.startswith("batch_results")
    ]

    total_input = 0
    total_output = 0
    total_requests = 0
    model_name = None

    for fpath in input_files:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                total_requests += 1
                result = data.get("result", {})
                if result.get("type") != "succeeded":
                    continue
                usage = result["message"].get("usage", {})
                total_input += usage.get("input_tokens", 0)
                total_output += usage.get("output_tokens", 0)
                if not model_name:
                    model_name = result["message"].get("model", "")

    pricing = BATCH_PRICING.get(model_name, {"input": 1.50, "output": 7.50})
    input_cost = (total_input / 1_000_000) * pricing["input"]
    output_cost = (total_output / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    print(f"\n--- Cost Summary ---")
    print(f"Model: {model_name} (batch pricing)")
    print(f"Requests: {total_requests}")
    print(f"Input tokens:  {total_input:,} (${input_cost:.4f})")
    print(f"Output tokens: {total_output:,} (${output_cost:.4f})")
    print(f"Total cost: ${total_cost:.4f}")
    if total_requests > 0:
        print(f"Avg cost per conversation: ${total_cost / total_requests:.6f}")
        est_1k = total_cost / total_requests * 1000
        est_10k = total_cost / total_requests * 10000
        est_50k = total_cost / total_requests * 50000
        print(f"Estimated cost: 1k=${est_1k:.2f}  10k=${est_10k:.2f}  50k=${est_50k:.2f}")
    print()


def postprocess(directory):
    params_file = os.path.join(directory, "params_lookup.json")
    if os.path.exists(params_file):
        with open(params_file, "r", encoding="utf-8") as f:
            params_lookup = json.load(f)
    else:
        print(f"Warning: {params_file} not found. Cannot map results to params.")
        params_lookup = {}

    input_files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".jsonl") and f.startswith("batch_results")
    ]

    all_results = []
    total_skipped = {}
    for fpath in input_files:
        results, skipped = process_batch_file(fpath, params_lookup)
        all_results.extend(results)
        for k, v in skipped.items():
            total_skipped[k] = total_skipped.get(k, 0) + v

    output_file = os.path.join(directory, "processed.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Processed {len(all_results)} valid conversations")
    print(f"Skipped: {total_skipped}")

    if len(all_results) == 0:
        print("No valid conversations to process.")
        return None

    return output_file


def filter_dataset(output_file):
    df = pd.read_json(output_file, lines=True)
    print(f"Total conversations before filtering: {len(df)}")

    df["conversation"] = df["conversation"].apply(lambda x: unidecode(x))

    df = df[df["character_count"] >= 1024]
    df = df[df["character_count"] <= 2048]
    print(f"After character count filter (1024-2048): {len(df)}")

    df = df[df["total_turns"] >= 3]
    print(f"After minimum turns filter (>=3): {len(df)}")

    df["initial_word_type"] = df["initial_word_type"].apply(
        lambda x: x.split()[-1] if x else x
    )

    df = df.drop(columns=["valid", "errors", "generation_id"], errors="ignore")
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    ordered_cols = [
        "conversation", "topic", "topic_category", "tone", "mode",
        "story_ending", "grammar", "initial_word_type", "initial_letter",
        "story_theme", "story_style", "story_feature", "story_persona",
        "word_count", "character_count", "person1_turns", "person2_turns",
        "total_turns", "model",
    ]
    df = df[[c for c in ordered_cols if c in df.columns]]

    filtered_file = output_file.replace("processed.jsonl", "filtered.jsonl")
    df.to_json(filtered_file, orient="records", lines=True, force_ascii=False)

    print(f"\nFinal dataset: {len(df)} conversations -> {filtered_file}")
    print(f"\nMode distribution:\n{df['mode'].value_counts(normalize=True)}")
    print(f"\nTopic category distribution:\n{df['topic_category'].value_counts()}")
    print(f"\nCharacter count stats:\n{df['character_count'].describe()}")

    return filtered_file


def download_batch(client, batch_id, directory, batch_number=1):
    os.makedirs(directory, exist_ok=True)
    output_file = os.path.join(directory, f"batch_results_{batch_number}.jsonl")
    result_count = 0
    with open(output_file, "w", encoding="utf-8") as f:
        for result in client.messages.batches.results(batch_id):
            f.write(json.dumps(result.model_dump(), ensure_ascii=False) + "\n")
            result_count += 1
    print(f"Downloaded {result_count} results to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Anthropic Batch Conversation Generator")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Submit batch, poll, download, and process")
    run_p.add_argument("-n", "--num", type=int, default=100, help="Number of conversations")
    run_p.add_argument("--batch-size", type=int, default=50_000, help="Max requests per batch")
    run_p.add_argument("--offset", type=int, default=0, help="Param iterator offset")
    run_p.add_argument("--model", default="claude-sonnet-4-6")
    run_p.add_argument("--max-retries", type=int, default=3)

    proc_p = sub.add_parser("process", help="Post-process a completed batch directory")
    proc_p.add_argument("directory", help="Path to batch directory (e.g. data/conv_batches_...)")

    dl_p = sub.add_parser("download", help="Download results from a previous batch ID")
    dl_p.add_argument("batch_id", help="Batch ID (msgbatch_...)")
    dl_p.add_argument("--directory", default=None, help="Output directory")

    args = parser.parse_args()

    if args.command == "run":
        client = anthropic.Anthropic()
        directory = os.path.join("data", f"conv_batches_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")
        os.makedirs(directory, exist_ok=True)

        total = 0
        batch_number = 0
        failures = 0

        all_params = {}

        while total < args.num and failures < args.max_retries:
            try:
                batch_number += 1
                n = min(args.batch_size, args.num - total)
                requests, params_lookup = get_batch_requests(n, args.model, offset=args.offset + total)
                all_params.update(params_lookup)
                submit_and_poll(client, requests, directory, batch_number)
                total += n
                failures = 0
            except Exception as e:
                print(f"Error: {e}")
                failures += 1

        with open(os.path.join(directory, "params_lookup.json"), "w", encoding="utf-8") as f:
            json.dump(all_params, f, ensure_ascii=False)

        if failures >= args.max_retries:
            print(f"Stopping due to {args.max_retries} consecutive failures.")
        else:
            print(f"\nAll batches complete. Processing results...")

        print_cost_summary(directory)
        output_file = postprocess(directory)
        if output_file:
            filter_dataset(output_file)

    elif args.command == "process":
        print_cost_summary(args.directory)
        output_file = postprocess(args.directory)
        if output_file:
            filter_dataset(output_file)

    elif args.command == "download":
        client = anthropic.Anthropic()
        directory = args.directory or os.path.join("data", f"conv_download_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")
        download_batch(client, args.batch_id, directory)
        print(f"Run 'python run_batch.py process {directory}' to post-process.")


if __name__ == "__main__":
    main()
