AWS Agentic AI Customer Support Agent
A production-style customer support agent built with Amazon Bedrock AgentCore, Strands Agents, Model Context Protocol (MCP), Amazon Bedrock Knowledge Bases, AgentCore Memory, Code Interpreter, AgentCore Browser, AWS Lambda, and Amazon API Gateway.
The project demonstrates how an AI agent can combine reasoning, retrieval, memory, external tools, deterministic computation, and live web access to complete realistic support tasks.
---
Overview
This project models an AI support assistant for an e-commerce platform.
The agent can:
Track customer orders
Process refunds
Check refund status
Generate return labels
Retrieve product and loyalty information with RAG
Remember customer preferences across sessions
Calculate loyalty discounts with sandboxed Python execution
Browse live websites
Invoke backend tools through an MCP Gateway
Run as a deployed Amazon Bedrock AgentCore Runtime
Rather than relying only on model-generated answers, the agent decides when to call external tools and AWS services to complete each request.
---
Architecture
```text
Customer
   |
   v
Amazon Bedrock AgentCore Runtime
   |
   v
Strands Agent + Amazon Nova 2 Lite
   |
   +---- MCP Gateway
   |       +---- Order Tracking API
   |       +---- Refund Processing Lambda
   |
   +---- Amazon Bedrock Knowledge Base
   |
   +---- AgentCore Memory
   |       +---- Semantic Memory
   |       +---- User Preference Memory
   |
   +---- AgentCore Code Interpreter
   |
   +---- AgentCore Browser
```
---
Core Features
MCP Gateway and External Tools
The agent connects to an AgentCore Gateway using `MCPClient`, discovers available tools, and adds them dynamically to the agent's tool list.
Implemented support operations include:
Order tracking through an API-based Gateway target
Refund processing through an AWS Lambda target
Refund status lookup
Return-label generation
This keeps external integrations modular and easier to extend.
Retrieval-Augmented Generation
The `search_knowledge_base` tool queries an Amazon Bedrock Knowledge Base and returns grounded context to the agent.
The knowledge base is used for:
Product information
Loyalty-tier benefits
Loyalty rules
Order-status definitions
Support policies
This reduces dependence on model-only knowledge and improves answer reliability.
Long-Term Memory
The project uses AgentCore Memory to store and retrieve customer information across separate sessions.
Memory strategies include:
Semantic memory
User preference memory
Example:
```text
Session 1:
"I prefer electronics and I like fast delivery."

Session 2:
"What do you remember about my preferences?"

Agent:
"You prefer electronics products and you like fast delivery."
```
This demonstrates persistent cross-session personalization.
Loyalty Discount Calculation
The `calculate_loyalty_discount` tool executes business rules in AgentCore Code Interpreter.
The calculation handles:
Loyalty point redemption
Minimum redemption thresholds
Redemption caps
Tier-based discounts
Product-category earn rates
Remaining points
Example result:
```text
Original total: $150.00
Points redeemed: 4,000
Points discount: $40.00
Gold discount: $11.00
Final total: $99.00
Total savings: $51.00
Remaining points: 349
```
Using executable Python makes the financial logic deterministic and reproducible.
Web Browsing
The agent uses `AgentCoreBrowser` to retrieve information from live web pages.
A successful browser test retrieved the page title and main heading from `https://example.com`.
AgentCore Deployment
The completed application was deployed to Amazon Bedrock AgentCore Runtime and verified with a `READY` runtime status.
---
Technology Stack
Area	Technology
Language	Python
Agent Framework	Strands Agents
Foundation Model	Amazon Nova 2 Lite
Runtime	Amazon Bedrock AgentCore
Tool Protocol	Model Context Protocol
Gateway	AgentCore Gateway
Serverless	AWS Lambda
API Layer	Amazon API Gateway
Retrieval	Amazon Bedrock Knowledge Bases
Memory	AgentCore Memory
Computation	AgentCore Code Interpreter
Browser	AgentCore Browser
Infrastructure	AWS CDK
Package Management	`uv`
---
Repository Structure
```text
aws-agentic-ai-customer-support-agent/
├── main.py
├── product_catalog.txt
├── pyproject.toml
├── uv.lock
├── test_browser.py
├── .env.example
├── lambda/
│   ├── order_tracker.py
│   ├── refund_processor.py
│   └── lambda_schema
├── agentcore/
│   └── agentcore.json
├── screenshots/
├── EVIDENCE_INDEX.md
├── reflection.md
├── PROJECT_README.md
└── README.md
```
---
Getting Started
Configuration
Create local environment variables based on `.env.example`:
```env
GATEWAY_URL=https://your-gateway-url/mcp
KB_ID=YOUR_KNOWLEDGE_BASE_ID
MEMORY_ID=YOUR_MEMORY_ID
AWS_REGION=us-east-1
```
AWS credentials should be configured separately using an appropriate AWS authentication method.
Install Dependencies
```bash
uv sync
```
Activate the environment if required:
```bash
source .venv/bin/activate
```
Validate the application:
```bash
python -m py_compile main.py
```
---
Deployment
Validate the AgentCore project:
```bash
agentcore validate
```
Run a deployment dry run:
```bash
agentcore deploy --dry-run --yes
```
Deploy:
```bash
agentcore deploy --yes
```
Check runtime status:
```bash
agentcore status
```
A successful deployment returns:
```text
CustomerSupportAgent: Deployed - Runtime: READY
```
---
Example Invocation
```bash
agentcore invoke '{
  "prompt": "What are the benefits of the Platinum loyalty tier?",
  "customer_id": "CUST-123",
  "session_id": "demo-session"
}'
```
---
Testing and Results
The project was validated across the required capability areas:
Test	Capability	Result
1	Order Tracking	Passed
2	Refund Processing	Passed
3	Knowledge Base / RAG	Passed
4	Cross-Session Memory	Passed
5	Loyalty Discount / Code Interpreter	Passed
6	Browser Tool	Passed
Additional deployment evidence confirms:
AgentCore runtime deployment
Gateway-backed tool execution
Knowledge Base retrieval after deployment
Memory extraction and recall
Code Interpreter execution
Supporting evidence is available in:
`EVIDENCE_INDEX.md`
`screenshots/`
---
Engineering Highlights
Dynamic MCP tool discovery keeps external integrations decoupled from the agent.
RAG-based grounding improves response reliability for product and policy questions.
Persistent memory enables customer personalization across separate sessions.
Sandboxed code execution handles financial logic more reliably than free-form LLM arithmetic.
Cloud deployment demonstrates a complete path from local implementation to managed AgentCore Runtime.
---
Security and Production Considerations
The public repository excludes:
AWS access keys
Secret keys
Session tokens
`.env` files
Runtime logs
Virtual environments
Generated deployment state
For production use, the solution should also include:
IAM least privilege
Centralized logging and tracing
Tool latency and failure monitoring
Cost monitoring
PII protection
Input/output validation
Rate limiting
Memory-retention policies
Human escalation workflows
Automated integration testing
---
Future Improvements
Potential enhancements include:
Pydantic-based structured response validation
GitHub Actions CI/CD
Conversation summarization
Automated evaluation datasets
CloudWatch dashboards and alarms
Guardrails for sensitive operations
Human-agent escalation
Multi-agent support workflows
---
Project Context
This project was developed as part of an AWS-focused Agentic AI engineering program and demonstrates hands-on experience with:
Agentic AI
Amazon Bedrock AgentCore
MCP-based tool integration
Retrieval-augmented generation
Long-term memory
Serverless APIs
Sandboxed code execution
Browser automation
IAM and cloud deployment
---
Author
Ayomikun Adaramola  
Senior Data Engineer | AI & Data Engineering
---
Disclaimer
This repository is an educational and portfolio project. It is not an official Amazon Web Services application, service, or product.
