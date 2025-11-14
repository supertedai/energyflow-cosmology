## 🛠️ Reproducibility Guide: Running the EFC System

### **1. Purpose**

This guide provides the necessary steps to clone the **Energy-Flow Cosmology (EFC) Computational System** and execute its core validation and build workflows locally. The goal is to ensure **full reproducibility** of published results and to demonstrate the functionality of the system's automated pipelines (GitHub Actions).

### **2. Prerequisites**

To run the full EFC system locally, you need the following software installed:

  * **Git:** For cloning the repository.
  * **Python:** Version **3.8+** (recommended for scientific dependencies).
  * **Docker** (or Podman): Required to run the automated GitHub Actions locally via a tool like `act` (recommended) or similar CI/CD emulation tools, as the workflows are containerized.

### **3. Setup: Cloning and Environment**

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/supertedai/energyflow-cosmology.git
    cd energyflow-cosmology
    ```

2.  **Install Python Dependencies:**
    All Python libraries required for the computational core (`/src/`) and the scripts (`/scripts/`) are listed in the `requirements.txt` file (location assumed).

    ```bash
    # Create a virtual environment (recommended)
    python3 -m venv venv
    source venv/bin/activate 

    # Install dependencies
    pip install -r requirements.txt
    ```

-----

## ⚙️ Execution: Running Core Workflows Locally

The most critical part of the EFC system is its validation and build pipeline, defined in the `.github/workflows/` directory.

### **A. Running Validation Pipelines**

This workflow runs the EFC model against empirical data (e.g., SPARC, JWST) and generates the data and plots found in the `/output/validation/` directory.

| Workflow File | Purpose | Corresponding Script |
| :--- | :--- | :--- |
| `run-validation.yml` | Executes the core validation suite. | `scripts/run_sparc_validation.py` |

**To run the main validation suite:**

1.  **Install/Use `act`:** We recommend using the tool `act` to emulate the GitHub Actions environment locally.
2.  **Execute the workflow:**
    ```bash
    # Assuming 'act' is installed and Docker is running
    act -W .github/workflows/run-validation.yml -j run-validation --container-architecture linux/amd64
    ```
3.  **Check Output:** After successful execution, the generated plots and data files will appear (or be updated) in the `/output/validation/` folder.

### **B. Running the Full System Build (Semantic + API)**

This workflow validates the project's internal structure and updates the machine-readable API.

| Workflow File | Purpose | Key Python Scripts |
| :--- | :--- | :--- |
| `update_efc_system.yml` | Full pipeline: fetches external DOIs, validates schemas, and rebuilds the semantic API. | `scripts/fetch_figshare.py`, `scripts/update_efc_api.py` |

**To run the full build pipeline:**

```bash
act -W .github/workflows/update_efc_system.yml -j update_efc_system --container-architecture linux/amd64
```

  * Upon completion, the API files in `/api/` and the schema files in `/schema/` should be consistent and updated, demonstrating the **Semantic Synchronization** of the project.

-----

## 4\. Verifying Symbiosis & Transparency

The efficacy of the **Human–AI evaluation** (Symbiotic Process) can be verified by inspecting the repository's history and the protocol files:

  * **Review Commit History:** Check the `git log` for commits explicitly referencing **`symbiotic-process`** or **`methodology`**. These commits will show the user introducing structural elements proposed or refined during interaction with the AI co-agent.
  * **Protocol Files:** Read the files in `/methodology/`:
      * `symbiotic-process.md`: Describes the operational concept of the symbiotic loop.
      * `symbiotic-process-llm.md`: Defines the operational constraints and role of the AI, allowing external parties to understand the machine's contribution boundary.

-----
