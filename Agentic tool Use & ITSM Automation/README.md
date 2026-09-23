# Agentic AI Tool Use & ITSM Automation

An end-to-end **Agentic AI implementation using Azure OpenAI** that demonstrates how a conversational AI system can securely move beyond information retrieval and perform controlled enterprise actions through **function calling / tool use**.

The project demonstrates a service-desk scenario where an AI agent can:

* Verify a user's identity
* Trigger an MFA notification
* Execute a password-reset workflow
* Enforce verification before privileged actions
* Exchange structured JSON payloads between the AI model and backend systems
* Maintain a multi-turn conversational context
* Provide visibility into AI decisions and backend execution

> **Important:** The current implementation uses mock backend functions for demonstration. No real Active Directory, CUCM, SMS gateway, or production ITSM system is modified.

---

## Architecture

```text
                    ┌──────────────────────┐
                    │       User           │
                    │  Service Desk Chat   │
                    └──────────┬───────────┘
                               │
                               ▼
                 ┌───────────────────────────┐
                 │     Python GUI Client      │
                 │     Tkinter Interface     │
                 └─────────────┬─────────────┘
                               │
                               │ Prompt
                               │ + Tool Schemas
                               ▼
                 ┌───────────────────────────┐
                 │      Azure OpenAI         │
                 │       AI Agent            │
                 │                           │
                 │  Tool Selection / JSON    │
                 │  Function Calling         │
                 └─────────────┬─────────────┘
                               │
                       Tool Call JSON
                               │
                               ▼
                 ┌───────────────────────────┐
                 │    Tool Execution Layer   │
                 │       Python              │
                 └─────────────┬─────────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
      │ Identity     │  │ MFA          │  │ Password Reset  │
      │ Verification │  │ Notification │  │ Workflow        │
      └──────────────┘  └──────────────┘  └─────────────────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                         Tool Result JSON
                               │
                               ▼
                 ┌───────────────────────────┐
                 │      Azure OpenAI         │
                 │   Response Synthesis      │
                 └─────────────┬─────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Natural Language   │
                    │       Response       │
                    └──────────────────────┘
```

---

# 1. Project Objectives

Traditional conversational AI systems primarily provide information.

This implementation demonstrates the next step:

```text
User Request
     │
     ▼
AI Reasoning
     │
     ▼
Tool Selection
     │
     ▼
Structured Function Call
     │
     ▼
Backend Execution
     │
     ▼
Tool Result
     │
     ▼
AI Response
```

The objective is to demonstrate how an Azure OpenAI model can act as a controlled **enterprise execution interface** rather than simply generating text.

---

# 2. Key Concepts Demonstrated

## Function Calling

The AI model receives explicit JSON schemas describing the operations it is allowed to request.

For example:

```json
{
  "type": "function",
  "function": {
    "name": "verify_user_identity",
    "description": "Verifies employee identity via corporate database.",
    "parameters": {
      "type": "object",
      "properties": {
        "employee_id": {
          "type": "string"
        },
        "pin_last_four": {
          "type": "string"
        }
      },
      "required": [
        "employee_id",
        "pin_last_four"
      ],
      "additionalProperties": false
    }
  }
}
```

The model does not directly execute the function.

Instead:

```text
Azure OpenAI
     │
     │ Tool Call
     ▼
Python Application
     │
     │ Validate / Execute
     ▼
Backend System
```

This separation provides an important security boundary between **AI decision-making** and **system execution**.

---

# 3. Available Tools

The application exposes three tools.

### `verify_user_identity`

Used to verify the caller before privileged operations.

Example:

```json
{
  "employee_id": "EMP1042",
  "pin_last_four": "4321"
}
```

Mock successful response:

```json
{
  "status": "success",
  "message": "Identity verified successfully.",
  "username": "jdoe"
}
```

---

### `trigger_mfa_sms`

Used to initiate an out-of-band MFA notification.

Example:

```json
{
  "phone_number": "+971XXXXXXXXX",
  "urgency_level": "high"
}
```

Mock response:

```json
{
  "status": "success",
  "message": "MFA token dispatched securely."
}
```

---

### `execute_password_reset`

Used to initiate a password-reset workflow associated with an ITSM ticket.

Example:

```json
{
  "ticket_id": "INC-88421",
  "username": "jdoe"
}
```

Mock response:

```json
{
  "status": "success",
  "message": "Password successfully reset."
}
```

---

# 4. Security Control

