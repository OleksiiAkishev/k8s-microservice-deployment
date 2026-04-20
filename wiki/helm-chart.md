# Helm Chart

The project has two Helm charts:
- `helm/app/` — application chart (deployment, service, configmap, namespace, ingressroute, pull secret)
- `helm/infra/` — infrastructure charts (Traefik, cert-manager ClusterIssuer)

`k8s-python-api-helm/` in the project root is an earlier version of the app chart, used in the current CI/CD pipeline.

---

## Chart Structure

```
helm/app/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl       # named template helpers (namespace, labels, fullname)
    ├── _ingress.tpl       # ingress helper logic
    ├── namespace.yaml
    ├── configmap.yaml
    ├── deployment.yaml
    ├── service.yaml
    ├── ingressroute.yaml  # Traefik CRD
    └── secret-docker.yaml # image pull secret
```

---

## Deployment Labels

A Deployment finds its pods via `spec.selector.matchLabels`. Whatever is defined there **must** exist in `spec.template.metadata.labels` and vice versa — Kubernetes enforces this.

```yaml
spec:
  selector:
    matchLabels:
      app: k8s-python-api       # <-- filter: "give me pods with this label"
  template:                     # <-- pod template starts here
    metadata:
      labels:
        app: k8s-python-api     # <-- must match matchLabels exactly
    spec:
      containers:
        ...
```

---

## Template Helpers (`_helpers.tpl`)

Common values reused across templates are defined as named templates:

```yaml
{{- define "k8s-python-api-helm.namespace" -}}
{{- ... -}}
{{- end }}
```

Used in other templates with `include`:

```yaml
namespace: {{ include "k8s-python-api-helm.namespace" . }}
```

---

## toYaml — When and Why

Helm parses values from YAML into Go objects. When you pass a list or object into a template field, Go's representation (`[]interface{}`) is invalid YAML. The `toYaml` pipe converts it back:

```yaml
# In values.yaml:
imagePullSecrets:
  - name: ghcr-secret

# In template — WRONG (Go object, not YAML):
imagePullSecrets: {{ .Values.imagePullSecrets }}

# Correct:
imagePullSecrets:
  {{ toYaml .Values.imagePullSecrets | nindent 2 }}
```

Without `toYaml`, you get: `wrong type for value; expected string; got []interface{}`

---

## Accessing a Specific List Element

```yaml
# Get the name field from the first item in imagePullSecrets:
name: {{ (index .Values.imagePullSecrets 0).name }}
```

---

## Deploy Commands

```bash
# First install
helm install k8s-python-api ./helm/app --namespace k8s-python-api --create-namespace

# Update after changes (--install creates if not exists)
helm upgrade --install k8s-python-api ./helm/app \
  --namespace k8s-python-api --create-namespace

# Delete release
helm uninstall k8s-python-api -n k8s-python-api

# List all releases
helm list -A
```

---

## Debugging

Render templates without deploying:

```bash
# Render only (no cluster contact)
helm template my-release ./helm/app

# Full install simulation (contacts cluster for validation)
helm install --dry-run --debug my-release ./helm/app
```

Debug what the template context `.` contains — add this to any template temporarily:

```yaml
metadata:
  debug-context: |
    {{ toYaml . | indent 4 }}
```

This only works if rendering succeeds. If there's an error earlier, you won't see it.

Validate YAML separately if helm error lines don't make sense:

```bash
# Install yq
sudo snap install yq

# Validate values file
yq eval '.' ./helm/app/values.yaml
```

Note: the line number in a Helm error message often points to where the parser *gave up*, not where the actual mistake is. Always check the YAML structure above the reported line.

Useful links:
- Sprig function library: https://masterminds.github.io/sprig/
- Online YAML validator: https://www.yamllint.com/

---

## Multiple Values Files

If overriding with multiple values files (e.g., secrets separated from config):

```bash
helm template my-app ./helm/app \
  -f ./helm/app/values.yaml \
  -f secrets-values.yaml
```

The last `-f` wins on conflicts.
