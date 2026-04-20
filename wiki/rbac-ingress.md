# RBAC & Ingress

Traefik runs as a Service Account inside the cluster. For it to watch Kubernetes resources (Ingresses, Services, Secrets) and its own CRDs (IngressRoute, Middleware, etc.), it needs explicit RBAC permissions.

---

## Traffic Flow

```
External client
      │
      ▼
NodePort Service (port 30443)
      │
      ▼
Traefik Pod (Ingress Controller)
  - reads IngressRoute CRD
  - handles TLS termination
      │
      ▼
ClusterIP Service (app)
      │
      ▼
FastAPI Pod (:8080)
```

**NodePort** exposes Traefik to the outside. **ClusterIP** is internal only — pods and services communicate through it. Traefik acts as the bridge between the two.

---

## Service Account

Traefik runs under a dedicated Service Account in the `ingress` namespace:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: traefik-ingress-controller
  namespace: ingress
```

---

## ClusterRole

A ClusterRole (not Role) is needed because Traefik watches resources cluster-wide:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: traefik-ingress-role
rules:
  - apiGroups: [""]
    resources: ["services", "endpoints", "secrets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["extensions", "networking.k8s.io"]
    resources: ["ingresses", "ingressclasses"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["traefik.io"]
    resources: ["ingressroutes", "middlewares", "tlsstores", ...]
    verbs: ["get", "list", "watch"]
```

The difference between Role and ClusterRole:
- **Role** — permissions only within the namespace it lives in
- **ClusterRole** — cluster-wide, can reach any namespace

---

## ClusterRoleBinding

Binds the ClusterRole to the Service Account:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: traefik-ingress-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: traefik-ingress-role
subjects:
  - kind: ServiceAccount
    name: traefik-ingress-controller
    namespace: ingress
```

---

## Checking Permissions

Check if a Service Account is allowed to do something:

```bash
kubectl auth can-i list services \
  --as=system:serviceaccount:ingress:traefik-ingress-controller
```

List everything a Service Account can do:

```bash
kubectl auth can-i --list \
  --as=system:serviceaccount:ingress:traefik-ingress-controller
```

Check existing roles and bindings:

```bash
kubectl get clusterroles
kubectl get clusterrolebindings
kubectl get roles -A
kubectl get rolebindings -A
```

The RBAC engine is queried through the API server. Rules are stored in etcd.

---

## Traefik CRDs

Traefik uses Custom Resource Definitions for its own routing config. Install them before deploying Traefik:

```bash
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.6/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml
```

Without the CRDs, the ClusterRole rules referencing `traefik.io` API group will fail, and Traefik pods will log errors like:

```
failed to list *v1alpha1.IngressRouteUDP: ingressrouteudps.traefik.io is forbidden
```

---

## IngressRoute

Traefik uses its own CRD (`IngressRoute`) instead of the standard Kubernetes `Ingress`. This allows more expressive routing rules.

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: k8s-python-api-route
  namespace: k8s-python-api
spec:
  entryPoints:
    - websecure
  routes:
    - match: PathPrefix(`/`)
      kind: Rule
      services:
        - name: k8s-python-api-service   # must match ClusterIP service name
          port: 80
  tls:
    secretName: k8s-python-api-tls       # cert-manager creates this
```

The service name and namespace in the IngressRoute must match the actual ClusterIP service exactly.

---

## Kind + WSL Networking Note

`localhost` inside WSL does not reach NodePort services in Kind. Kind nodes run as Docker containers with their own network namespace. To reach them from WSL:

```bash
# Find the container IP of the Kind node
docker ps  # get container ID
docker inspect <container_id> | grep IPAddress
# e.g., 172.19.0.2

# Curl the NodePort directly
curl -k https://172.19.0.2:30443
```

To reach the cluster from a Windows browser, port-forward or configure Kind's extraPortMappings in the cluster config to bind to `0.0.0.0`.
