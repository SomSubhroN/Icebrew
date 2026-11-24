# Contributing to Icebrew

Thank you for your interest in contributing to Icebrew.

Icebrew is an open-source, local-first computational research toolkit intended to bring scientific computing, data analysis, AI experimentation, visualization, media processing, and reproducible workflows into a unified command-line environment.

Contributions are welcome, including bug reports, documentation improvements, code contributions, testing, feature proposals, and constructive technical discussions.

This document outlines the contribution process and the standards expected of contributions.

## Before Contributing

Before opening an issue or submitting a pull request:

- Review the [Code of Conduct](CODE_OF_CONDUCT.md).
- Check existing issues and pull requests to avoid duplication.
- Understand the relevant module and its intended scope.
- For substantial changes, open an issue or discussion first to establish the proposed direction.

For significant architectural changes, new dependencies, major functionality, or changes affecting scientific interpretation, discussion before implementation is strongly encouraged.

## Development Environment

Icebrew is developed using Python.

### 1. Clone the repository

```bash
git clone https://github.com/SomSubhroN/Icebrew.git
cd Icebrew
```

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the development dependencies

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

If additional optional dependencies are required for the module being developed, install the relevant dependency group as appropriate.

## Code Standards

Contributions should prioritize clarity, maintainability, correctness, and consistency.

### Python

- Follow established project conventions.
- Write readable and maintainable code.
- Use meaningful variable, function, and class names.
- Prefer type annotations where appropriate.
- Write docstrings for public functions, classes, and modules.
- Avoid unnecessary abstraction.
- Avoid duplicating functionality unnecessarily.
- Do not introduce dependencies without justification.

### Error Handling

- Use Icebrew's structured exception system where appropriate.
- Avoid silently swallowing exceptions.
- Provide actionable error messages.
- Preserve underlying exception context where useful.
- Do not expose secrets, credentials, or sensitive information in logs or error messages.

### Configuration

- Respect the project's configuration hierarchy.
- Avoid introducing hard-coded behaviour that bypasses configuration unnecessarily.
- Configuration changes should be validated.
- Changes to defaults should be clearly documented.
- Avoid silently altering scientific or analytical behaviour.

### Scientific and Computational Integrity

Contributions affecting statistical analysis, data processing, interpretation, AI evaluation, or computational methodology should:

- Clearly define the intended behaviour.
- Document relevant assumptions.
- Avoid overstating conclusions.
- Distinguish observed results from interpretation.
- Avoid introducing misleading statistical or scientific claims.
- Include tests for the relevant computational behaviour.
- Document limitations where appropriate.

## Testing

All contributions should be tested to the extent reasonably applicable.

Run the test suite:

```bash
pytest -v
```

Run linting:

```bash
ruff check .
```

Where applicable, contributors should also test:

- Edge cases.
- Invalid inputs.
- Error handling.
- Platform-specific behaviour.
- Dependency availability.
- Configuration interactions.
- Regression scenarios.

Contributions should not knowingly introduce failing tests.

If a change cannot be tested on a particular platform, disclose that limitation in the pull request.

## Branching

Create a separate branch for your contribution.

```bash
git checkout -b feature/your-feature-name
```

Examples:

```bash
git checkout -b feature/data-profiling
git checkout -b fix/config-validation
git checkout -b docs/installation-guide
```

Avoid making substantial contributions directly on the main branch.

## Commit Messages

Commit messages should be concise, descriptive, and focused on the change.

Examples:

```text
Add dataset profiling functionality
Fix diagnostic dependency check
Improve configuration validation
Add statistical regression tests
Update installation documentation
```

Avoid vague commit messages such as:

```text
Changes
Update
Fix stuff
Final
```

## Pull Requests

Before submitting a pull request:

1. Ensure your branch is based on the latest relevant project branch.
2. Run applicable tests.
3. Run linting.
4. Review your own changes.
5. Remove unrelated modifications.
6. Update documentation where necessary.
7. Provide a clear description of the change.

Pull requests should include:

- A concise title.
- A description of the problem addressed.
- The proposed solution.
- Relevant testing information.
- Any known limitations.
- Documentation updates, where applicable.

Small, focused pull requests are generally preferred over large, unrelated changes.

## Dependencies

New dependencies should be introduced only when reasonably necessary.

Pull requests introducing dependencies should explain:

- Why the dependency is needed.
- What functionality it provides.
- Whether it is mandatory or optional.
- Its licensing implications, where relevant.
- Any compatibility or security considerations.

Dependencies should be evaluated for compatibility with Icebrew's supported environments.

## Security

Do not submit:

- API keys.
- Credentials.
- Private tokens.
- Personal or sensitive data.
- Unnecessary system information.
- Malicious code.
- Unverified binaries.

If you discover a security vulnerability, avoid publicly disclosing exploitable details in an issue.

Report it privately to the project maintainer:

**Som Subhro Nath**  
**Email:** nathsomsubhro7@gmail.com

## Documentation

Documentation contributions are encouraged.

Documentation should:

- Be clear and accurate.
- Reflect the actual implementation.
- Avoid claiming functionality that is not implemented.
- Include relevant examples where useful.
- Identify limitations and prerequisites.

Documentation describing planned functionality should explicitly distinguish it from implemented functionality.

## Licensing

By submitting a contribution, you agree that your contribution may be distributed under the project's **Apache License 2.0**.

You retain copyright in your contributions, subject to the licensing terms under which they are submitted and distributed.

Contributions must not knowingly infringe the intellectual property rights of others.

Contributors are responsible for ensuring that submitted material is appropriately licensed or otherwise legally permissible to contribute.

## Review Process

All contributions are subject to review.

Maintainers may request modifications, clarification, additional testing, documentation, or revisions before accepting a contribution.

A contribution may be declined if it:

- Conflicts with the project's design principles.
- Introduces unnecessary complexity.
- Cannot be adequately maintained.
- Lacks appropriate testing.
- Introduces unacceptable security or licensing risks.
- Does not adequately justify its proposed functionality.

Technical disagreements should be addressed constructively and through evidence, implementation details, and reasonable discussion.

## Questions and Discussions

For feature proposals, questions, bug reports, and technical discussions, use the GitHub repository.

Thank you for helping make Icebrew better.

---

**Icebrew — Brew your experiments.**
