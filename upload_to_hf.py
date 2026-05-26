import argparse
import os
import glob
import pandas as pd
from datasets import Dataset, DatasetDict


def find_batch_dirs(data_dir="data"):
    dirs = sorted(glob.glob(os.path.join(data_dir, "batches_*")))
    return [d for d in dirs if os.path.isfile(os.path.join(d, "filtered.jsonl"))]


def load_batch(directory):
    path = os.path.join(directory, "filtered.jsonl")
    df = pd.read_json(path, lines=True)
    return df


def main():
    parser = argparse.ArgumentParser(description="Upload batch datasets to HuggingFace")
    parser.add_argument("repo", help="HuggingFace repo (e.g. username/dataset-name)")
    parser.add_argument("--dirs", nargs="+", default=None,
                        help="Specific batch directories to upload. If omitted, shows a picker.")
    parser.add_argument("--all", action="store_true", help="Upload all available batch directories")
    parser.add_argument("--test-size", type=float, default=0.05, help="Test split fraction (default 0.05)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--private", action="store_true", help="Make the dataset private")
    parser.add_argument("--data-dir", default="data", help="Data directory (default: data)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded without pushing")
    args = parser.parse_args()

    available = find_batch_dirs(args.data_dir)
    if not available:
        print(f"No batch directories with filtered.jsonl found in {args.data_dir}/")
        return

    if args.all:
        selected = available
    elif args.dirs:
        selected = []
        for d in args.dirs:
            if not d.startswith(args.data_dir):
                d = os.path.join(args.data_dir, d)
            if os.path.isfile(os.path.join(d, "filtered.jsonl")):
                selected.append(d)
            else:
                print(f"Warning: {d} has no filtered.jsonl, skipping")
        if not selected:
            print("No valid directories selected.")
            return
    else:
        print("Available batch directories:\n")
        for i, d in enumerate(available):
            path = os.path.join(d, "filtered.jsonl")
            df = pd.read_json(path, lines=True)
            print(f"  [{i}] {os.path.basename(d)}  ({len(df)} rows)")
        print(f"\n  [a] All of the above")

        choice = input("\nSelect directories (comma-separated numbers, or 'a' for all): ").strip()
        if choice.lower() == "a":
            selected = available
        else:
            indices = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
            selected = [available[i] for i in indices if i < len(available)]

        if not selected:
            print("No directories selected.")
            return

    print(f"\nLoading {len(selected)} batch directories...")
    dfs = []
    for d in selected:
        df = load_batch(d)
        print(f"  {os.path.basename(d)}: {len(df)} rows")
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    print(f"\nCombined: {len(combined)} rows")

    if "format" in combined.columns:
        print(f"\nFormat distribution:\n{combined['format'].value_counts().to_string()}")

    ds = Dataset.from_pandas(combined)

    if args.test_size > 0:
        split = ds.train_test_split(test_size=args.test_size, seed=args.seed)
        dataset_dict = DatasetDict({"train": split["train"], "test": split["test"]})
        print(f"\nSplit: train={len(split['train'])}, test={len(split['test'])}")
    else:
        dataset_dict = DatasetDict({"train": ds})
        print(f"\nNo test split (--test-size 0)")

    if args.dry_run:
        print(f"\n[DRY RUN] Would push to: {args.repo}")
        print(f"  Private: {args.private}")
        print(f"  Columns: {list(combined.columns)}")
        print(f"  Sample row:\n{combined.iloc[0].to_dict()}")
        return

    print(f"\nPushing to {args.repo}...")
    dataset_dict.push_to_hub(args.repo, private=args.private)
    print(f"\nDone! Dataset available at https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
