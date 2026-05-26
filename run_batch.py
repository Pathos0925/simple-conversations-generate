import argparse
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import anthropic
import openai
import pandas as pd
from unidecode import unidecode

from generate import (
    create_prompt,
    iterate_params,
    process_result,
)
from formats.shared import MAX_TOKENS


MODEL_PARAMETERS = {"top_p": 0.9}

KIMI_BASE_URL = "https://api.moonshot.ai/v1"
KIMI_MODELS = {"kimi-k2.6", "kimi-k2.5"}

BATCH_PRICING = {
    "claude-sonnet-4-6": {"input": 1.50, "output": 7.50},
    "claude-sonnet-4-5-20250514": {"input": 1.50, "output": 7.50},
    "claude-haiku-4-5-20251001": {"input": 0.40, "output": 2.00},
    "kimi-k2.6": {"input": 0.57, "output": 2.40},
    "kimi-k2.5": {"input": 0.36, "output": 1.80},
}


def is_kimi_model(model):
    return model in KIMI_MODELS


def get_batch_requests(num_completions, model, offset=0):
    params_iterator = iterate_params()
    for _ in range(offset):
        next(params_iterator)

    requests = []
    params_lookup = {}
    for i in range(num_completions):
        params = next(params_iterator)
        system_prompt, user_prompt = create_prompt(params)
        custom_id = f"gen_{i + offset}"

        params_lookup[custom_id] = params

        if is_kimi_model(model):
            requests.append({
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "max_completion_tokens": MAX_TOKENS,
                    "thinking": {"type": "disabled"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            })
        else:
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


def kimi_submit_and_poll(client, requests, directory, batch_number):
    jsonl_path = os.path.join(directory, f"batch_input_{batch_number}.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for req in requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")

    print(f"Uploading {len(requests)} requests for batch {batch_number}...")
    file_obj = client.files.create(
        file=open(jsonl_path, "rb"),
        purpose="batch",
    )

    print(f"Creating batch {batch_number} (file_id={file_obj.id})...")
    batch = client.batches.create(
        input_file_id=file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch_id = batch.id

    with open(os.path.join(directory, "batch_ids.txt"), "a") as f:
        f.write(f"{batch_id}\n")

    while True:
        status = client.batches.retrieve(batch_id)
        counts = status.request_counts
        print(
            f"  [{status.status}] "
            f"completed={counts.completed} failed={counts.failed} "
            f"total={counts.total}"
        )
        if status.status in ("completed", "failed", "expired", "cancelled"):
            break
        time.sleep(60)

    if status.status != "completed":
        print(f"  Batch {batch_number} ended with status: {status.status}")
        return 0

    output_file = os.path.join(directory, f"batch_results_{batch_number}.jsonl")
    content = client.files.content(status.output_file_id)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content.text)

    result_count = sum(1 for _ in content.text.strip().split("\n") if _)
    print(f"  Downloaded {result_count} results to {output_file}")
    return result_count


def process_kimi_batch_file(input_file, params_lookup):
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

            if data.get("error"):
                skipped["not_succeeded"] += 1
                continue

            response = data.get("response", {})

            body = response.get("body", {})
            choices = body.get("choices", [])
            if not choices:
                skipped["not_succeeded"] += 1
                continue

            message = choices[0].get("message", {})
            completion = message.get("content", "")
            if not completion:
                skipped["not_succeeded"] += 1
                continue

            gen_model = body.get("model", "kimi-k2.6")
            processed = process_result(completion, params, gen_model)
            if not processed["valid"]:
                skipped["invalid_format"] += 1
                continue

            results.append(processed)

    return results, skipped


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

            message = result_data["message"]
            if not message.get("content") or message.get("stop_reason") == "refusal":
                skipped["not_succeeded"] += 1
                continue

            completion = message["content"][0]["text"]
            gen_model = message["model"]

            processed = process_result(completion, params, gen_model)
            if not processed["valid"]:
                skipped["invalid_format"] += 1
                continue

            results.append(processed)

    return results, skipped


def _detect_kimi_results(directory):
    for f in os.listdir(directory):
        if f.endswith(".jsonl") and f.startswith("batch_results"):
            fpath = os.path.join(directory, f)
            with open(fpath, "r", encoding="utf-8") as fh:
                first_line = fh.readline()
                if first_line.strip():
                    data = json.loads(first_line)
                    return "response" in data and "result" not in data
    return False


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

    is_kimi = _detect_kimi_results(directory)

    for fpath in input_files:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                total_requests += 1

                if is_kimi:
                    if data.get("error"):
                        continue
                    response = data.get("response", {})
                    body = response.get("body", {})
                    usage = body.get("usage", {})
                    total_input += usage.get("prompt_tokens", 0)
                    total_output += usage.get("completion_tokens", 0)
                    if not model_name:
                        model_name = body.get("model", "")
                else:
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
        print(f"Avg cost per generation: ${total_cost / total_requests:.6f}")
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

    is_kimi = _detect_kimi_results(directory)
    processor = process_kimi_batch_file if is_kimi else process_batch_file

    all_results = []
    total_skipped = {}
    for fpath in input_files:
        results, skipped = processor(fpath, params_lookup)
        all_results.extend(results)
        for k, v in skipped.items():
            total_skipped[k] = total_skipped.get(k, 0) + v

    output_file = os.path.join(directory, "processed.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Processed {len(all_results)} valid texts")
    print(f"Skipped: {total_skipped}")

    if len(all_results) == 0:
        print("No valid texts to process.")
        return None

    return output_file


def load_tokenizer(tokenizer_path):
    import sys
    tokenizer_dir = os.path.dirname(os.path.abspath(tokenizer_path))
    if tokenizer_dir not in sys.path:
        sys.path.insert(0, tokenizer_dir)
    from sentencepiece import SentencePieceProcessor
    sp = SentencePieceProcessor(model_file=tokenizer_path)
    return sp


def filter_dataset(output_file, tokenizer_path=None):
    df = pd.read_json(output_file, lines=True)
    print(f"Total texts before filtering: {len(df)}")

    df["text"] = df["text"].apply(lambda x: unidecode(x))

    if tokenizer_path:
        print(f"Counting tokens with tokenizer: {tokenizer_path}")
        sp = load_tokenizer(tokenizer_path)
        df["token_count"] = df["text"].apply(lambda x: len(sp.encode(x)))
        df = df[df["token_count"] >= 200]
        print(f"After token count filter (>=200): {len(df)}")
    else:
        df = df[df["character_count"] >= 1024]
        print(f"After character count filter (>=1024): {len(df)}")

    df["initial_word_type"] = df["initial_word_type"].apply(
        lambda x: x.split()[-1] if x else x
    )

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["text"], keep="first")
    if before_dedup > len(df):
        print(f"After deduplication: {len(df)} (dropped {before_dedup - len(df)} duplicates)")

    df = df.drop(columns=["valid", "errors", "generation_id"], errors="ignore")
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    priority_cols = [
        "text", "format", "topic", "topic_category", "tone", "grammar",
        "initial_word_type", "initial_letter", "story_ending",
    ]
    other_cols = [c for c in df.columns if c not in priority_cols]
    ordered_cols = [c for c in priority_cols if c in df.columns] + other_cols
    df = df[ordered_cols]

    filtered_file = output_file.replace("processed.jsonl", "filtered.jsonl")
    df.to_json(filtered_file, orient="records", lines=True, force_ascii=False)

    print(f"\nFinal dataset: {len(df)} texts -> {filtered_file}")
    print(f"\nFormat distribution:\n{df['format'].value_counts()}")
    if "mode" in df.columns:
        print(f"\nConversation mode distribution:\n{df[df['format']=='conversation']['mode'].value_counts()}")
    print(f"\nTopic category distribution:\n{df['topic_category'].value_counts()}")
    print(f"\nCharacter count stats:\n{df['character_count'].describe()}")

    if "token_count" in df.columns:
        print(f"\nToken count stats:\n{df['token_count'].describe()}")
        total_tokens = df["token_count"].sum()
        print(f"\nTotal tokens in dataset: {total_tokens:,}")

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


