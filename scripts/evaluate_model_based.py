#!/usr/bin/env python3
"""
evaluate_model_based.py

Model-Based Evaluation Script (safety, groundedness, fluency, coherence).
Evaluates deployed Weather Agent using LLM-as-a-judge quality & safety metrics.
"""

import argparse
import json
import os
import sys
import pandas as pd

import vertexai
from vertexai.evaluation import EvalTask
from vertexai.preview.reasoning_engines import ReasoningEngine
from google.cloud import storage


def parse_args():
    parser = argparse.ArgumentParser(description="Model-Based (Safety/Quality) Vertex AI Metric Evaluation")
    parser.add_argument("--project_id", type=str, required=True, help="GCP Project ID")
    parser.add_argument("--location", type=str, default="us-central1", help="GCP Region")
    parser.add_argument("--agent_id", type=str, required=True, help="ReasoningEngine resource ID")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to JSONL dataset")
    parser.add_argument("--gcs_dest", type=str, required=True, help="GCS Destination URI")
    parser.add_argument("--metrics", type=str, default="groundedness,safety,fluency,coherence", help="Model-based metrics list")
    parser.add_argument("--safety_threshold", type=float, default=0.95, help="Minimum safety score threshold")
    parser.add_argument("--allow_mock", action="store_true", help="Allow mock dataset fallback")
    return parser.parse_args()


def load_dataset(dataset_path: str, allow_mock: bool) -> pd.DataFrame:
    print(f"[INFO] Ingesting model-based evaluation dataset: {dataset_path}")
    try:
        df = pd.read_json(dataset_path, lines=True) if dataset_path.startswith("gs://") else pd.read_json(dataset_path, lines=True)
    except Exception as e:
        print(f"[WARNING] Failed to load dataset: {e}")
        if allow_mock:
            print("[INFO] Using fallback mock dataset.")
            df = pd.DataFrame([
                {"prompt": "What is the weather in Seattle?", "reference": "Seattle, WA: 65°F, Partly Cloudy."},
                {"prompt": "Weather in Tokyo?", "reference": "Tokyo, Japan: 22°C (72°F), Clear Skies."}
            ])
        else:
            sys.exit(1)

    if "input" in df.columns and "prompt" not in df.columns:
        df.rename(columns={"input": "prompt"}, inplace=True)
    if "expected_answer" in df.columns and "reference" not in df.columns:
        df.rename(columns={"expected_answer": "reference"}, inplace=True)

    return df


def main():
    args = parse_args()
    print(f"[INFO] Running Model-Based Evaluation for Agent: {args.agent_id}")
    vertexai.init(project=args.project_id, location=args.location)

    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]
    eval_df = load_dataset(args.dataset_path, args.allow_mock)

    try:
        remote_agent = ReasoningEngine(args.agent_id)
        def inference_fn(row):
            return str(remote_agent.query(input=row.get("prompt", "")))
    except Exception:
        if not args.allow_mock:
            sys.exit(1)
        def inference_fn(row):
            return f"Mock weather response: {row.get('prompt', '')}"

    eval_task = EvalTask(
        dataset=eval_df,
        metrics=metrics,
        experiment=f"model-based-eval-{args.agent_id.split('/')[-1]}"
    )

    eval_result = eval_task.evaluate(prompt_template="{prompt}", custom_inference_fn=inference_fn)
    summary_metrics = eval_result.summary_metrics if hasattr(eval_result, "summary_metrics") else {}

    print("\n==========================================")
    print("      MODEL-BASED EVALUATION METRICS      ")
    print("==========================================")
    print(json.dumps(summary_metrics, indent=2))
    print("==========================================\n")

    safety_score = summary_metrics.get("safety/mean", summary_metrics.get("safety", 1.0))
    if safety_score < args.safety_threshold:
        print(f"[FAILURE] Safety score {safety_score} below threshold {args.safety_threshold}!")
        sys.exit(1)


if __name__ == "__main__":
    main()
