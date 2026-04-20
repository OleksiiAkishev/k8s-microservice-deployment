# Local Setup

Everything needed to run this project on a local machine. Tested on WSL Ubuntu.

---

## Prerequisites

- Docker Desktop (or Docker Engine on Linux/WSL)
- `kubectl`
- Kind
- Helm 3

---

## 1. Install Kind

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

Kind runs each Kubernetes node as a Docker container. When you do `docker ps` after creating a cluster, you will see the node listed there — that mental model helps later when debugging networking.

---

## 2. Create the Cluster

```bash
kind create cluster --name local-dev
```

Check it came up:

```bash
kubectl get nodes
# NAME                     STATUS   ROLES           AGE   VERSION
# local-dev-control-plane  Ready    control-plane   30s   v1.35.1
```

If `kubectl get nodes` returns `connection refused`, kubectl is pointing at the wrong context:

```bash
kubectl config use-context kind-local-dev
kubectl cluster-info
```

Delete the cluster when done to free resources:

```bash
kind delete cluster --name local-dev
```

---

## 3. Python App (local run, optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 4. Docker Image

Build the image locally:

```bash
docker build -t k8s-python-app:local .
```

The Dockerfile uses a two-stage build:
- **Stage 1 (builder):** installs all dependencies into a virtual env
- **Stage 2 (runtime):** copies only the venv, no build tools, non-root user

Run it to verify:

```bash
docker run -p 8000:8080 k8s-python-app:local
# or detached:
docker run -p 8000:8080 -d k8s-python-app:local
```

Exec into a running container if needed:

```bash
docker exec -it <container_id> /bin/sh
```

---

## 5. Image Pull Secret

The cluster needs credentials to pull the image from `ghcr.io`. The secret must be type `kubernetes.io/dockerconfigjson` — not Opaque. Use `kubectl create secret docker-registry`, not `secret generic`:

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<your-github-username> \
  --docker-password=<your-ghcr-token>
```

Verify the type is correct:

```bash
kubectl describe secret ghcr-secret
# Type: kubernetes.io/dockerconfigjson  <-- must be this, not Opaque
```

A secret typed as `Opaque` is silently ignored during image pulls, which results in a 401 from the registry even when the token is valid.

---

## 6. Deploy via Helm

```bash
helm upgrade --install k8s-python-api ./helm/app \
  --namespace k8s-python-api --create-namespace
```

Verify:

```bash
kubectl get pods -n k8s-python-api
kubectl get deployment -n k8s-python-api
helm list
```

Check which cluster Helm is targeting:

```bash
kubectl config current-context
```

---

## 7. Useful Troubleshooting Commands

```bash
# Pod status and events
kubectl get pods -n k8s-python-api
kubectl describe pod <pod-name> -n k8s-python-api
kubectl get events -n k8s-python-api --field-selector involvedObject.name=<pod-name>

# Logs
kubectl logs <pod-name> -c k8s-python-api -n k8s-python-api

# Restart all pods in a deployment (rolling)
kubectl rollout restart deployment k8s-python-api-deployment -n k8s-python-api

# Full cluster state dump (pipe to grep to avoid huge output)
kubectl cluster-info dump | grep <keyword>
```
