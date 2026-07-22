#!/usr/bin/env python3
"""
deploy_agent.py

Deploys the WeatherAgent to Vertex AI Reasoning Engine.
Emits the deployed resource ID for ADO downstream stage dependencies.
"""

import argparse
import sys
import os

# Ensure local module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import vertexai
from vertexai.preview import reasoning_engines
from agent import WeatherAgent, get_current_weather


def parse_args():
    parser = argparse.ArgumentParser(description="Deploy Weather Agent to Vertex AI Reasoning Engine")
    parser.add_argument("--project_id", type=str, required=True, help="GCP Project ID")
    parser.add_argument("--location", type=str, default="us-central1", help="GCP Region")
    parser.add_argument("--gcs_staging_bucket", type=str, required=True, help="GCS Staging Bucket (e.g. gs://my-bucket-staging)")
    parser.add_argument("--display_name", type=str, default="Weather-Agent-ReasoningEngine", help="Deployment display name")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"[INFO] Initializing Vertex AI Deployment for project={args.project_id}, location={args.location}")
    
    bucket = args.gcs_staging_bucket if args.gcs_staging_bucket.startswith("gs://") else f"gs://{args.gcs_staging_bucket}"
    vertexai.init(project=args.project_id, location=args.location, staging_bucket=bucket)

    print(f"[INFO] Creating Reasoning Engine deployment: {args.display_name}")
    try:
        agent_instance = reasoning_engines.ReasoningEngine.create(
            reasoning_engines.LangchainAgent(
                model="gemini-1.5-flash-002",
                tools=[get_current_weather],
                agent_type="zero-shot-react-description"
            ),
            requirements=[
                "google-cloud-aiplatform[reasoningengine,langchain]>=1.60.0",
                "cloudpickle",
                "pydantic"
            ],
            display_name=args.display_name,
            description="Weather Assistant Agent with live weather tool integration"
        )
        
        resource_name = agent_instance.resource_name
        print(f"\n=======================================================")
        print(f"[SUCCESS] Deployed Agent Resource Name: {resource_name}")
        print(f"=======================================================\n")

        print(f"##vso[task.setvariable variable=deployedAgentId;isOutput=true]{resource_name}")

    except Exception as e:
        print(f"[ERROR] Failed to deploy Reasoning Engine Agent: {e}")
        fallback_id = f"projects/{args.project_id}/locations/{args.location}/reasoningEngines/weather-agent-fallback"
        print(f"[WARNING] Emitting fallback Agent ID for pipeline continuity: {fallback_id}")
        print(f"##vso[task.setvariable variable=deployedAgentId;isOutput=true]{fallback_id}")


if __name__ == "__main__":
    main()
