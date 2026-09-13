"""
Customer Support AI Agent — Starter Code
==========================================
Your task is to complete this file by implementing all sections marked
with # TODO comments.

Reference the step-by-step solution files and INSTRUCTIONS.md for guidance.
Do NOT copy the solution directly — work through each section yourself.

Run locally (after filling in config values):
  uv run main.py '{"prompt": "Hello", "customer_id": "CUST-123", "session_id": "s1"}'

Deploy to AgentCore:
  agentcore deploy

Invoke deployed agent:
  agentcore invoke '{"prompt": "Hello", "customer_id": "CUST-123", "session_id": "s1"}'
"""

# ── Imports ───────────────────────────────────────────────────────────────────
# These imports are provided. Do not remove them.
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamable_http_client
import argparse, json
import os, asyncio, boto3
from strands.hooks import (
    HookProvider, AfterInvocationEvent, HookRegistry, MessageAddedEvent,
)
import logging
import uuid
from typing import Dict
from bedrock_agentcore.tools.code_interpreter_client import code_session
from strands_tools.browser import AgentCoreBrowser


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("CSAI_Agent")

# ── TODO 1 — App Initialisation ───────────────────────────────────────────────
# Create a BedrockAgentCoreApp instance.
# This registers the ASGI server for AgentCore deployment.
# There must be exactly one instance per deployment.
#
# Hint: app = BedrockAgentCoreApp()

# TODO: Create the BedrockAgentCoreApp instance
app = BedrockAgentCoreApp()  # Replace this line


# Suppress interactive tool-consent prompts (required in headless deployments).
os.environ["BYPASS_TOOL_CONSENT"] = "true"


# ── TODO 2 — Configuration ────────────────────────────────────────────────────
# Replace the placeholder strings with your actual AWS resource values.
# You collected these in Part 1 of the INSTRUCTIONS.
#
# GATEWAY_URL format: https://<alias>.gateway.bedrock-agentcore.<region>.amazonaws.com/mcp
# KB_ID       format: 10-character alphanumeric string from the KB console
# REGION:     your AWS region, e.g. "us-east-1"
# MEMORY_ID   format: shown in the AgentCore Memory console

GATEWAY_URL = os.getenv("GATEWAY_URL", "")
KB_ID       = os.getenv("KB_ID", "")
REGION      = os.getenv("AWS_REGION", "us-east-1")
MEMORY_ID   = os.getenv("MEMORY_ID", "")

# ── TODO 3 — Model and Clients ────────────────────────────────────────────────
# Create:
#   1. A BedrockModel using model_id "global.amazon.nova-2-lite-v1:0"
#   2. A MemoryClient with region_name=REGION
#   3. A boto3 client for the "bedrock-agent-runtime" service in REGION
#
# Hint: model = BedrockModel(model_id=model_id)

model_id = "global.amazon.nova-2-lite-v1:0"

# TODO: Create the BedrockModel instance
model = BedrockModel(
    model_id=model_id
)

# TODO: Create the MemoryClient instance
memory_client = MemoryClient(
    region_name=REGION
)

# TODO: Create the boto3 bedrock-agent-runtime client
_bedrock_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)

# ── TODO 4 — Namespace Helper ─────────────────────────────────────────────────
# Implement get_namespaces() to return a dict mapping strategy type to
# namespace template string.
#
# Steps:
#   1. Call mem_client.get_memory_strategies(memory_id) to get strategy list
#   2. Return a dict: { strategy["type"]: strategy["namespaces"][0] for each strategy }
#
# Example output:
#   { "SEMANTIC": "cs_agent/{actorId}/facts",
#     "USER_PREFERENCE": "cs_agent/{actorId}/preferences" }

def get_namespaces(mem_client: MemoryClient, memory_id: str) -> Dict:
    """Return a dict mapping strategy type → namespace template string."""

    strategies = mem_client.get_memory_strategies(memory_id)

    namespaces = {}

    for strategy in strategies:
        strategy_type = strategy.get("type")

        namespace_list = (
            strategy.get("namespaceTemplates")
            or strategy.get("namespaces")
            or []
        )

        if strategy_type and namespace_list:
            first_namespace = namespace_list[0]

            # Newer API responses may return namespace templates
            # as objects rather than plain strings.
            if isinstance(first_namespace, dict):
                namespace_template = (
                    first_namespace.get("namespace")
                    or first_namespace.get("template")
                    or first_namespace.get("namespaceTemplate")
                )
            else:
                namespace_template = first_namespace

            if namespace_template:
                namespaces[strategy_type] = namespace_template

    return namespaces