def kimi_download_batch(client, batch_id, directory, batch_number=1):
    os.makedirs(directory, exist_ok=True)
    batch = client.batches.retrieve(batch_id)
    if batch.status != "completed":
        print(f"Batch status is '{batch.status}', not completed yet.")
        return
    output_file = os.path.join(directory, f"batch_results_{batch_number}.jsonl")
    content = client.files.content(batch.output_file_id)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content.text)
    result_count = sum(1 for line in content.text.strip().split("\n") if line)
    print(f"Downloaded {result_count} results to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Batch Text Generator (multi-format)")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Submit batch, poll, download, and process")
    run_p.add_argument("-n", "--num", type=int, default=100, help="Number of texts to generate")
    run_p.add_argument("--batch-size", type=int, default=50_000, help="Max requests per batch")
    run_p.add_argument("--offset", type=int, default=0, help="Param iterator offset")
    run_p.add_argument("--model", default="claude-sonnet-4-6")
    run_p.add_argument("--max-retries", type=int, default=3)
    run_p.add_argument("--tokenizer", default=None, help="Path to sentencepiece .model file for token counting")

    proc_p = sub.add_parser("process", help="Post-process a completed batch directory")
    proc_p.add_argument("directory", help="Path to batch directory (e.g. data/batches_...)")
    proc_p.add_argument("--tokenizer", default=None, help="Path to sentencepiece .model file for token counting")

    dl_p = sub.add_parser("download", help="Download results from a previous batch ID")
    dl_p.add_argument("batch_id", help="Batch ID (msgbatch_... or batch_...)")
    dl_p.add_argument("--directory", default=None, help="Output directory")
    dl_p.add_argument("--kimi", action="store_true", help="Use Kimi API for download")

    args = parser.parse_args()

    if args.command == "run":
        use_kimi = is_kimi_model(args.model)
        if use_kimi:
            client = openai.OpenAI(
                api_key=os.environ["KIMI_API_KEY"],
                base_url=KIMI_BASE_URL,
            )
        else:
            client = anthropic.Anthropic()

        directory = os.path.join("data", f"batches_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")
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
                with open(os.path.join(directory, "params_lookup.json"), "w", encoding="utf-8") as f:
                    json.dump(all_params, f, ensure_ascii=False)
                if use_kimi:
                    kimi_submit_and_poll(client, requests, directory, batch_number)
                else:
                    submit_and_poll(client, requests, directory, batch_number)
                total += n
                failures = 0
            except Exception as e:
                print(f"Error: {e}")
                failures += 1

        if failures >= args.max_retries:
            print(f"Stopping due to {args.max_retries} consecutive failures.")
        else:
            print(f"\nAll batches complete. Processing results...")

        print_cost_summary(directory)
        output_file = postprocess(directory)
        if output_file:
            filter_dataset(output_file, tokenizer_path=args.tokenizer)

    elif args.command == "process":
        print_cost_summary(args.directory)
        output_file = postprocess(args.directory)
        if output_file:
            filter_dataset(output_file, tokenizer_path=args.tokenizer)

    elif args.command == "download":
        directory = args.directory or os.path.join("data", f"download_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")
        if args.kimi:
            client = openai.OpenAI(
                api_key=os.environ["KIMI_API_KEY"],
                base_url=KIMI_BASE_URL,
            )
            kimi_download_batch(client, args.batch_id, directory)
        else:
            client = anthropic.Anthropic()
            download_batch(client, args.batch_id, directory)
        print(f"Run 'python run_batch.py process {directory}' to post-process.")


if __name__ == "__main__":
    main()
