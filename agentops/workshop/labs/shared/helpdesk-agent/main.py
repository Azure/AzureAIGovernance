"""Foundry Responses-protocol host, following the official local-tools sample."""

import os
from pathlib import Path

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

from tools import check_service_status, create_ticket, lookup_article


def main():
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )
    agent = Agent(
        client=client,
        instructions=Path(__file__).with_name("instructions.md").read_text(encoding="utf-8"),
        tools=[tool(approval_mode="never_require")(function) for function in
               (lookup_article, check_service_status, create_ticket)],
        default_options={"store": False},
    )
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