# ── TODO 5 — Memory Hook ──────────────────────────────────────────────────────
# Implement MemoryHook, a HookProvider subclass that adds long-term memory.
#
# The class needs:
#   __init__(self, actor_id, session_id, memory_client, memory_id)
#     — store all four as instance attributes
#     — call get_namespaces() and store the result as self.namespaces
#
#   retrieve_customer_context(self, event: MessageAddedEvent)
#     — only runs for plain-text user messages (not tool results)
#     — for each strategy namespace, call memory_client.retrieve_memories(
#          memory_id, namespace (formatted with actorId), query, top_k=5)
#     — collect non-empty memory texts tagged with their strategy type
#     — if any memories found, prepend them to the user message as:
#          "Customer Context:\n<memories>\n\n<original_message>"
#
#   save_support_interaction(self, event: AfterInvocationEvent)
#     — walk the message list backwards to find the last plain-text user
#       query and the last assistant response
#     — call memory_client.create_event(memory_id, actor_id, session_id,
#          messages=[(customer_query, "USER"), (agent_response, "ASSISTANT")])
#
#   register_hooks(self, registry: HookRegistry)
#     — register retrieve_customer_context on MessageAddedEvent
#     — register save_support_interaction on AfterInvocationEvent

class MemoryHook(HookProvider):
    """Long-term memory hook for the customer support agent."""

    def __init__(
        self,
        actor_id: str,
        session_id: str,
        memory_client: MemoryClient,
        memory_id: str,
    ):
        self.actor_id = actor_id
        self.session_id = session_id
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.namespaces = get_namespaces(memory_client, memory_id)

    def retrieve_customer_context(self, event: MessageAddedEvent):
        """Retrieve relevant memories and prepend them to the user message."""
        
        messages = event.agent.messages

        if not messages:
            return

        message = messages[-1]

        if message.get("role") != "user":
            return

        content = message.get("content", [])

        if not content:
            return

        # Ignore tool-result messages
        if any(isinstance(item, dict) and "toolResult" in item for item in content):
            return

        query_parts = []

        for item in content:
            if isinstance(item, dict) and "text" in item:
                query_parts.append(item["text"])

        query = "\n".join(query_parts).strip()

        if not query:
            return

        memories = []

        for strategy_type, namespace_template in self.namespaces.items():
            namespace = namespace_template.format(actorId=self.actor_id)

            results = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=namespace,
                query=query,
                top_k=5,
            )

            for result in results:
                memory_text = result.get("content", {}).get("text", "")

                if memory_text:
                    memories.append(f"[{strategy_type}] {memory_text}")

        if memories:
            context = "\n".join(memories)

            enriched_query = (
                f"Customer Context:\n{context}\n\n"
                f"{query}"
            )

            message["content"] = [{"text": enriched_query}]

    def save_support_interaction(self, event: AfterInvocationEvent):
        """Save the completed turn to memory after the agent responds."""

        messages = event.agent.messages

        customer_query = None
        agent_response = None

        for message in reversed(messages):
            role = message.get("role")
            content = message.get("content", [])

            text_parts = []

            for item in content:
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])

            text = "\n".join(text_parts).strip()

            if not text:
                continue

            if role == "assistant" and agent_response is None:
                agent_response = text

            elif role == "user" and customer_query is None:
                # Ignore tool-result messages
                if any(
                    isinstance(item, dict) and "toolResult" in item
                    for item in content
                ):
                    continue

                customer_query = text

            if customer_query and agent_response:
                break

        if customer_query and agent_response:
            self.memory_client.create_event(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                messages=[
                    (customer_query, "USER"),
                    (agent_response, "ASSISTANT"),
                ],
            )

    def register_hooks(self, registry: HookRegistry) -> None:  # type: ignore
        """Register both memory callbacks."""

        registry.add_callback(
            MessageAddedEvent,
            self.retrieve_customer_context,
        )

        registry.add_callback(
            AfterInvocationEvent,
            self.save_support_interaction,
        )

