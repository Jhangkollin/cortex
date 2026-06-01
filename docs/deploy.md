# Deploy

## Boundary

This repo (`cortex/`) builds and pushes container images. Deploy config lives in `../infra/`.

| Lives here | Lives in `../infra/data-platform-helm-charts/` | Lives in `../infra/data-platform-iac/` | Lives in Databricks workspace |
|---|---|---|---|
| `Dockerfile` (api + web) | `cortex-api/` Helm chart | **RDS PostgreSQL** (OLTP) | SQL Warehouse Serverless |
| GHA workflows (build + ECR push) | `cortex-web/` Helm chart | ElastiCache Redis | Vector Search index |
| `docs/deploy.md` (this) | values.uat.yaml, values.prod.yaml | ECR repos | Workspace-scoped service principal |
| | shared library chart (if used) | Pod Identity / IAM roles | |
| | | OAuth client registration | |
| | | Secrets in AWS Secrets Manager (RDS password, Redis URL, OAuth) | |

## Pod Identity

Per `../infra/CLAUDE.md`: **Pod Identity over IRSA** for all new workloads. Cortex's service accounts in Helm carry **no** `eks.amazonaws.com/role-arn` annotation; the IAM-to-ServiceAccount binding lives in Terraform.

| Helm chart | IAC pod-identity | Service account | Namespace |
|---|---|---|---|
| `cortex-api` | `aigc/pod-identity` | `cortex-api-sa` | TBD (`agent` or new `cortex` ns) |
| `cortex-web` | `aigc/pod-identity` | `cortex-web-sa` | TBD |

## CI/CD chain

```
PR → GitHub Actions (this repo)
       lint + test (api/ + web/)
       merge to develop
       ↓
       build images, push to ECR with commit SHA tag
       ↓
       (manual or ArgoCD) bump image tag in ../infra/data-platform-helm-charts/cortex-{api,web}/values.uat.yaml
       PR → merge → helm upgrade
```

For early MVP, the bump is manual (small extra PR per deploy). When ArgoCD is configured for the cortex namespace, this becomes automatic.

## When you change...

| What | Where | Notes |
|---|---|---|
| Application code | this repo, feature branch → develop | CI builds image automatically |
| Env vars / replicas / resource limits | `../infra/data-platform-helm-charts/cortex-{api,web}/` | PR in infra repo |
| RDS / ElastiCache / IAM / ECR | `../infra/data-platform-iac/aigc/` | PR in infra repo; Pod Identity must be applied BEFORE Helm chart |
| OAuth credentials | AWS Secrets Manager via `../infra/data-platform-iac/aigc/secretsmanager/` | rotate quarterly |