A key requirement is that a password reset must not occur before identity verification.

The system prompt establishes this control:

```text
Never execute a password reset without first verifying the user's identity.
```

The intended workflow is:

```text
Password Reset Request
          │
          ▼
Identity Verification
          │
      ┌───┴────┐
      │        │
    Failed   Success
      │        │
      ▼        ▼
   Stop     Continue
               │
               ▼
        Password Reset
```

This demonstrates a basic **authorization workflow around AI tool use**.

> In a production implementation, this control should not rely solely on the system prompt. Backend authorization must independently enforce the same policy.

---

# 5. Multi-Turn Conversation

The application maintains conversational history.

### Turn 1

User:

```text
Hi - can you please reset my password for CUCM, I'm locked?
```

Expected behavior:

```text
AI identifies that identity verification is required
before a privileged password-reset operation.
```

The AI should request the required verification information rather than immediately executing the reset.

---

### Turn 2

User:

```text
My employee ID is EMP1042 and my PIN digits are 4321.
```

The model can now request:

```text
verify_user_identity
```

Example tool call:

```json
{
  "employee_id": "EMP1042",
  "pin_last_four": "4321"
}
```

The Python application intercepts the request and executes the backend function.

Example execution log:

```text
[AI DECISION] Model requested 1 tool call(s):

-> Function: verify_user_identity

-> Arguments JSON:
{"employee_id":"EMP1042","pin_last_four":"4321"}

[BACKEND EXECUTION]
Database lookup triggered for ID: EMP1042

-> Tool Output Payload:
{
  "status": "success",
  "message": "Identity verified successfully.",
  "username": "jdoe"
}

[AI RESPONSE SYNTHESIS COMPLETE]
```

The tool response is then returned to Azure OpenAI so that the model can generate the final conversational response.

---

# 6. Execution Loop

The core agentic execution pattern is:

```text
1. User sends request
        │
        ▼
2. Application sends:
   - Conversation
   - System instructions
   - Tool definitions
        │
        ▼
3. Azure OpenAI determines whether
   a tool is required
        │
        ▼
4. Model generates structured
   tool call
        │
        ▼
5. Python intercepts tool call
        │
        ▼
6. Application executes backend logic
        │
        ▼
7. Backend returns structured result
        │
        ▼
8. Tool result is added to conversation
        │
        ▼
9. Azure OpenAI receives tool result
        │
        ▼
10. Model generates final response
```

This pattern forms the foundation for integrating AI with enterprise APIs.

---

# 7. Application Interface

The Python application provides two primary views.

### Service Desk Chat

Used to interact with the AI agent.

```text
┌──────────────────────────────────────────┐
│          Service Desk Chat               │
│                                          │
│ User: I need to reset my password        │
│                                          │
│ Agent: I need to verify your identity    │
│        first. Please provide...          │
│                                          │
│ [ Enter request... ]       [Send Prompt] │
└──────────────────────────────────────────┘
```

### Backend Execution Logs

Provides visibility into:

* API requests
* Tool schemas
* AI tool decisions
* Function names
* Function arguments
* Backend execution
* Tool output payloads
* Final AI response synthesis

This makes the execution chain easier to inspect while developing and testing.

---

# 8. Prerequisites

The implementation requires:

* Windows, Linux, or macOS
* Python 3.x
* Azure subscription
* Azure OpenAI / Microsoft Foundry resource
* Deployed Azure OpenAI model
* Azure OpenAI API key
* Network connectivity to the Azure endpoint

Python dependency:

```bash
pip install openai
```

Tkinter is normally included with standard Python installations on Windows.

---

# 9. Configuration

Launch the application:

```bash
python lab3_gui.py
```

> Rename the file if you prefer a project-specific name such as `agentic_itsm.py`.

Enter:

| Setting    | Example                         |
| ---------- | ------------------------------- |
| API Key    | Azure OpenAI API key            |
| Endpoint   | Azure OpenAI / Foundry endpoint |
| Deployment | Your deployed model name        |

Example endpoint:

```text
https://azure-openai-resource-lab3.services.ai.azure.com/
```

Do not commit API keys to GitHub.

For a production implementation, use:

* Environment variables
* Azure Key Vault
* Managed Identity
* Secret management
* RBAC

---

# 10. Recommended Environment Variables

Instead of entering credentials directly into the GUI, production implementations should use environment variables.

Example:

```bash
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_DEPLOYMENT=<your-deployment>
```

