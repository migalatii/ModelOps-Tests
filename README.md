# ModelOps-Tests

Welcome to **ModelOps-Tests**! This repository serves as the active test harness and operational reference implementation for AI applications deployed on Google Cloud Platform (GCP).

It wires together templates from `ModelOps-Templates` to create an end-to-end Master Orchestrator Pipeline (`orchestrator.yml`), complete with a sample **Weather Agent**, deployment scripts, evaluation scripts, and test datasets.

---

## 📁 Repository Directory Map

```
ModelOps-Tests/
├── README.md                            # Main project overview & agent navigation guide
├── ARCHITECTURE.md                      # Technical architecture & execution graph specs
├── requirements.txt                     # All Python dependencies (vertexai, pandas, storage, etc.)
├── data/
│   └── evalset.jsonl                    # Weather Agent evaluation dataset
├── src/
│   └── weather_agent/
│       ├── agent.py                     # WeatherAgent logic & get_current_weather tool
│       └── deploy_agent.py              # Vertex AI ReasoningEngine deployment script
├── scripts/
│   ├── evaluate_metric_based.py         # Computation-based metrics script (exact_match, rouge_l)
│   └── evaluate_model_based.py          # Model-based metrics script (safety, groundedness, fluency)
└── pipelines/runs/agent-creation-and-evaluation/
    ├── orchestrator.yml                 # Master Orchestrator ADO Pipeline entrypoint
    ├── deployment/
    │   ├── build-env-job.yml            # Calls ModelOps-Templates build_python_environment.yml
    │   ├── deploy-agent-job.yml         # Runs deploy_agent.py & emits deployedAgentId
    │   ├── deployment-validation-job.yml
    │   └── setup-wif-step.yml
    └── evaluation/
        ├── define-metrics-step.yml
        ├── run-eval-task-step.yml
        ├── evaluate-metric-based-jobs.yml # Job wrapper invoking ModelOps-Templates component
        └── evaluate-model-based-jobs.yml  # Job wrapper invoking ModelOps-Templates component
```

---

## ⚡ Master Orchestrator Pipeline Parameters

When triggering `orchestrator.yml` in Azure DevOps, you can parameterize the run for rapid development:

1. **`runDeployment`** (`boolean`, default: `true`):
   * Set to `false` to skip environment build and Reasoning Engine deployment.
2. **`existingAgentId`** (`string`, default: `''`):
   * If `runDeployment` is `false`, paste an existing Vertex AI resource ID here (e.g. `projects/<num>/locations/<loc>/reasoningEngines/<id>`) to route directly to evaluation.
3. **`allowMockDataset`** (`boolean`, default: `false`):
   * Set to `true` to allow fallback mock evaluation for dry-run testing.

---

## 🛠️ Rapid Developer Iteration Workflow

1. **Deploy Once**: Trigger pipeline with `runDeployment: true`. Copy the output `deployedAgentId` from Stage 2 logs.
2. **Iterate Fast**: For subsequent tweaks to `scripts/evaluate_metric_based.py`, `scripts/evaluate_model_based.py`, or `data/evalset.jsonl`, run the pipeline with `runDeployment: false` and pass the `existingAgentId`. This skips deployment entirely and executes evaluations in seconds.
