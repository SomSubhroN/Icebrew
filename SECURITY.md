# Security Policy

## Supported Versions

Icebrew is currently under active development.

Security fixes are generally intended to be applied to the latest maintained version of the project.

| Version | Security support |
|---|---|
| 1.0.x | Under development; support status subject to release policy |
| Earlier or unreleased versions | No formal security support guarantee |

Security support policies may be revised as the project matures.

## Reporting a Vulnerability

If you discover a potential security vulnerability in Icebrew, please report it responsibly.

**Do not publicly disclose exploitable vulnerabilities through GitHub Issues, pull requests, discussions, or other public channels before contacting the maintainer.**

### Private reporting

Contact the project maintainer directly:

**Maintainer:** Som Subhro Nath

**Email:** nathsomsubhro7@gmail.com

Please use a descriptive subject line, such as:

`[SECURITY] Vulnerability report - Icebrew`

### What to include

Where possible, your report should include:

- A description of the vulnerability.
- The affected component, module, version, or commit.
- Steps to reproduce the issue.
- Potential security impact.
- Relevant logs, screenshots, or proof-of-concept material, provided they do not expose sensitive data.
- Any suggested mitigation or remediation, if available.

A clear and reproducible report helps the maintainer assess and address the issue.

## Scope

Security reports may concern, among other things:

- Arbitrary code execution.
- Command injection.
- Unsafe subprocess execution.
- Path traversal.
- Unauthorized access to files or resources.
- Unsafe file handling.
- Malicious or unsafe extension behaviour.
- Dependency vulnerabilities.
- Model download integrity or verification failures.
- Credential or sensitive information exposure.
- Unsafe configuration handling.
- Vulnerabilities involving AI backends or integrations.
- Security issues involving media processing.
- Vulnerabilities affecting installation, update, or uninstallation scripts.
- Other issues that compromise confidentiality, integrity, or availability.

The security implications of third-party backends, extensions, models, dependencies, and external services may also be relevant where they affect Icebrew.

## Responsible Disclosure

Please allow the maintainer reasonable time to investigate, verify, and address a reported vulnerability before public disclosure.

The maintainer will make reasonable efforts to:

- Acknowledge security reports.
- Investigate reported issues.
- Assess their severity and impact.
- Develop or identify appropriate mitigations.
- Communicate relevant updates where reasonably possible.

However, Icebrew currently has no formal security response team, guaranteed response time, or bug bounty programme.

## Security Considerations

Icebrew is designed around a local-first computational workflow. Local-first operation does not automatically guarantee security.

Users should exercise caution when:

- Installing third-party extensions.
- Downloading models from untrusted sources.
- Executing scripts or commands obtained from external sources.
- Processing untrusted datasets or media files.
- Connecting external AI backends or services.
- Providing credentials to third-party integrations.
- Running Icebrew with elevated privileges.

Users should keep their operating system, Python environment, dependencies, and supported Icebrew installations updated.

## Disclosure

Public disclosure of a vulnerability should ideally occur after a fix or mitigation has been made available, or after reasonable coordination with the maintainer.

The maintainer may publish security advisories through GitHub when appropriate.

---

**Icebrew — Brew your experiments.**
