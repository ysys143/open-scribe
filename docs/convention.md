# Development Environment and Dependency Policy (English, updated)

## 1. General communication

* Always address the user as **“재솔님”**
* Always respond in **Korean**
* Do not use **emojis**

## 2. Time-sensitive and web information

* Before creating **schedules** (e.g., Gantt charts) or searching the web for up-to-date information, confirm the current system date:

  ```bash
  date "+%Y-%m-%d %H:%M:%S"
  ```
* Perform this only when **needed**

## 3. Python virtual environment

* Always activate the **project-local virtual environment** before running any terminal commands:

  ```bash
  source .venv/bin/activate
  ```
* Do not execute Python commands **outside** the activated `.venv`

## 4. Package management (Python)

* Use **uv** for all Python dependency operations:

  ```bash
  uv pip install <package>
  uv pip install -r requirements.txt
  ```
* **Never** use `pip` directly
* **Never** use `python -m pip install`
* **Never** install packages globally
* If additional dependencies are required:

  1. Update `requirements.txt` first
  2. Install via `uv`
* Keep dependencies **reproducible** and **pinned** in `requirements.txt`

## 5. Java build and dependencies

* Manage Java builds and dependencies with **Gradle**
* Always use the **Gradle Wrapper**:

  ```bash
  ./gradlew <task>
  ```

## 6. Web framework

* Use **FastAPI** by default
* Do not use **Flask** unless explicitly requested

## 7. PDF and document tooling

* Use `pdftotext` to **extract text** from local PDF files
* Use `md_pdf` (Marp alias) to **convert Markdown files** to PDF
* Use **original Marp** for PPTX (or PDF if explicitly requested)

## 8. Engineering quality and design

* Do not remove existing features merely to “fix” errors; implement **proper fixes** that satisfy task requirements
* Avoid **ad-hoc workarounds**; aim for **robust, maintainable solutions**
* Maintain clear **separation of concerns** and follow **SOLID principles**
* Explain structural design decisions (the **why**) in **code comments** or **docstrings**

## 9. Schedule and process

* When writing **development schedules** in documents, do not follow generic timelines
* Adjust schedules to the actual pace of **vibe coding**
* Confirm **system date** when needed (see section 2)
* Communicate in **Korean** to **재솔님**
* Document **design decisions** clearly

## 10. Summary

* **Python**: `.venv` + `uv`, no global installs, no `pip`, no `python -m pip install`, keep `requirements.txt` updated
* **Java**: Gradle (via wrapper)
* **Web**: prefer FastAPI
* **Tools**: `pdftotext`, `md_pdf`, original Marp as specified
* **Process**: confirm system date when needed; communicate in Korean to “재솔님”; consider **vibe coding speed** when planning schedules; document design decisions