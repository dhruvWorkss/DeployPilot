# Operations runbook

## Rollout is stuck

1. Inspect the deployment condition and events.
2. Check image pull, scheduling, readiness, and quota failures.
3. Run `python incident_cli.py --file deployment.log` for classification.
4. If the health deadline has elapsed, undo the revision and confirm the previous ReplicaSet becomes available.

## Elevated error rate after rollout

1. Compare the release marker with request error and latency charts.
2. Verify upstream dependencies before assuming the new image is defective.
3. Roll back when the burn-rate gate remains violated for its configured window.
4. Preserve logs, image digest, configuration checksum, and commit SHA in the incident.

## Database unavailable

The API readiness endpoint fails while liveness remains successful. Traffic is removed without restarting a healthy process. Restore connectivity, validate migrations, and only then re-enable mutations.

## Recovery objective

Deployment metadata is backed up with PostgreSQL. Runtime desired state remains declarative in Git and can be recreated using Terraform and Kubernetes manifests.
