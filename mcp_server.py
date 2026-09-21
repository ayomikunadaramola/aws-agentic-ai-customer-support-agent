
"""
MCP tool server for the AWS Agentic AI Customer Support Agent.

Exposes knowledge-base retrieval and loyalty-discount calculation
with explicit MCP tool annotations.
"""

import asyncio
import json

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

import main


# Initialize the MCP server.
mcp = MCPServer(
    name="AWS Agentic AI Customer Support Tools"
)


@mcp.tool(
    name="search_knowledge_base",
    description=(
        "Search the Amazon product catalog and support knowledge base "
        "for product information, return policies, warranty details, "
        "loyalty benefits, and order status definitions."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def search_knowledge_base(query: str) -> str:
    """Retrieve information from the configured knowledge base."""

    result = main.search_knowledge_base.tool_func(query=query)

    return result


@mcp.tool(
    name="calculate_loyalty_discount",
    description=(
        "Calculate a customer's loyalty discount using available "
        "loyalty points, membership tier, order total, and product "
        "category. This operation does not modify customer records."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def calculate_loyalty_discount(
    loyalty_points: int,
    tier: str,
    order_total: float,
    product_category: str = "standard",
) -> str:
    """Calculate loyalty discounts without modifying customer data."""

    result = main.calculate_loyalty_discount.tool_func(
        loyalty_points=loyalty_points,
        tier=tier,
        order_total=order_total,
        product_category=product_category,
    )

    return result


if __name__ == "__main__":
    mcp.run()