
"""
Automated tests for MCP tool registration and annotations.

These tests verify tool metadata without invoking AWS services.
"""

import asyncio

import pytest

from mcp_server import mcp


EXPECTED_ANNOTATIONS = {
    "search_knowledge_base": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
    "calculate_loyalty_discount": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
}


@pytest.fixture(scope="module")
def registered_tools():
    """Retrieve the tools registered with the MCP server."""

    tools = asyncio.run(mcp.list_tools())

    return {
        tool.name: tool
        for tool in tools
    }


def test_expected_tools_registered(registered_tools):
    """Verify both expected tools are registered."""

    assert set(registered_tools) == set(EXPECTED_ANNOTATIONS)


@pytest.mark.parametrize(
    "tool_name",
    list(EXPECTED_ANNOTATIONS.keys()),
)
def test_mcp_tool_annotations(registered_tools, tool_name):
    """Verify that each tool exposes the expected MCP annotations."""

    tool = registered_tools[tool_name]

    assert tool.annotations is not None

    actual_annotations = tool.annotations.model_dump(
        by_alias=True,
        exclude_none=True,
    )

    for field, expected_value in EXPECTED_ANNOTATIONS[tool_name].items():
        assert field in actual_annotations
        assert actual_annotations[field] is expected_value


@pytest.mark.parametrize(
    "tool_name",
    list(EXPECTED_ANNOTATIONS.keys()),
)
def test_mcp_tool_has_description(registered_tools, tool_name):
    """Verify each MCP tool has a meaningful description."""

    tool = registered_tools[tool_name]

    assert tool.description
    assert len(tool.description.strip()) >= 20
