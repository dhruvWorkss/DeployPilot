# Security policy

Do not report vulnerabilities through public issues. Share the affected component, reproduction steps, impact, and suggested mitigation privately with the repository owner.

## Deployment requirements

- Set `AUTH_DISABLED=false` outside local development.
- Store JWT, database, Jenkins, registry, and cloud credentials in a secret manager.
- Use TLS at ingress and restrict the Kubernetes API by network and identity.
- Grant DeployPilot a namespace-scoped service account unless cluster-wide inventory is explicitly needed.
- Verify and sign release images, pin them by digest, and scan them before promotion.
- Protect Terraform state with encryption, versioning, and limited IAM access.
