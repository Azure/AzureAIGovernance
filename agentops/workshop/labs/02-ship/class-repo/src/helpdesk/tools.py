"""Synthetic tools. The candidate deliberately contains two workshop defects."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def variant():
    value = os.environ.get("HELPDESK_VARIANT", "candidate")
    if value not in {"candidate", "baseline"}:
        raise ValueError("HELPDESK_VARIANT must be candidate or baseline")
    return value


def lookup_article(topic: str) -> str:
    articles = json.loads((ROOT / "knowledge.json").read_text(encoding="utf-8"))
    if topic not in articles:
        return json.dumps({"error": "Unknown topic; escalate to Service Desk."})
    article = dict(articles[topic])
    if variant() == "candidate" and topic == "password":
        article.pop("source")
    return json.dumps(article)


def check_service_status(service: str) -> str:
    if service.lower() != "vpn":
        return json.dumps({"error": "Only the simulated VPN service is supported."})
    return json.dumps({"service": "vpn", "status": "operational", "simulated": True})


def create_ticket(category: str) -> str:
    queues = {"vpn": "Network Support", "software": "Software Support",
              "password": "Service Desk"}
    if category not in queues:
        return json.dumps({"error": "Unknown category; no ticket created."})
    queue = queues[category]
    if variant() == "candidate" and category == "vpn":
        queue = "Software Support"
    return json.dumps({"reference": f"SIM-{category.upper()}-001",
                       "queue": queue, "simulated": True})
