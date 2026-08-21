from app.incident import analyze_logs


def test_classifies_crash_loop_with_high_confidence():
    result = analyze_logs("CrashLoopBackOff: back-off restarting failed container")
    assert result["category"] == "crash_loop"
    assert result["confidence"] == "high"


def test_classifies_oom():
    result = analyze_logs("Container terminated OOMKilled with exit code 137")
    assert result["category"] == "out_of_memory"
    assert result["severity"] == "critical"


def test_unknown_logs_are_safe():
    result = analyze_logs("An unusual application-specific condition occurred")
    assert result["category"] == "unknown"
    assert "root cause" in result["recommendations"][1].lower()