Then retrieve them in Python:

```python
api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
```

Never commit `.env` files or API keys to the repository.

Example `.gitignore`:

```text
.env
*.key
secrets/
__pycache__/
```

---

# 11. Project Structure

Recommended repository structure:

```text
agentic-itsm-automation/
│
├── README.md
├── agentic_itsm.py
├── requirements.txt
├── .gitignore
│
├── diagrams/
│   └── architecture.png
│
└── screenshots/
    ├── chat-interface.png
    └── execution-logs.png
```

Example `requirements.txt`:

```text
openai
```

---

# 12. Verification Checklist

Use the following sequence to verify the implementation.

### Test 1 — Direct conversational request

```text
Hi - can you please reset my password for CUCM, I'm locked?
```

Verify that the agent does not immediately execute the password-reset function.

Expected:

```text
Identity verification required
```

---

### Test 2 — Identity verification

```text
My employee ID is EMP1042 and my PIN digits are 4321.
```

Verify:

```text
Function:
verify_user_identity
```

Expected backend result:

```json
{
  "status": "success",
  "username": "jdoe"
}
```

---

### Test 3 — Invalid credentials

Try:

```text
My employee ID is EMP1042 and my PIN digits are 9999.
```

Expected:

```json
{
  "status": "failure",
  "message": "Verification failed."
}
```

The application should not treat the user as verified.

---

### Test 4 — Tool output round trip

Verify the complete sequence:

```text
User
 ↓
Azure OpenAI
 ↓
Tool Call
 ↓
Python Backend
 ↓
Tool Result
 ↓
Azure OpenAI
 ↓
Final Response
```

---

# 13. Production Architecture

The mock backend functions can later be replaced with real enterprise integrations.

```text
                     Azure OpenAI
                           │
                           │ Tool Call
                           ▼
                 ┌─────────────────────┐
                 │ Agent / API Layer   │
                 │                     │
                 │ Authentication      │
                 │ Authorization       │
                 │ Validation          │
                 │ Audit Logging       │
                 │ Rate Limiting       │
                 └──────────┬──────────┘
                            │
             ┌──────────────┼───────────────┐
             │              │               │
             ▼              ▼               ▼
        Identity          MFA             ITSM
        Provider         Provider        Platform
             │              │               │
             ▼              ▼               ▼
          Entra ID       MFA/SMS       ServiceNow
          / AD           Provider      / Other ITSM
                            │
                            ▼
                         CUCM
```

---

# 14. Active Directory / Identity Integration

The mock identity verification function can eventually be replaced by an enterprise identity provider.

Potential implementation:

```text
AI Tool Call
     │
     ▼
Identity API
     │
     ▼
Active Directory / Entra ID
     │
     ▼
Identity Verification Result
```

For legacy Active Directory environments, an application may use LDAP/LDAPS through an appropriate service layer.

For modern cloud environments, Microsoft Graph and Entra ID-based authentication should generally be considered instead of directly exposing domain controllers to an AI application.

---

# 15. CUCM Integration

The password-reset workflow can eventually integrate with Cisco Unified Communications Manager.

Potential architecture:

```text
Azure OpenAI
     │
     ▼
Agent Tool
     │
     ▼
ITSM / Automation API
     │
     ▼
Authorization Check
     │
     ▼
CUCM AXL API
     │
     ▼
Cisco Unified Communications Manager
```

The AI agent should **not** receive unrestricted direct access to CUCM.

A controlled API or automation service should validate:

* User identity
* ITSM ticket
* Authorization
* Requested operation
* Target username
* Scope of the operation
* Audit requirements

before calling CUCM.

---

# 16. Idempotency & Safety

Enterprise automation should account for repeated tool calls.

For example:

```text
User requests password reset
        │
        ▼
ITSM ticket INC-88421
        │
        ▼
Reset requested
        │
        ├── First request → Execute
        │
        └── Duplicate request → Return existing status
```

A production implementation should use an idempotency key such as:

```text
INC-88421 + username + operation
```

This helps prevent duplicate execution when:

* The model retries a tool call
* Network timeouts occur
* The client retries a request
* A workflow is accidentally submitted twice

---

# 17. Zero Trust Considerations

The architecture can be extended using Zero Trust principles.

### Identity

Authenticate the calling application and backend services.

### Least Privilege

Give the agent only the minimum permissions required.

### Explicit Authorization

Do not assume that a valid AI tool call is automatically authorized.

