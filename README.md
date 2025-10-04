# HR Automation Multi-Agent System

[](https://github.com/) [](https://opensource.org/licenses/MIT)

A multi-agent automation solution designed to streamline key HR processes, including resume screening, new hire onboarding, and answering company policy questions. This system uses a modular architecture where specialized agents collaborate to perform complex tasks, coordinated by a central orchestrator.

## Description

  - **🤖 Automated Resume Screening:** The **TalentScout** agent intelligently parses resumes, scores them against job descriptions, and provides a ranked shortlist of qualified candidates.
  - **🚀 Dynamic Onboarding Plan Generation:** The **Onboarder** agent creates personalized 30/60/90-day onboarding plans for new hires based on their role and department.
  - **📚 Instant Policy Q\&A:** The **PolicyBot** agent provides immediate and accurate answers to employee questions by searching a dedicated knowledge base of company policies.
  - **🧠 Centralized Memory & Orchestration:** An **Orchestrator** manages the workflow, delegating tasks to the appropriate agent. All interactions are logged by the **Archivist** for context and continuity.

## 🏛️ Architecture Overview

The system is built on a multi-agent model:

  - **Orchestrator:** The "brain" of the operation. It receives all incoming requests and routes them to the correct specialist agent.
  - **TalentScout:** Specializes in analyzing job descriptions and resumes to find the best candidates.
  - **Onboarder:** Specializes in creating structured and comprehensive onboarding plans.
  - **PolicyBot:** Specializes in understanding user queries and retrieving information from a knowledge base.
  - **Archivist (Memory Core):** The central database handler that provides a memory system for all agents, logging interactions and storing results.

## 📁 File Structure

```plaintext
/hr_automation_project/
|
|-- agents/
|   |-- __init__.py
|   |-- base_agent.py
|   |-- orchestrator/
|   |-- talent_scout/
|   |-- onboarder/
|   `-- policy_bot/
|       `-- knowledge_base/
|
|-- core/
|   |-- memory_system/
|   |   `-- archivist.py
|   `-- utils/
|       |-- file_parser.py
|       `-- llm_connector.py
|
|-- data/
|   |-- input_resumes/
|   `-- output_reports/
|
|-- tests/
|   |-- test_talent_scout.py
|   |-- test_onboarder.py
|   `-- test_orchestrator.py
|
|-- config.py
|-- main.py
|-- requirements.txt
`-- README.md
```

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

  - Python 3.9+
  - Git

### Installation

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/your-username/hr_automation_project.git
    cd hr_automation_project
    ```

2.  **Create and activate a virtual environment:**

      * On macOS/Linux:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```
      * On Windows:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4.  **Configure your settings:**

      * Rename `config.py.template` (you'll need to create this file) to `config.py`.
      * Add your API keys and other configuration settings to `config.py`.

    *Example `config.py.template`:*

    ```python
    # /config.py.template

    # LLM API Configuration
    # Example for OpenAI, adapt for Gemini or other models
    LLM_API_KEY = "YOUR_API_KEY_HERE"
    LLM_MODEL_NAME = "gemini-2.5 flash"

    # Database Configuration (Example for SQLite)
    DATABASE_URL = "sqlite:///hr_data.db"

    # File Paths
    RESUME_INPUT_DIR = "data/input_resumes/"
    REPORTS_OUTPUT_DIR = "data/output_reports/"
    ```

## 💻 Usage

The main entry point for the application is `main.py`. You can interact with the system via the command line.

**Example 1: Screen Resumes for a Job**

```sh
python main.py screen --job_desc "path/to/job_description.txt" --resume_dir "data/input_resumes/"
```

**Example 2: Create an Onboarding Plan**

```sh
python main.py onboard --name "Saanvi Desai" --role "Software Engineer" --start_date "2025-10-20"
```

**Example 3: Ask a Policy Question**

```sh
python main.py ask --question "What is the company policy on remote work?"
```

## ✅ Running Tests

To ensure everything is working correctly, run the test suite:

```sh
pytest
```

## 🤝 Contributing

Contributions are welcome\! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some amazing feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.
