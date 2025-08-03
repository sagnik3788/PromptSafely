# PromptSafely 🛡️

**PromptSafely** is a lightweight privacy gateway API that redacts sensitive information (PII) from user prompts before forwarding them to large language models like OpenAI's GPT. Built for developers and enterprises that prioritize user privacy while leveraging powerful AI capabilities.

---

## 🧠 About the App

PromptSafely helps enforce data privacy by detecting and redacting personally identifiable information (PII) such as:

- Names
- Email addresses
- Phone numbers
- Addresses
- Sensitive keywords or identifiers

Once cleaned, the prompt is safely sent to an LLM like OpenAI GPT for processing. This acts as a middleware API between clients and LLMs.

---

## ⚙️ Tech Stack

- **Python 3.10**
- **FastAPI** – lightweight and async-friendly API framework
- **Gunicorn + UvicornWorker** – production-ready ASGI server
- **Docker** – containerization for consistent deployment
- **GitHub Actions** – CI pipeline to build and push images to Docker Hub
- **PipeCD** – GitOps-based CD tool for automated deployment
- **OpenTofu** – infrastructure provisioning and environment management

---

## 🚀 CI/CD Pipeline

### 🧪 CI: GitHub Actions

Every push to the `main` branch triggers a CI pipeline that:

1. Installs Python dependencies.
2. Lints and checks for errors.
3. Builds a Docker image of the app.
4. Pushes the image to Docker Hub under the tag `sagnik3788/promptsafely:latest`.

📄 `.github/workflows/docker-ci.yml` handles all CI steps.

### ⚙️ CD: PipeCD + OpenTofu

The deployment pipeline is fully GitOps-enabled using PipeCD:

- A **separate EC2 VM** hosts the PipeCD `piped` agent and `control-plane` UI.
- **PipeCD** watches the Git repository for changes and triggers deployment when a new Docker image or manifest is pushed.
- **OpenTofu (Terraform fork)** provisions and manages cloud infrastructure needed for deployment:
  - EC2 instances
  - Security groups
  - Networking
  - DNS (if needed)


---

## 🐳 Docker Usage

To build and run locally:

```bash
# Build Docker image
docker build -t promptsafely:latest .

# Run container
docker run -p 5000:5000 -e OPENAI_API_KEY=<your-key> promptsafely:latest