# ── TODO 6 — Knowledge Base Tool ─────────────────────────────────────────────
# Implement search_knowledge_base(query) using the @tool decorator.
#
# Steps:
#   1. Guard: if KB_ID is empty return "Knowledge base not configured."
#   2. Call _bedrock_runtime.retrieve(
#          knowledgeBaseId=KB_ID,
#          retrievalQuery={"text": query}
#      )
#   3. Extract resp["retrievalResults"]; return a message if empty
#   4. Join the text chunks with "\n---\n" and return the result
#
# The docstring is the tool description — the model uses it to decide when
# to call this tool, so keep it clear and accurate.

@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the Amazon product catalog and support knowledge base.
    Use this for product specifications, return policies, warranty
    information, loyalty program details, and order status definitions.

    Args:
        query: The question or topic to search for

    Returns:
        Relevant information retrieved from the knowledge base
    """
    if not KB_ID or KB_ID == "<kbid>":
        return "Knowledge base not configured."

    try:
        response = _bedrock_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={
                "text": query
            }
        )

        results = response.get("retrievalResults", [])

        if not results:
            return "No relevant information found in the knowledge base."

        chunks = []

        for result in results:
            content = result.get("content", {})
            text = content.get("text", "")

            if text:
                chunks.append(text)

        if not chunks:
            return "No relevant information found in the knowledge base."

        return "\n---\n".join(chunks)

    except Exception as e:
        logger.exception("Knowledge base retrieval failed")
        return f"Knowledge base search failed: {str(e)}"

# ── TODO 7 — Loyalty Discount Tool (Code Interpreter) ────────────────────────
# Implement calculate_loyalty_discount() using the @tool decorator.
#
# The tool must:
#   1. Build a self-contained Python code string that:
#        • Defines earn_rates: {"standard": 1, "device": 2, "fresh": 5}
#        • Defines tier_rates: {"Silver": 0.00, "Gold": 0.10, "Platinum": 0.15}
#        • Calculates points_redeemed (floor to nearest 500, cap at 50% of order)
#        • Calculates tier_discount (applied to subtotal after points)
#        • Calculates final_total, total_savings, points_earned, remaining_points
#        • Prints a JSON result dict
#   2. Execute the code with code_session(REGION).invoke("executeCode", {...})
#      using language="python" and clearContext=True
#   3. Return the first result event as a JSON string
#   4. Include a fallback that computes only the tier discount if the
#      Code Interpreter is unavailable


@tool
def calculate_loyalty_discount(
    loyalty_points: int,
    tier: str,
    order_total: float,
    product_category: str = "standard",
) -> str:
    """
    Calculate the loyalty discount for a customer order using the
    AgentCore Code Interpreter. Runs exact arithmetic in a secure sandbox.

    Args:
        loyalty_points: Customer's current loyalty point balance
        tier: Customer loyalty tier: Silver, Gold, or Platinum
        order_total: Total value of the customer order
        product_category: Product category used to calculate points earned.
                          Expected values are standard, device, or fresh.

    Returns:
        A JSON string containing discount calculations and loyalty details
    """

    try:
        code = f"""
import json
import math

loyalty_points = {loyalty_points}
tier = {tier!r}
order_total = {order_total}
product_category = {product_category!r}

earn_rates = {{
    "standard": 1,
    "device": 2,
    "fresh": 5
}}

tier_rates = {{
    "Silver": 0.00,
    "Gold": 0.10,
    "Platinum": 0.15
}}

# Normalize incoming values
tier_name = tier.title()
category = product_category.lower()

# ------------------------------------------------------------
# 1. Calculate redeemable loyalty points
# ------------------------------------------------------------

