# Security

## Reporting a vulnerability

If you believe you have discovered a security issue, please open a private security advisory on the repository or email the maintainers directly. Please do **not** disclose vulnerabilities publicly until a fix has been released.

When reporting, please include:

- A clear description of the issue and impact.
- Steps to reproduce or proof-of-concept code.
- The git commit or release where the issue was observed.

## Scope

This application is a **decision-support tool only**. It must not:

- Place trades.
- Execute orders.
- Connect to broker order execution endpoints.
- Store broker execution credentials.
- Provide UI controls that execute trades.
- Claim guaranteed returns.

Any pull request that violates these rules will be rejected. Reports that show such functionality being introduced are treated as critical security issues.

## Practices

- All secrets must be provided via environment variables (`backend/.env.example`).
- Live data providers and LLM providers require explicit API keys; without them the system uses deterministic mock providers labeled `MOCK_DATA`.
- The backend uses structured JSON logging with request IDs. Do not log secrets, API keys, or PII.
- Hard risk gates (data quality, news blackout, spread, reward/risk, mock data, paper validation mode) always override AI output through the Final Arbiter.

## Supported versions

The MVP tracks the latest commit on `main`. There are no LTS branches yet.
