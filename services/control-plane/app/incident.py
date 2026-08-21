import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    category: str
    title: str
    severity: str
    patterns: tuple[str, ...]
    recommendations: tuple[str, ...]


RULES = (
    Rule(
        "image_pull",
        "Container image could not be pulled",
        "high",
        (r"imagepullbackoff", r"errimagepull", r"manifest unknown"),
        (
            "Verify the image name, digest, and registry credentials.",
            "Confirm the node can reach the registry and retry the rollout.",
        ),
    ),
    Rule(
        "crash_loop",
        "Workload is repeatedly crashing",
        "critical",
        (r"crashloopbackoff", r"back-off restarting failed container", r"exit code [1-9]"),
        (
            "Inspect the previous container logs and termination reason.",
            "Validate required secrets, configuration, and startup dependencies "
            "before redeploying.",
        ),
    ),
    Rule(
        "out_of_memory",
        "Container exceeded its memory limit",
        "critical",
        (r"oomkilled", r"out of memory", r"exit code 137"),
        (
            "Compare working-set memory with the configured limit.",
            "Fix the memory regression or adjust requests and limits using observed usage.",
        ),
    ),
    Rule(
        "readiness",
        "New pods failed readiness checks",
        "high",
        (r"readiness probe failed", r"unhealthy.*readiness", r"context deadline exceeded"),
        (
            "Call the readiness endpoint from inside the pod and inspect dependency checks.",
            "Increase probe delay only when startup duration is expected and measured.",
        ),
    ),
    Rule(
        "scheduling",
        "Pods cannot be scheduled",
        "high",
        (r"failedscheduling", r"insufficient (cpu|memory)", r"didn't match pod"),
        (
            "Inspect node capacity, affinity, taints, and namespace quota.",
            "Right-size resource requests or add capacity before retrying.",
        ),
    ),
    Rule(
        "permission",
        "Runtime identity lacks permission",
        "high",
        (r"forbidden", r"permission denied", r"unauthorized"),
        (
            "Identify the denied action from the audit or API error.",
            "Grant the narrowest required role to the workload identity.",
        ),
    ),
    Rule(
        "network",
        "Service dependency is unreachable",
        "medium",
        (r"connection refused", r"no route to host", r"temporary failure in name resolution"),
        (
            "Verify service endpoints, DNS, network policies, and dependency health.",
            "Use a bounded retry with backoff only for transient failures.",
        ),
    ),
)


def analyze_logs(logs: str) -> dict[str, object]:
    normalized = logs.lower()
    ranked: list[tuple[int, Rule, list[str]]] = []
    for rule in RULES:
        evidence = []
        for pattern in rule.patterns:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                evidence.append(match.group(0)[:160])
        if evidence:
            ranked.append((len(evidence), rule, evidence))
    if not ranked:
        return {
            "title": "No known failure signature detected",
            "category": "unknown",
            "severity": "low",
            "confidence": "low",
            "evidence": ["No rule matched the supplied logs."],
            "recommendations": [
                "Correlate application logs with Kubernetes events and deployment metrics.",
                "Add a reviewed classifier rule after the root cause is confirmed.",
            ],
        }
    score, rule, evidence = max(ranked, key=lambda item: item[0])
    confidence = "high" if score >= 2 else "medium"
    return {
        "title": rule.title,
        "category": rule.category,
        "severity": rule.severity,
        "confidence": confidence,
        "evidence": evidence,
        "recommendations": list(rule.recommendations),
    }
