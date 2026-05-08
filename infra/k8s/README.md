# Kubernetes manifests (skeleton)

These manifests are **not** applied as part of the milestone delivery. They
exist to demonstrate that the architecture is already portable to
Kubernetes without a refactor:

- Each service is a `Deployment` + `Service`.
- Postgres is a single-replica `Deployment` (no PVC for now to keep the
  example trivial — swap for a `StatefulSet` + `PersistentVolumeClaim` when
  promoting beyond local dev).
- Environment variables come from a `Secret` you create from your local
  `.env` so credentials never live in the manifests.

## Apply against a local cluster (kind / minikube)

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl -n leaf-app create secret generic leaf-env --from-env-file=.env
kubectl apply -f infra/k8s/
```

## Files

| File | What it deploys |
| --- | --- |
| `namespace.yaml` | `leaf-app` namespace. |
| `postgres.yaml` | Postgres 16 `Deployment` + `ClusterIP` service. |
| `auth.yaml` | `auth-service` Deployment + `ClusterIP` service on 8000. |
| `classifier.yaml` | `classifier-service` Deployment + `ClusterIP` service on 8000. |

## Validation (no cluster required)

```bash
kubectl apply --dry-run=client -f infra/k8s/
```
