# TLS & cert-manager

cert-manager handles TLS certificate lifecycle inside the cluster. In this project it issues self-signed certificates via a ClusterIssuer.

---

## Install cert-manager

Apply the official manifest to the cluster:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
```

Verify pods are running before proceeding:

```bash
kubectl get pods -n cert-manager
# NAME                                      READY   STATUS    
# cert-manager-...                          1/1     Running   
# cert-manager-cainjector-...               1/1     Running   
# cert-manager-webhook-...                  1/1     Running   
```

All three pods must be `Running`. The webhook pod validates cert-manager resources - if it's not ready, ClusterIssuer creation will fail.

---

## ClusterIssuer

A ClusterIssuer is a cluster-scoped resource (no namespace). It defines *how* certificates are issued. This project uses a self-signed issuer suitable for local development:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}
```

Deploy the ClusterIssuer chart:

```bash
helm upgrade --install selfsigned-cluster-issuer ./helm/infra/cert-manager
```

Verify:

```bash
kubectl get clusterissuer
# NAME                READY   AGE
# selfsigned-issuer   True    ...
```

`READY: True` means cert-manager can issue certificates through this issuer.

---

## TLS Certificate for Traefik

Traefik needs a TLS certificate to serve HTTPS on its `websecure` entrypoint. cert-manager creates and rotates it automatically once a `Certificate` resource is defined:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: traefik-tls
  namespace: ingress
spec:
  secretName: traefik-tls-secret    # cert-manager will create this Secret
  issuerRef:
    name: selfsigned-issuer
    kind: ClusterIssuer
  dnsNames:
    - localhost
```

After applying, cert-manager issues the cert and stores it in the named Secret:

```bash
kubectl get secret -n ingress
# traefik-tls-secret   kubernetes.io/tls   ...
```

---

## IngressRoute TLS

The IngressRoute for the application references the certificate secret:

```yaml
spec:
  tls:
    secretName: traefik-tls-secret
```

Traefik reads this secret and presents the certificate during the TLS handshake.

---

## Verify TLS

Test from WSL using the Kind node IP:

```bash
# Get Kind node container IP
docker inspect kind-local-dev-control-plane | grep IPAddress

# Curl - -k skips cert verification (expected for self-signed)
curl -k https://172.19.0.2:30443/health
# {"status":"healthy","timestamp":...}
```

If you see a TLS handshake error rather than a cert warning, the secret name is likely mismatched between the Certificate resource and the IngressRoute.

---

## Summary

| Resource | Scope | Purpose |
|---|---|---|
| `ClusterIssuer` | Cluster | Defines how certs are issued |
| `Certificate` | Namespaced | Requests a cert, cert-manager fulfills it |
| `Secret` (tls type) | Namespaced | Stores the issued cert + key |
| `IngressRoute` | Namespaced | References the secret for TLS termination |

---

## Production Notes

Self-signed certs are fine locally. In production, replace the ClusterIssuer with an ACME issuer (Let's Encrypt) or an internal CA. cert-manager handles the renewal automatically in both cases - the application and ingress config do not change.