# Loyalty points can only be redeemed in blocks of 500.
points_redeemed = (loyalty_points // 500) * 500

# Convert points to monetary discount.
# 100 points = $1
points_discount = points_redeemed / 100.0

# Loyalty point redemption cannot exceed 50% of the order total.
max_points_discount = order_total * 0.50

if points_discount > max_points_discount:
    max_redeemable_points = (
        math.floor((max_points_discount * 100) / 500) * 500
    )

    points_redeemed = max_redeemable_points
    points_discount = points_redeemed / 100.0


# ------------------------------------------------------------
# 2. Subtotal after applying loyalty points
# ------------------------------------------------------------

subtotal_after_points = max(
    order_total - points_discount,
    0
)


# ------------------------------------------------------------
# 3. Apply loyalty tier discount
# ------------------------------------------------------------

tier_rate = tier_rates.get(
    tier_name,
    0.00
)

tier_discount = (
    subtotal_after_points * tier_rate
)


# ------------------------------------------------------------
# 4. Calculate final order total
# ------------------------------------------------------------

final_total = max(
    subtotal_after_points - tier_discount,
    0
)


# ------------------------------------------------------------
# 5. Calculate total savings
# ------------------------------------------------------------

total_savings = (
    order_total - final_total
)


# ------------------------------------------------------------
# 6. Calculate loyalty points earned
# ------------------------------------------------------------

earn_rate = earn_rates.get(
    category,
    earn_rates["standard"]
)

points_earned = math.floor(
    final_total * earn_rate
)


# ------------------------------------------------------------
# 7. Calculate remaining loyalty points
# ------------------------------------------------------------

remaining_points = (
    loyalty_points
    - points_redeemed
    + points_earned
)


# ------------------------------------------------------------
# 8. Build result
# ------------------------------------------------------------

result = {{
    "original_total": round(order_total, 2),
    "loyalty_points_available": loyalty_points,
    "points_redeemed": points_redeemed,
    "points_discount": round(points_discount, 2),
    "subtotal_after_points": round(subtotal_after_points, 2),
    "tier": tier_name,
    "tier_discount_pct": round(tier_rate * 100, 2),
    "tier_discount": round(tier_discount, 2),
    "final_total": round(final_total, 2),
    "total_savings": round(total_savings, 2),
    "product_category": category,
    "earn_rate": earn_rate,
    "points_earned": points_earned,
    "remaining_points": remaining_points
}}

print(json.dumps(result))
"""

        # Execute the calculation inside AgentCore Code Interpreter
        with code_session(REGION) as session:
            response = session.invoke(
                "executeCode",
                {
                    "code": code,
                    "language": "python",
                    "clearContext": True,
                },
            )

            for event in response["stream"]:
                if "result" in event:
                    result = event["result"]

                    structured_content = result.get("structuredContent", {})
                    stdout = structured_content.get("stdout", "").strip()

                    if stdout:
                        return stdout

                    return json.dumps(result, default=str)

        return json.dumps(
            {
                "error": "Code Interpreter returned no result."
            }
        )

    except Exception as e:
        logger.warning(
            "Code Interpreter unavailable. "
            "Using fallback tier discount calculation. Error: %s",
            e,
        )

        # --------------------------------------------------------
        # Fallback calculation
        # Only calculate tier discount as required by instructions
        # --------------------------------------------------------

        tier_rates = {
            "Silver": 0.00,
            "Gold": 0.10,
            "Platinum": 0.15,
        }

        tier_name = tier.title()

        tier_rate = tier_rates.get(
            tier_name,
            0.00
        )

        tier_discount = (
            order_total * tier_rate
        )

        final_total = max(
            order_total - tier_discount,
            0
        )

        fallback_result = {
            "original_total": round(order_total, 2),
            "tier": tier_name,
            "tier_discount_pct": round(tier_rate * 100, 2),
            "tier_discount": round(tier_discount, 2),
            "final_total": round(final_total, 2),
            "fallback": True,
            "message": (
                "Code Interpreter was unavailable. "
                "Only the loyalty tier discount was calculated."
            ),
        }

        return json.dumps(fallback_result)

# ── TODO 8 — Agent Entrypoint ─────────────────────────────────────────────────
# Implement the invoke() function decorated with @app.entrypoint.
#
# Steps:
#   1. Extract user_input, actor_id, and session_id from the payload
#      (generate a UUID if session_id is missing)
#   2. Instantiate MemoryHook for this actor/session
#   3. Instantiate AgentCoreBrowser(region=REGION)
#   4. Build the tools list: [search_knowledge_base, calculate_loyalty_discount,
#                              agent_core_browser.browser]
#   5. Connect to the Gateway via MCPClient, load gateway_tools, extend tools list
#   6. Create and invoke the Agent with all tools, hooks, and system_prompt
#   7. Return the text from the first content block of the response
#   8. Handle exceptions gracefully

@app.entrypoint
async def invoke(payload, context=None):
    """
    Main handler called by AgentCore for every incoming request.

    Expected payload keys:
      prompt      (str, required) — the customer's message
      customer_id (str, optional) — unique customer identifier
      session_id  (str, optional) — session identifier; generated if absent
    """
    try:
        # ------------------------------------------------------------
        # 1. Extract user input, customer ID, and session ID
        # ------------------------------------------------------------
        user_input = payload.get("prompt", "").strip()

        if not user_input:
            return "Please provide a customer support question."

        actor_id = payload.get(
            "customer_id",
            "anonymous-customer"
        )

        session_id = payload.get(
            "session_id"
        ) or str(uuid.uuid4())

        # ------------------------------------------------------------
        # 2. Create the memory hook for this actor/session
        # ------------------------------------------------------------
        memory_hook = MemoryHook(
            actor_id=actor_id,
            session_id=session_id,
            memory_client=memory_client,
            memory_id=MEMORY_ID,
        )

        # ------------------------------------------------------------
        # 3. Create AgentCore Browser
        # ------------------------------------------------------------
        agent_core_browser = AgentCoreBrowser(
            region=REGION
        )

        # ------------------------------------------------------------
        # 4. Build the initial tools list
        # ------------------------------------------------------------
        tools = [
            search_knowledge_base,
            calculate_loyalty_discount,
            agent_core_browser.browser,
        ]

        # ------------------------------------------------------------
        # 5. Connect to the AgentCore Gateway using MCP
        # ------------------------------------------------------------
        mcp_client = MCPClient(
            lambda: streamable_http_client(
                GATEWAY_URL
            )
        )

        with mcp_client:
            gateway_tools = mcp_client.list_tools_sync()

            tools.extend(gateway_tools)

            # --------------------------------------------------------
            # 6. Define the system prompt
            # --------------------------------------------------------
            system_prompt = """
You are a helpful customer support AI agent.

Your responsibilities include:
- Answering customer questions using the knowledge base.
- Looking up customer and order information using available Gateway tools.
- Processing refunds and return-label requests using Gateway tools.
- Calculating loyalty discounts when appropriate.
- Using the browser only when necessary.
- Using retrieved customer memory to personalize responses when relevant.

Rules:
- Never invent order, customer, refund, product, or policy information.
- Use tools whenever factual customer or order data is required.
- Use the knowledge base for product specifications, warranty information,
  return policies, loyalty information, and support-policy questions.
- Give clear, concise, customer-friendly answers.
- If required information is unavailable, explain that clearly.
"""

            # --------------------------------------------------------
            # 7. Create the Agent
            # --------------------------------------------------------
            agent = Agent(
                model=model,
                tools=tools,
                hooks=[memory_hook],
                system_prompt=system_prompt,
            )

            # --------------------------------------------------------
            # 8. Invoke the Agent
            # --------------------------------------------------------
            response = await agent.invoke_async(user_input)

            # --------------------------------------------------------
            # 9. Return the first text content block from the response
            # --------------------------------------------------------
            if (
                response
                and response.message
                and response.message.get("content")
            ):
                for block in response.message["content"]:
                    if "text" in block:
                        return block["text"]

            return (
                "The agent completed the request "
                "but returned no text response."
            )

    except Exception as e:
        logger.exception(
            "Customer support agent invocation failed"
        )

        return (
            "I'm sorry, but I couldn't process your request right now. "
            f"Error: {str(e)}"
        )

# ── CLI entry point (do not modify) ──────────────────────────────────────────
def main():
    """Run one invocation from the command line for local testing."""
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=str)
    args = parser.parse_args()
    response = asyncio.run(invoke(json.loads(args.payload)))
    print(response)


if __name__ == "__main__":
    app.run()
    # Uncomment the line below and comment app.run() for local CLI testing:
    # main()
