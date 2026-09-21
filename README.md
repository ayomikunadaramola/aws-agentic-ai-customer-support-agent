# AWS Agentic AI Customer Support Agent 

![Python Automated Tests](https://github.com/ayomikunadaramola/aws-agentic-ai-customer-support-agent/actions/workflows/tests.yml/badge.svg)


An agentic customer-support application for an e-commerce scenario, built with Amazon Bedrock AgentCore, Strands Agents, Model Context Protocol (MCP), AWS Lambda, Amazon API Gateway, Amazon Bedrock Knowledge Bases, AgentCore Memory, Code Interpreter, and Browser.
The agent routes customer requests to external business tools, retrieves product and policy information, remembers preferences across sessions, calculates loyalty discounts, and accesses web content when needed. This is an educational portfolio project, not a production customer-service system.
Contents
Project overview
Architecture
Capabilities and implementation
Technology stack
Repository structure
Configuration and local setup
Deployment and invocation
Testing and evidence
Engineering decisions and challenges
Security and production considerations
Future improvements
Project context and author
License and disclaimer
Project overview
This project demonstrates how an AI support agent can use tools and managed AWS services instead of attempting to answer every request using model-generated text alone. The simulated online retailer's customers can ask about orders, refunds, returns, products, loyalty benefits, and their saved preferences.
Example requests include:
> Where is my order?
>
> What is the status of my refund?
>
> What are the benefits of the Platinum loyalty tier?
>
> I prefer electronics and fast delivery. What do you remember about my preferences?
>
> Calculate my loyalty discount using 4,250 points.
The agent decides whether to respond conversationally, retrieve information, or invoke an appropriate tool. External actions are demonstrated in the project environment; real-world customer authorization and refund controls would require additional safeguards.
Architecture
```text
Customer request
       |
       v
Amazon Bedrock AgentCore Runtime
       |
       v
Strands Agent + Amazon Nova 2 Lite
       |
       +-- AgentCore Gateway (MCP)
       |      +-- Order-tracking API target
       |      +-- Refund-processing Lambda target
       |
       +-- Amazon Bedrock Knowledge Base (RAG)
       +-- AgentCore Memory (semantic facts and user preferences)
       +-- AgentCore Code Interpreter (loyalty calculations)
       +-- AgentCore Browser (external web content)
```
The agent runs on AgentCore Runtime, loads local and Gateway-provided tools, and uses customer/session context when handling requests.
Capabilities and implementation
Order tracking and refunds
Order tracking: The agent uses an API-backed Gateway tool to retrieve order status and available shipping details such as carrier, tracking number, and estimated delivery date.
Refund operations: Lambda-backed Gateway tools support refund initiation, refund-status lookup, and return-label generation in the simulated support workflow.
Tool discovery: An `MCPClient` connects to AgentCore Gateway, discovers its tools, and adds them to the agent's tool list. This keeps business integrations separate from the agent's conversational logic.
Retrieval-augmented generation
The `search_knowledge_base(query)` Strands tool queries Amazon Bedrock Knowledge Bases and returns retrieved text chunks to the agent. The knowledge base covers product specifications, loyalty-program rules and benefits, order-status definitions, and related support information. The tool also handles missing configuration, empty results, and retrieval errors.
Long-term memory
A `MemoryHook` uses AgentCore Memory to save support interactions and retrieve context for a customer across separate sessions. The memory strategies are `SEMANTIC` and `USER_PREFERENCE`, with namespace patterns:
```text
cs_agent/{actorId}/facts
cs_agent/{actorId}/preferences
```
Using the same customer identifier across sessions enables the agent to recall previously stored preferences, such as an interest in electronics and fast delivery.
Loyalty calculations with Code Interpreter
The `calculate_loyalty_discount` tool executes Python business rules through AgentCore Code Interpreter. Rules include 500-point redemption blocks, a maximum points discount of 50% of the order total, tier discounts applied after points redemption, category-specific earning rates, and updated points balances.
For an order total of $150, 4,250 available points, Gold tier, and the standard category, the demonstrated calculation produces:
Result	Value
Points redeemed	4,000
Points discount	$40.00
Subtotal after points	$110.00
Gold tier discount (10%)	$11.00
Final total	$99.00
Total savings	$51.00
Points earned	99
Remaining points	349
If Code Interpreter is unavailable, the tool returns a limited fallback that calculates only the tier discount and explicitly marks the result as a fallback.
Browser and runtime
AgentCore Browser allows the agent to retrieve information from external web pages. A demonstration retrieved the title and main heading of `https://example.com`. The application uses a `BedrockAgentCoreApp` entry point for managed runtime invocation.
Technology stack
Area	Technology
Language and agent framework	Python; Strands Agents
Foundation model and managed runtime	Amazon Nova 2 Lite; Amazon Bedrock AgentCore Runtime
Tool interoperability	Model Context Protocol (MCP); AgentCore Gateway
Business integrations	AWS Lambda; Amazon API Gateway
Retrieval and memory	Amazon Bedrock Knowledge Bases; AgentCore Memory
Code execution and web access	AgentCore Code Interpreter; AgentCore Browser
Development and deployment	`uv`; AgentCore CLI; AWS CDK
Automated testing	`pytest`; GitHub Actions
Repository structure
```text
aws-agentic-ai-customer-support-agent/
├── .github/workflows/tests.yml    # Automated test workflow
├── agentcore/                     # AgentCore project configuration
├── lambda/
│   ├── order_tracker.py
│   ├── refund_processor.py
│   └── lambda_schema
├── screenshots/                   # Project and deployment evidence
├── tests/
│   ├── test_knowledge_base.py
│   └── test_loyalty_discount.py
├── .env.example                   # Environment-variable template
├── .gitignore
├── EVIDENCE_INDEX.md
├── LICENSE
├── PROJECT_README.md
├── README.md
├── main.py                        # Agent, tools, and runtime entry point
├── product_catalog.txt
├── pyproject.toml
├── reflection.md
├── test_browser.py
└── uv.lock
```
Configuration and local setup
Prerequisites: Python 3.14, `uv`, AWS credentials with permissions for the required services, and provisioned AWS resources for live cloud-backed tests. The repository does not contain reusable deployed AWS infrastructure or active credentials.
Clone the repository and enter its directory:
```bash
   git clone https://github.com/ayomikunadaramola/aws-agentic-ai-customer-support-agent.git
   cd aws-agentic-ai-customer-support-agent
   ```
Install project dependencies:
```bash
   uv sync
   ```
Configure AWS authentication separately. Copy `.env.example` to a local `.env` file and supply values for `GATEWAY_URL`, `KB_ID`, `AWS_REGION`, and `MEMORY_ID` as applicable. Do not commit `.env` or AWS credentials. Ensure the configuration is loaded into the process environment before invoking the agent; the sample file alone does not configure AWS resources.
Validate the Python file and run local automated tests:
```bash
   uv run python -m py_compile main.py
   uv run python -m pytest tests/ -v
   ```
The automated tests mock external services; they do not require the original deployed AWS resources. Live agent invocation and cloud-backed integration tests require your own provisioned resources and appropriate permissions.
Deployment and invocation
The project was deployed during development through the AgentCore CLI. Deployment is not a one-click operation for a new account: configure the required IAM permissions, Gateway targets, Knowledge Base, Memory, and any other service dependencies first. Refer to the AgentCore project configuration and documentation appropriate to your installed CLI version.
The documented project workflow used:
```bash
agentcore validate
agentcore deploy --dry-run --yes
agentcore deploy --yes
agentcore status
```
The project's deployment evidence shows an AgentCore Runtime in the `READY` state at the time of testing. The original cloud resources may no longer be running; the repository and screenshots remain available for review.
Example of a deployed-runtime invocation (CLI syntax depends on the installed AgentCore CLI version):
```bash
agentcore invoke '{"prompt":"What are the benefits of the Platinum loyalty tier?","customer_id":"CUST-123","session_id":"demo-session"}'
```
Use a different `session_id` with the same `customer_id` when testing cross-session memory. Treat sample customer and order identifiers as demonstration data.
Testing and evidence
The Udacity project exercised these capabilities: order tracking through Gateway, refund processing, knowledge-base retrieval, cross-session memory, Code Interpreter calculations, and browser access. Screenshots of these runs and the AgentCore deployment are in `screenshots/`; see `EVIDENCE_INDEX.md` for the evidence mapped to each scenario.
The repository also includes 19 automated pytest cases covering the knowledge-base tool and loyalty-discount logic, including edge cases and the Code Interpreter fallback. Tests mock external calls and run locally and in the GitHub Actions CI workflow on pushes and pull requests targeting `main`. The badge above reports the workflow's current status; it does not imply that live AWS integrations are continuously tested.
Engineering decisions and challenges
MCP-based integrations: Dynamic Gateway tool discovery keeps order and refund tools separate from the main agent implementation.
Grounded retrieval: The Knowledge Base provides controlled source content for product and loyalty-policy questions.
Customer-scoped memory: Distinct customer and session identifiers allow preferences to persist across conversations.
Executable business rules: The loyalty tool uses Python for reproducible calculations and labels its limited fallback explicitly.
During development, the project required migration to the newer AgentCore CLI, installation of CDK/TypeScript tooling, AWS environment bootstrapping, IAM permission adjustments, and a dedicated browser test to address an asynchronous runtime issue. Each relevant capability was retested after the corresponding change.
Security and production considerations
This repository is intended to exclude credentials, local environment files, virtual environments, generated deployment artifacts, and other sensitive runtime state. Review commits and screenshots for sensitive information before publishing changes. Use narrowly scoped IAM permissions and avoid committing account-specific secrets or live tokens.
A production implementation would also need customer authentication and authorization, approval controls for refunds and other sensitive actions, input/output validation, PII and memory-retention policies, rate limits, logging and tracing, cost/latency monitoring, alerts, and human-support escalation. The demonstrated project is not presented as having all of these controls.
Future improvements
Potential next steps include structured response validation, broader unit and integration-test coverage, regression evaluation datasets, observability dashboards, automated deployment, sensitive-action guardrails, and human-agent escalation.
Project context and author
Created as part of an AWS-focused Agentic AI engineering program and developed into a portfolio project demonstrating tool-enabled AI support workflows on AWS.
Ayomikun Adaramola — Senior Data Engineer | AI & Data Engineering
License and disclaimer
Licensed under the MIT License. This is an educational and portfolio project and is not an official Amazon Web Services application, service, or product.