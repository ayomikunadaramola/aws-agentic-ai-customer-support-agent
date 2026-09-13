# AWS Agentic AI Customer Support Agent

An end-to-end agentic AI customer support system built with **Amazon Bedrock AgentCore**, **Strands Agents**, **Model Context Protocol (MCP)**, **AWS Lambda**, **Amazon Bedrock Knowledge Bases**, **AgentCore Memory**, **Code Interpreter**, and **AgentCore Browser**.

## Project Overview

This project demonstrates how an AI support agent can combine reasoning, retrieval, memory, external tools, web browsing, and deterministic computation to handle realistic customer-support requests.

The agent can:

- Track customer orders through Gateway-backed tools
- Process refunds and check refund status
- Generate return labels
- Retrieve product and policy information using RAG
- Remember customer preferences across separate sessions
- Calculate loyalty discounts using sandboxed Python execution
- Browse live web pages using AgentCore Browser
- Run as a deployed Amazon Bedrock AgentCore Runtime

## Architecture

```text
Customer
   |
   v
Amazon Bedrock AgentCore Runtime
   |
   +---- Amazon Nova 2 Lite
   |
   +---- MCP Gateway
   |       +---- Order Tracking API
   |       +---- Refund Processing Lambda
   |
   +---- Bedrock Knowledge Base
   |
   +---- AgentCore Memory
   |       +---- Semantic Memory
   |       +---- User Preference Memory
   |
   +---- AgentCore Code Interpreter
   |
   +---- AgentCore Browser


