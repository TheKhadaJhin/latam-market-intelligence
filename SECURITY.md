# Security Policy

## Supported version

Security fixes are applied to the latest release on `main`.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability
reporting feature for this repository. Include affected version, reproduction steps, impact,
and any suggested mitigation.

## Operational guidance

- Never commit `.env`, database dumps, tokens, or generated raw payloads containing private data.
- The included World Bank source requires no API key.
- Use a managed secret store for production database credentials.
- Run containers as the non-root application user provided by the Dockerfile.
- Restrict `/metrics` at the network layer when deploying publicly.
- Review dependency and CodeQL alerts before release.
