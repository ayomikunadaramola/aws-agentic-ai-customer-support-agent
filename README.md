AWS Agentic AI Customer Support Agent
An end-to-end AI customer support system built with Amazon Bedrock AgentCore, Strands Agents, Model Context Protocol (MCP), AWS Lambda, Amazon API Gateway, Amazon Bedrock Knowledge Bases, AgentCore Memory, AgentCore Code Interpreter, and AgentCore Browser.
The project demonstrates how an agentic AI application can combine reasoning, external tools, retrieval-augmented generation, persistent memory, deterministic computation, and live web browsing to handle realistic customer-support workflows.
---
Table of Contents
Project Overview
Business Scenario
Key Capabilities
Architecture
Core Components
Technology Stack
Repository Structure
Configuration
Local Setup
Deployment
Example Invocation
Testing and Evidence
Engineering Decisions
Challenges Encountered
Security Considerations
Production Considerations
Future Improvements
Project Context
Author
Disclaimer
---
Project Overview
The AWS Agentic AI Customer Support Agent is an AI-powered support assistant designed for an e-commerce customer-service environment.
Unlike a basic chatbot that only generates natural-language responses, this agent can:
invoke backend business tools,
retrieve grounded information from a knowledge base,
remember customer preferences across separate sessions,
perform loyalty calculations in a sandboxed Python environment,
browse live websites,
and run as a deployed Amazon Bedrock AgentCore Runtime.
The project focuses on building a practical agentic system in which the model decides when to use tools and external services rather than attempting to answer every request directly.
---
Business Scenario
The agent simulates a customer-support assistant for an online retail platform.
Typical customer requests include:
> "Where is my order?"
> "Process a refund for my order."
> "What is the status of my refund?"
> "Generate a return label."
> "What are the benefits of the Platinum loyalty tier?"
> "I prefer electronics and I like fast delivery."
> "Calculate my loyalty discount using 4,250 points."
For each request, the agent determines whether it should respond conversationally or call one or more external tools.
---
Key Capabilities
Order Tracking
The agent can retrieve order details through a Gateway-backed API tool, including:
order status,
product information,
carrier,
tracking number,
estimated delivery date.
Refund Processing
The agent can use a Lambda-backed Gateway tool to:
initiate refunds,
check refund status,
generate return labels.
Retrieval-Augmented Generation
The agent queries an Amazon Bedrock Knowledge Base for grounded answers about:
products,
loyalty tiers,
loyalty rules,
shipping and order-status definitions,
support information.
Long-Term Memory
The system stores and retrieves information across separate customer sessions using AgentCore Memory.
It supports:
semantic memory,
user preference memory.
Loyalty Discount Calculation
The agent executes business rules using AgentCore Code Interpreter rather than relying on free-form LLM arithmetic.
Web Browsing
The agent can browse a live external webpage using AgentCore Browser and extract relevant content.
Cloud Deployment
The completed application is deployed to Amazon Bedrock AgentCore Runtime and can be invoked through the AgentCore CLI.
---
Architecture
```text
                         ┌──────────────────────────┐
                         │        Customer          │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ Amazon Bedrock AgentCore │
                         │ Runtime                  │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ Strands Agent            │
                         │ Amazon Nova 2 Lite       │
                         └────────────┬─────────────┘
                                      │
             ┌────────────────────────┼─────────────────────────┐
             │                        │                         │
             ▼                        ▼                         ▼
   ┌──────────────────┐    ┌────────────────────┐    ┌──────────────────┐
   │ MCP Gateway      │    │ Bedrock Knowledge  │    │ AgentCore Memory │
   │                  │    │ Base               │    │                  │
   └────────┬─────────┘    └────────────────────┘    └──────────────────┘
            │
      ┌─────┴──────────────┐
      │                    │
      ▼                    ▼
┌───────────────┐   ┌──────────────────┐
│ Order API     │   │ Refund Processing│
│ Target        │   │ Lambda Target    │
└───────────────┘   └──────────────────┘

Additional AgentCore capabilities:
- Code Interpreter
- Browser
```
---
Core Components
1. Amazon Bedrock AgentCore Runtime
The application includes a module-level `BedrockAgentCoreApp` instance.
The runtime entry point is implemented using:
```python
@app.entrypoint
async def invoke(payload):
    ...
```
The module uses:
```python
app.run()
```
as the main runtime entry point.
This allows the application to run as a managed AgentCore Runtime and be invoked remotely.
---
2. Strands Agent
The agent uses the Strands Agents framework as the orchestration layer.
The Strands agent receives:
the user prompt,
customer/session context,
locally defined tools,
Gateway-backed MCP tools,
browser capability,
retrieved memory context.
The model then decides which tools to call based on the user request.
---
3. Model Context Protocol Gateway Integration
The application connects to an AgentCore Gateway through `MCPClient`.
Gateway-backed tools are discovered dynamically:
```python
gateway\_tools = mcp\_client.list\_tools\_sync()
tools.extend(gateway\_tools)
```
This design keeps external integrations modular and avoids tightly coupling the agent to individual APIs.
The project demonstrates two distinct integration patterns:
API-based target for order tracking
Lambda-based target for refund processing
Gateway-backed operations tested successfully include:
order tracking,
refund processing,
refund status lookup,
return-label generation.
---
4. Retrieval-Augmented Generation
The `search\_knowledge\_base` function is implemented as a Strands tool.
The tool:
checks that the Knowledge Base ID is configured,
calls the Amazon Bedrock Retrieve API,
collects retrieved text chunks,
joins the chunks into a formatted response,
returns the grounded context to the agent.
The knowledge base contains information such as:
product specifications,
loyalty-program rules,
loyalty-tier benefits,
order-status definitions.
Example knowledge-base queries tested in the project include:
"What are the benefits of the Platinum loyalty tier?"
product catalog queries for electronics such as the Wireless Headphones Pro.
---
5. Cross-Session Memory
The project implements long-term memory using AgentCore Memory.
The memory resource includes:
SEMANTIC strategy
USER_PREFERENCE strategy
Namespace templates follow the pattern:
```text
cs\_agent/{actorId}/facts
cs\_agent/{actorId}/preferences
```
The application includes:
`get\_namespaces()`
`MemoryHook`
`retrieve\_customer\_context()`
`save\_support\_interaction()`
Customer interactions are persisted using:
```python
memory\_client.create\_event(...)
```
Memory is retrieved using the same customer ID across separate sessions.
Example:
```text
Session 1
Customer:
I prefer electronics and I like fast delivery.
```
Later:
```text
Session 2
Customer:
What do you remember about my preferences?

Agent:
You prefer electronics products and you like fast delivery.
```
This demonstrates genuine cross-session recall rather than temporary in-session conversation history.
---
6. AgentCore Code Interpreter
The `calculate\_loyalty\_discount` tool performs loyalty calculations through sandboxed Python execution.
The business rules include:
points earning rates,
loyalty-tier discounts,
minimum redemption threshold,
maximum redemption cap,
category-specific earn rates,
remaining-point calculations.
Example input:
```text
loyalty\_points = 4250
tier = Gold
order\_total = 150.00
product\_category = standard
```
Example result:
```text
Original order total: $150.00
Points redeemed: 4,000
Points discount: $40.00
Subtotal after points: $110.00
Gold tier discount: 10% ($11.00)
Final total: $99.00
Total savings: $51.00
Points earned: 99
Remaining points: 349
```
The application also includes a fallback calculation path for cases where Code Interpreter is unavailable.
---
7. AgentCore Browser
The project instantiates `AgentCoreBrowser` using the configured AWS region and adds the browser to the agent's tools list.
A live-browser test successfully visited:
```text
https://example.com
```
and retrieved:
```text
Page Title: Example Domain
Main Heading: Example Domain
```
This demonstrates the agent's ability to access external web content when required.
---
Technology Stack
Category	Technology
Programming Language	Python
Agent Framework	Strands Agents
Foundation Model	Amazon Nova 2 Lite
Agent Runtime	Amazon Bedrock AgentCore
Tool Protocol	Model Context Protocol (MCP)
Gateway	Amazon Bedrock AgentCore Gateway
Serverless Compute	AWS Lambda
API Layer	Amazon API Gateway
Retrieval	Amazon Bedrock Knowledge Bases
Memory	Amazon Bedrock AgentCore Memory
Computation	AgentCore Code Interpreter
Browser	AgentCore Browser
Infrastructure	AWS CDK
Package Management	`uv`
Cloud Platform	AWS
---
Repository Structure
```text
aws-agentic-ai-customer-support-agent/
│
├── main.py
├── product\_catalog.txt
├── pyproject.toml
├── uv.lock
├── test\_browser.py
├── .env.example
├── .gitignore
│
├── lambda/
│   ├── order\_tracker.py
│   ├── refund\_processor.py
│   └── lambda\_schema
│
├── agentcore/
│   └── agentcore.json
│
├── screenshots/
│   ├── Agent\_Order\_Tracking\_via\_Gateway\_Success.png
│   ├── Agent\_Refund\_Processing\_via\_Gateway\_Success.png
│   ├── Agent\_Knowledge\_Base\_Retrieval\_Success.png
│   ├── Agent\_Long\_Term\_Memory\_Cross\_Session\_Recall\_Success.png
│   ├── Agent\_Loyalty\_Discount\_Code\_Interpreter\_Success.png
│   ├── Agent\_Browser\_Tool\_External\_Web\_Success.png
│   └── additional deployment evidence
│
├── EVIDENCE\_INDEX.md
├── reflection.md
├── PROJECT\_README.md
└── README.md
```
---
Configuration
The public repository intentionally excludes live AWS credentials and deployed resource identifiers.
Use `.env.example` as a template:
```env
GATEWAY\_URL=https://your-gateway-alias.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
KB\_ID=YOUR\_KNOWLEDGE\_BASE\_ID
AWS\_REGION=us-east-1
MEMORY\_ID=YOUR\_MEMORY\_ID
```
Set the environment variables before running the agent.
AWS credentials should be configured separately using an appropriate AWS authentication mechanism.
---
Local Setup
Prerequisites
You should have:
Python
AWS credentials with the required permissions
`uv`
AgentCore CLI
access to the required AWS services and resources
Install Dependencies
```bash
uv sync
```
Activate the environment if required:
```bash
source .venv/bin/activate
```
Validate the Python Application
```bash
python -m py\_compile main.py
```
---
Deployment
The application was deployed through the AgentCore CLI.
Validate the AgentCore Project
```bash
agentcore validate
```
Perform a Dry Run
```bash
agentcore deploy --dry-run --yes
```
Deploy
```bash
agentcore deploy --yes
```
Check Runtime Status
```bash
agentcore status
```
Successful deployment produced a runtime status of:
```text
CustomerSupportAgent: Deployed - Runtime: READY
```
---
Example Invocation
A deployed runtime can be invoked with:
```bash
agentcore invoke \\
'{
  "prompt": "What are the benefits of the Platinum loyalty tier?",
  "customer\_id": "CUST-123",
  "session\_id": "demo-session"
}'
```
Example order-tracking invocation:
```bash
agentcore invoke \\
'{
  "prompt": "Can you track order ORD-001?",
  "customer\_id": "CUST-123",
  "session\_id": "order-demo"
}'
```
---
Testing and Evidence
The completed project was tested across all major rubric capabilities.
Test	Capability	Status
Test 1	Order Tracking via Gateway	Passed
Test 2	Refund Processing via Gateway/Lambda	Passed
Test 3	Knowledge Base Retrieval / RAG	Passed
Test 4	Cross-Session Long-Term Memory	Passed
Test 5	Loyalty Discount via Code Interpreter	Passed
Test 6	Live Web Browsing	Passed
Additional cloud-deployment evidence includes:
deployed AgentCore Knowledge Base invocation,
deployed Gateway order tracking,
long-term memory extraction,
deployed memory recall,
deployed Code Interpreter loyalty calculation,
AgentCore Runtime `READY` status.
Project screenshots are stored in:
```text
screenshots/
```
A structured index is available in:
`EVIDENCE\_INDEX.md`
---
Engineering Decisions
MCP for External Tool Integration
The Gateway tools are loaded dynamically through MCP instead of being hard-coded directly into the agent.
This improves extensibility because additional external services can be exposed through the Gateway without redesigning the entire agent.
RAG for Grounded Answers
Product and loyalty information is retrieved from an Amazon Bedrock Knowledge Base.
This reduces reliance on model-only knowledge and allows support responses to be grounded in controlled source data.
Persistent Customer Memory
Memory is organized around customer identity rather than a single chat session.
This allows preferences and facts to survive across conversations and enables personalized support experiences.
Code Execution for Business Logic
Loyalty calculations are performed through executable Python code instead of relying on LLM arithmetic.
This provides more deterministic and reproducible results for rules-based calculations.
---
Challenges Encountered
Several technical issues were resolved while building and deploying the project.
AgentCore CLI Migration
The original Starter Toolkit CLI was no longer the recommended deployment path.
The project was migrated to the newer AgentCore CLI.
CDK and TypeScript Dependencies
Deployment initially failed because required TypeScript tooling was unavailable.
The CDK dependencies and TypeScript compiler were installed and validated before rerunning the deployment.
AWS CDK Bootstrap
The AWS environment required CDK bootstrapping before deployment could proceed.
The deployment process was rerun with automatic bootstrapping enabled.
IAM Permissions
The deployed runtime initially lacked permissions for services such as:
AgentCore Memory,
Knowledge Base retrieval,
Code Interpreter.
The runtime role was updated using least-privilege service permissions and each capability was retested.
Browser Async Runtime
Browser testing exposed an asynchronous runtime issue when invoked through a nested `asyncio.run()` command.
A dedicated test script was used instead, allowing the browser tool to complete successfully.
---
Security Considerations
The repository intentionally excludes:
AWS access keys,
AWS secret keys,
AWS session tokens,
`.env` files,
local AWS credential files,
virtual environments,
generated deployment logs,
AgentCore runtime state,
Node.js dependency folders,
generated CDK output.
Environment-specific resource identifiers are loaded from environment variables.
For a production implementation, IAM roles should follow the principle of least privilege and only receive access to the services and resources required by the runtime.
---
Production Considerations
A production-ready version of the agent should include:
centralized application logging,
distributed tracing,
CloudWatch alarms,
tool latency monitoring,
failed-tool-call monitoring,
token and model-cost monitoring,
Code Interpreter usage monitoring,
browser-session monitoring,
API rate limiting,
PII protection,
input and output validation,
customer authentication and authorization,
memory-retention policies,
sensitive-action approval workflows,
human-agent escalation,
automated integration tests,
automated evaluation datasets,
conversation summarization for long-running sessions.
---
Future Improvements
Potential enhancements include:
Pydantic-based structured response validation,
GitHub Actions CI/CD,
automated AgentCore deployment pipelines,
conversation summarization,
automated regression evaluations,
AWS CloudWatch dashboards,
human escalation workflows,
customer sentiment detection,
guardrails for refunds and sensitive operations,
additional MCP Gateway tools,
multi-agent support workflows,
structured observability and cost reporting.
---
Project Context
This project was developed as part of an AWS-focused Agentic AI engineering program.
It demonstrates practical experience with:
Amazon Bedrock AgentCore,
Strands Agents,
Model Context Protocol,
Retrieval-Augmented Generation,
long-term memory,
serverless APIs,
AWS Lambda,
API Gateway,
sandboxed code execution,
browser automation,
IAM permissions,
AWS CDK,
cloud deployment,
production-oriented agent architecture.
---
Recommended GitHub Topics
```text
amazon-bedrock
bedrock-agentcore
agentic-ai
generative-ai
aws
strands-agents
model-context-protocol
mcp
rag
retrieval-augmented-generation
aws-lambda
amazon-api-gateway
python
ai-agents
long-term-memory
code-interpreter
customer-support
cloud-ai
```
---
Author
Ayomikun Adaramola
Senior Data Engineer | AI & Data Engineering
Focus areas:
Data Engineering
Cloud Data Platforms
Artificial Intelligence
Agentic AI
Generative AI
AWS
Python
---
Disclaimer
This repository is an educational and portfolio project created to demonstrate agentic AI engineering concepts and AWS implementation patterns.
It is not an official Amazon Web Services application, service, or product.