### Network Segmentation

Keep enterprise systems behind controlled APIs and network boundaries.

### Monitoring

Record:

* User request
* Tool selected
* Tool arguments
* Identity used
* Backend response
* Timestamp
* ITSM ticket
* Execution result

### Defense in Depth

Security controls should exist independently of the model.

```text
                AI
                 │
                 ▼
          Tool Definition
                 │
                 ▼
        Application Gateway
                 │
                 ▼
        Authentication
                 │
                 ▼
        Authorization
                 │
                 ▼
          Policy Engine
                 │
                 ▼
        Backend API
                 │
                 ▼
        Enterprise System
```

---

# 18. Important Security Improvements

The current implementation is intentionally simplified for demonstrating function calling.

Before production deployment, consider implementing:

* Managed Identity
* Azure Key Vault
* Entra ID authentication
* RBAC
* Conditional Access
* Strong identity verification
* MFA
* API Management
* Private Endpoints
* Network segmentation
* Input validation
* Output validation
* Rate limiting
* Audit logging
* SIEM integration
* ITSM approval workflows
* Human approval for privileged operations
* Tool allow-lists
* Backend authorization
* Idempotency controls
* Prompt-injection defenses
* Sensitive-data filtering

---

# 19. AI Security Boundary

A key architectural principle is:

> **The AI model decides what tool it wants to use; the application decides whether that tool call is actually allowed to execute.**

For example:

```text
                  AI MODEL
                     │
              "reset_password"
                     │
                     ▼
              Tool Dispatcher
                     │
              ┌──────┴──────┐
              │             │
          Authorized?     Valid?
              │             │
              └──────┬──────┘
                     │
                     ▼
              Policy Engine
                     │
              ┌──────┴──────┐
              │             │
            DENY          ALLOW
              │             │
              ▼             ▼
             STOP       Backend API
```

This prevents the model from becoming the final authority over privileged enterprise operations.

---

# 20. Future Enhancements

Potential extensions include:

### ITSM Integration

```text
ServiceNow
Jira Service Management
BMC Helix
```

### Identity

```text
Microsoft Entra ID
Active Directory
LDAP
Okta
```

### Communications

```text
Cisco CUCM
Webex
Microsoft Teams
Amazon Connect
```

### Security Operations

```text
Microsoft Sentinel
Defender
SOAR
Security APIs
```

### Agent Architecture

The current function-calling model can evolve into a larger architecture:

```text
User
 │
 ▼
Voice / Chat Interface
 │
 ▼
AI Agent
 │
 ├── Knowledge Tool
 │
 ├── Identity Tool
 │
 ├── ITSM Tool
 │
 ├── MFA Tool
 │
 ├── Communications Tool
 │
 └── Security Tool
        │
        ▼
   Policy / Authorization
        │
        ▼
 Enterprise APIs
```

---

# 21. What This Project Demonstrates

This project demonstrates the transition:

```text
Traditional Chatbot
        │
        ▼
Grounded AI / RAG
        │
        ▼
Agentic AI
        │
        ▼
Tool Use
        │
        ▼
Enterprise Automation
```

The important architectural distinction is that **RAG allows an AI system to retrieve information, while tool use allows the system to interact with external services and initiate controlled actions.**

---

# 22. Technology Stack

| Component      | Technology                   |
| -------------- | ---------------------------- |
| AI Model       | Azure OpenAI                 |
| AI Pattern     | Function Calling / Tool Use  |
| Application    | Python                       |
| GUI            | Tkinter                      |
| API SDK        | OpenAI Python SDK            |
| Identity       | Mock → AD / Entra ID         |
| MFA            | Mock → MFA/SMS provider      |
| ITSM           | Mock → ITSM platform         |
| UC Platform    | Mock → Cisco CUCM            |
| Security Model | Zero Trust / Least Privilege |
| Logging        | Application execution logs   |

---

# 23. Disclaimer

This repository is intended for **educational, architectural, and proof-of-concept purposes**.

The included backend functions are mocked and should not be treated as production implementations.

Do not connect the example directly to production Active Directory, CUCM, ITSM, MFA, or other enterprise systems without implementing appropriate authentication, authorization, validation, monitoring, secrets management, and change-control processes.

---

## Author

**Shahzad**

Cloud • AI • Security • Collaboration • Contact Center Architecture

```
Azure | AI | Cloud Security | Zero Trust | Automation | UC/CX
```
