# ModelOps-Tests Architecture & Developer Handoff

This document describes the runtime architecture, ADO variable state routing, evaluation execution engines, and developer guidelines for `ModelOps-Tests`.

---

## 🏛️ End-to-End Orchestrator Pipeline Graph

The Master Orchestrator (`orchestrator.yml`) unifies three execution stages:

```
[ Stage 1: BuildEnv ]
         │
         ▼
[ Stage 2: DeployAgent ] ───( Emits deployedAgentId )
         │                             │
         └──────────────┬──────────────┘
                        │
                        ▼
[ Stage 3: EvaluateAgent ]
         ├── Job 1: EvaluateMetricBased (exact_match, rouge_l)
         └── Job 2: EvaluateModelBased  (safety, groundedness, fluency)
```

---

## 🔄 Dynamic Variable Routing & State Passing

`orchestrator.yml` dynamically routes the target `agentId` to Stage 3 using ADO YAML expressions:

```yaml
variables:
  ${{ if eq(parameters.runDeployment, true) }}:
    resolvedAgentId: $[ stageDependencies.DeployAgent.DeployJob.outputs['deployAgentTask.deployedAgentId'] ]
  ${{ if eq(parameters.runDeployment, false) }}:
    resolvedAgentId: '${{ parameters.existingAgentId }}'
```

> [!CAUTION]
> If you rename the deployment stage (`DeployAgent`), the job (`DeployJob`), or the script task (`deployAgentTask`), update this variable expression immediately or `resolvedAgentId` will resolve to null.

---

## 🧪 Evaluation Script Specs

1. **Computation-Based Script (`scripts/evaluate_metric_based.py`)**:
   * Uses `vertexai.evaluation.EvalTask` for deterministic metric evaluation (`exact_match`, `rouge_l`).
   * Connects to deployed `ReasoningEngine` endpoint and uploads results to GCS.

2. **Model-Based Script (`scripts/evaluate_model_based.py`)**:
   * Uses `vertexai.evaluation.EvalTask` with LLM-as-a-judge evaluators (`safety`, `groundedness`, `fluency`, `coherence`).
   * Evaluates safety scores against `--safety_threshold` (default `0.95`). Exits with code `1` if safety score drops below threshold.

---

## 🔧 ADO Executable Permissions Workaround

When ADO publishes and downloads the Python `.venv` pipeline artifact, binary executable permissions are stripped. All evaluation job steps execute a mandatory `chmod` fix:

```bash
chmod +x $(Build.SourcesDirectory)/.venv/bin/python* || true
```
