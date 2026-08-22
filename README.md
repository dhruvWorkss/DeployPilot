# DeployPilot

DeployPilot is a production-oriented deployment control plane for building, releasing, observing, and automatically recovering Kubernetes workloads.

It combines a Next.js operations dashboard, a FastAPI control-plane API, PostgreSQL-backed release history, a deterministic Python incident assistant, Jenkins automation, Prometheus/Grafana observability, and Terraform for GKE.

## What makes it self-healing

1. Kubernetes probes and replica controllers recover failed containers and pods.
2. Each release is observed through its rollout rather than treated as complete after `kubectl apply`.
3. Post-deployment health gates evaluate availability and error-rate signals.
4. Failed rollouts are automatically undone and recorded as incidents.
5. The incident assistant classifies logs and returns safe, actionable remediation guidance.

## Quick start

Requirements: Docker with Compose v2.

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Dashboard: http://localhost:3000
- API documentation: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (`admin` / the value of `GRAFANA_PASSWORD`)

Local dashboard login:

- Email: `operator@deploypilot.dev`
- Password: `DeployPilot2026!`

The dashboard includes Overview, Services, Deployments, Incidents, and Infrastructure workspaces. Each operational page reads live data from the FastAPI control plane.

The API seeds realistic deployment and incident data in development mode. No Kubernetes cluster is required to explore the product.

## Repository layout

```text
apps/web/                  Next.js operations dashboard
services/control-plane/    FastAPI API, deployment orchestration, incident analysis
deploy/kubernetes/         Namespaced app and observability manifests
Jenkinsfile                Release pipeline
infra/terraform/           Production GKE infrastructure
observability/             Prometheus and Grafana provisioning
scripts/                   Rollout and health-gate automation
```

## Development

Backend:

```bash
cd services/control-plane
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

Python 3.12 is required — the pinned `psycopg[binary]` build has no wheels for 3.13+.

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

## Production model

- Authentication is expected at the ingress using an OIDC-aware proxy; the API accepts signed JWTs when `AUTH_DISABLED=false`.
- The API never exposes cluster credentials to browsers.
- Container images are pinned by digest in promotion workflows.
- Terraform uses remote state and Workload Identity; no static GCP service-account key is required.
- Namespace quotas, pod disruption budgets, network policies, non-root containers, and read-only filesystems are included.
- Every deployment mutation produces an audit event.

See [docs/architecture.md](docs/architecture.md), [docs/runbook.md](docs/runbook.md), and [SECURITY.md](SECURITY.md).

## Verification

```bash
docker compose config
cd services/control-plane && pytest
cd apps/web && npm ci && npm run lint && npm run build
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform init -backend=false && terraform -chdir=infra/terraform validate
```

## License

MIT
