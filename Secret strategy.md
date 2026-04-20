## Secret Management Strategy

This project uses GitHub Actions to create a Kubernetes docker-registry secret for GHCR authentication.

### Production Considerations

In real-world environments, this approach can be improved by:

- Managing secrets via Terraform (IaC)
- Using Vault or External Secrets Operator for dynamic secret injection
- Avoiding long-lived PATs in favor of short-lived credentials (OIDC)

This demonstrates awareness of secure and scalable secret management practices.