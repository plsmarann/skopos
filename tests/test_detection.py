from skopos.detection import detect_agents
from skopos.models import ProcessInfo


def test_detect_known_model_runtime() -> None:
    processes = [
        ProcessInfo(
            pid=111,
            ppid=1,
            user="tester",
            cpu_percent=0.2,
            mem_percent=1.2,
            command="/usr/local/bin/ollama serve",
            executable="/usr/local/bin/ollama",
        )
    ]

    findings = detect_agents(processes)
    assert len(findings) == 1
    assert "ollama" in findings[0].model_keywords
    assert findings[0].risk_score >= 20


def test_unknown_agent_execution() -> None:
    processes = [
        ProcessInfo(
            pid=222,
            ppid=1,
            user="tester",
            cpu_percent=0.0,
            mem_percent=0.3,
            command="/tmp/ghost-agent --silent",
            executable="/tmp/ghost-agent",
        )
    ]

    findings = detect_agents(processes)
    assert len(findings) == 1
    assert findings[0].unknown_agent_execution is True
    assert findings[0].severity in {"medium", "high"}
