# Icebrew

<p align="center">

**Brew your experiments.**

*A configurable, local-first computational research toolkit.*

</p>

---

> Icebrew is an open-source, local-first computational research toolkit designed to bring data analysis, statistical workflows, visualization, sentiment analysis, local AI experimentation, media processing, and reproducible research into a unified command-line environment.

## Overview

Scientific and computational workflows often require researchers to switch between multiple tools, libraries, scripts, environments, and platforms.

Icebrew aims to simplify that process.

Built around a configurable command-line interface, Icebrew is intended to provide a modular environment for computational research while prioritizing local execution, reproducibility, transparency, extensibility, and user control.

Icebrew is designed to grow as a unified toolkit rather than a collection of disconnected utilities.

## Design Principles

- **Local-first:** Local execution is the default philosophy. Cloud services and remote inference are not assumed.
- **Modular:** Functional capabilities are organized into independent modules.
- **Configurable:** Behaviour can be controlled through configuration files, environment variables, and command-line arguments.
- **Reproducible:** Workflows, parameters, outputs, and experimental metadata are intended to be traceable.
- **Transparent:** Computational results should be accompanied by appropriate methodological context and limitations.
- **Lightweight core:** Optional functionality should not unnecessarily burden the base installation.
- **Extensible:** A stable extension interface is planned for additional capabilities.
- **Cross-platform:** Icebrew aims to support Windows, macOS, and Linux.

## Planned Modules

Icebrew is being developed around the following modules.

| Module | Intended functionality |
|---|---|
| `data` | Dataset inspection, profiling, transformation, filtering, missing-value analysis, duplicate detection and export. |
| `stats` | Statistical tests, descriptive statistics, regression, diagnostics, effect sizes and confidence intervals. |
| `plotting` | Statistical and general-purpose data visualization. |
| `sentiment` | Local sentiment analysis and configurable text analysis workflows. |
| `insight` | Structured interpretation of analytical results with methodological safeguards. |
| `ai` | Local AI inference, model management, benchmarking and backend integrations. |
| `media` | Image and video processing, analysis and optional AI-assisted media workflows. |
| `reporting` | Structured research reports incorporating data, analyses, outputs and methodological information. |
| `experiments` | Experiment metadata, configuration, artifacts and reproducibility management. |
| `extensions` | Extensible functionality through a planned extension interface. |
| `diagnostics` | Environment, dependency, installation and backend diagnostics. |

<sub>These modules represent the project's intended scope. Not all modules or capabilities are currently implemented.</sub>

## Architecture

Icebrew is designed as a modular Python application with a command-line interface.

```text
Icebrew
│
├── CLI
│
├── Core
│   ├── Exceptions
│   ├── Utilities
│   └── Security
│
├── Configuration
│
├── Data
├── Statistics
├── Plotting
├── Sentiment
├── Insight
│
├── AI
│   ├── Model Management
│   ├── Inference
│   ├── Backends
│   └── Benchmarks
│
├── Media
│   ├── Image
│   ├── Video
│   └── Analysis
│
├── Reporting
├── Experiments
├── Diagnostics
└── Extensions
```

The architecture is intended to keep functionality separated, facilitate maintenance, and allow optional capabilities to be introduced without making every dependency mandatory.

## Installation

Icebrew is currently under active development.

Installation scripts are being developed for Windows, macOS, and Linux. These scripts have not yet undergone complete cross-platform validation.

### Development installation

A development installation can be performed from a cloned repository using Python and pip.

```bash
git clone https://github.com/SomSubhroN/Icebrew.git
cd Icebrew
```

Create a virtual environment:

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

Install Icebrew:

```bash
python -m pip install --upgrade pip
pip install -e .
```

Run:

```bash
icebrew
```

Or:

```bash
python -m icebrew
```

<sub>Installation instructions are subject to change during development.</sub>

## Command-line Interface

Icebrew currently includes foundational CLI functionality.

### General information

```bash
icebrew info
```

Displays basic information about the current Icebrew installation and runtime environment.

### Diagnostics

```bash
icebrew doctor
```

Performs the currently implemented basic diagnostic checks.

The diagnostic system is intended to expand to cover installation integrity, dependencies, configuration, AI backends, multimedia capabilities, and other relevant components.

### Version

```bash
icebrew version
```

Displays the installed version.

## Configuration

Icebrew is being designed around YAML-based configuration.

The intended configuration hierarchy is:

1. Command-line arguments.
2. Environment variables.
3. User configuration.
4. Built-in defaults.

Configuration validation, versioning, migration, backup, and recovery are planned components of the configuration system.

## Privacy and Local Execution

Icebrew is designed with a local-first approach.

- No telemetry by default.
- No automatic cloud inference.
- No bundled AI model weights.
- User-directed model downloads.
- Explicit integration with remote services, where applicable.
- Local data processing whenever supported by the selected functionality.

Specific privacy and security characteristics may vary depending on the optional backends, extensions, and external services selected by the user.

## Reproducibility and Scientific Integrity

Icebrew aims to support reproducible computational workflows.

The project intends to incorporate:

- Experiment metadata.
- Parameter and configuration tracking.
- Analytical artifacts.
- Structured outputs.
- Methodological context.
- Explicit limitations.
- Reproducibility-oriented reporting.

Icebrew is a computational toolkit, not a substitute for domain expertise, independent verification, statistical judgment, or scientific peer review.

Analytical results should be interpreted within the assumptions and limitations of the methods used.

## Dependencies

Icebrew is developed using Python.

Its core dependencies are intentionally limited. Additional dependencies are expected to be installed only when their corresponding functionality is required.

Optional dependencies may include libraries for:

- Statistical analysis.
- Data manipulation.
- Visualization.
- Sentiment analysis.
- Image processing.
- AI inference.
- Multimedia processing.

Dependency compatibility and platform support are subject to ongoing testing.

## Development

Icebrew is currently under active development.

Contributions, bug reports, suggestions, and constructive discussions are welcome.

Before contributing, please review:

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License](LICENSE)

Issues should preferably include reproducible steps, relevant system information, expected behaviour, and actual behaviour.

Pull requests should aim to remain focused, maintainable, and consistent with the project's design principles.

## Roadmap

The development roadmap broadly includes:

- [x] Initial project structure.
- [x] Foundational CLI.
- [x] Basic `info` command.
- [x] Initial `doctor` diagnostics.
- [x] Structured exception foundation.
- [x] Initial platform installation scripts.
- [ ] Installer lifecycle validation.
- [ ] Configuration system.
- [ ] Centralized error handling.
- [ ] Core data module.
- [ ] Statistical module.
- [ ] Plotting module.
- [ ] Sentiment module.
- [ ] Structured insight engine.
- [ ] Local AI infrastructure.
- [ ] Media processing.
- [ ] Reporting system.
- [ ] Experiment management.
- [ ] Extension system.
- [ ] Cross-platform testing.
- [ ] Release validation.

The roadmap is subject to revision as development progresses.

## License

Icebrew is distributed under the **Apache License 2.0**.

See [LICENSE](LICENSE) for the full license text.

## Citation

If you use Icebrew in research, academic work, software development, or computational experiments, attribution is appreciated.

Citation metadata will be provided through `CITATION.cff` as the project develops.

## Author

**Som Subhro Nath**

Creator and developer of Icebrew.

## Contact

For technical discussions, bug reports, or project-related inquiries, please use the GitHub repository.

---

<p align="center">

**Icebrew — Brew your experiments.**

</p>
