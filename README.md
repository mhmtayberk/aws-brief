<p align="center">
  <h1 align="center">AWS-Brief 🚀</h1>
  <p align="center"><strong>The Elite Cloud Intelligence Feed</strong></p>
  <p align="center">
    <em>Autonomous, AI-Powered, Multi-Channel Intelligence for Cloud Architects & DevOps Teams.</em>
  </p>
  <p align="center">
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
    </a>
    <a href="https://www.docker.com/">
      <img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg" alt="Docker">
    </a>
    <a href="#">
      <img src="https://img.shields.io/badge/AI-Multi--Model-purple.svg" alt="AI Powered">
    </a>
    <a href="./LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
    </a>
  </p>
</p>

<br>

## 🧐 What is this?

**AWS-Brief** is an automated "AI Analyst" that lives in your terminal. It monitors **36+ official AWS feeds** (Security Bulletins, Architecture Blog, etc.), uses advanced AI to filter the noise, and tells you exactly what matters.

> *"Here is the one critical Security update you need to patch today, and here are 4 cost-saving opportunities."*

---

## ✨ Features

<table>
  <tr>
    <td align="center">🧠 <strong>5+ AI Models</strong></td>
    <td align="center">🛡️ <strong>Noise Cancellation</strong></td>
    <td align="center">📢 <strong>Multi-Channel</strong></td>
  </tr>
  <tr>
    <td>Switch instantly between <strong>Ollama, OpenAI, Anthropic, Gemini, Groq</strong>. Privacy-first local inference supported.</td>
    <td><strong>Granular Regex Filtering</strong> to mute standard updates. <strong>Smart Init</strong> prevents historical spam.</td>
    <td>Rich notifications on <strong>Slack, Teams, Discord, and Email</strong>.</td>
  </tr>
</table>

---

## 🚀 Installation & Usage

### Docker

The easiest way to run. Handles database and auto-restarts.

```bash
git clone https://github.com/mhmtayberk/aws-brief.git
cd aws-brief
cp .env.example .env 
# Edit .env and filters.yaml.example

docker-compose up -d --build
```

#### Useful Docker Commands

```bash
# View Logs (Watch the AI work)
docker-compose logs -f app

# Run a manual scan immediately
docker-compose exec app python main.py scan

# Send a Weekly Digest manually
docker-compose exec app python main.py send-digest --days 7 --channels slack

# Verify Configuration
docker-compose exec app python main.py verify-config
```

---

### Local Python

For running directly on your machine or VPS.

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Initialize Database
python main.py init-db
python main.py mark-all-read --yes # Skip old news
```

#### Automate with Cron (Mac/Linux)

Add to your `crontab -e`:

```bash
# Hourly Check
0 * * * * cd /path/to/aws-brief && venv/bin/python main.py process-cycle

# Monday Morning Digest
0 9 * * 1 cd /path/to/aws-brief && venv/bin/python main.py send-digest --days 7
```

---

## 🛡️ Noise Cancellation (Filtering)

Don't want to hear about **GovCloud** or **Test Regions**?
Rename `filters.yaml.example` to `filters.yaml` and add your rules.

**Supported Actions:**

- `IGNORE`: Completely skips the item. No database entry, no notification.
- `DIGEST_ONLY`: Saves for Weekly Summary, but mutes real-time alerts.
- `NOTIFY`: (Default) Sends immediate alert.

**Example `filters.yaml`:**

```yaml
rules:
  - name: "Ignore GovCloud"
    match:
      title_regex: ".*GovCloud.*"
    action: IGNORE

  - name: "Digest Only Updates"
    match:
      title_regex: ".*EC2 Instance Type.*"
    action: DIGEST_ONLY
```

---

## ⚙️ Configuration (.env)

| Key | Description | Example |
| :--- | :--- | :--- |
| `DEFAULT_AI_ENGINE` | Which provider to use. | `ollama`, `openai`, `anthropic` |
| `DEFAULT_AI_MODEL` | Specific model ID. | `llama3`, `gpt-4o`, `claude-3-opus` |
| `SLACK_WEBHOOK_URL` | For Slack alerts. | `https://hooks.slack.com/...` |
| `SUMMARY_LANGUAGE` | Output language. | `English`, `Turkish`, `German` |
| `SCAN_INTERVAL` | Seconds between Docker checks. | `900` (15 mins) |

---

## 💻 CLI Reference

If you want to use the tool manually (or build your own scripts), here are the available commands:

| Command | Description | Example |
| :--- | :--- | :--- |
| `--help` | Show all available commands. | `python main.py --help` |
| `init-db` | Initializes the SQLite database. | `python main.py init-db` |
| `scan` | Checks RSS feeds for new items. | `python main.py scan --url "http://..."` |
| `list-news` | Shows latest headlines in terminal. | `python main.py list-news --limit 20` |
| `summarize` | AI summarizes a specific item by ID. | `python main.py summarize --item-id 123` |
| `send-digest` | Generates a report for past N days. | `python main.py send-digest --days 7 --channels slack` |
| `process-cycle` | Runs Scan -> Summarize -> Notify loop. | `python main.py process-cycle` |
| `mark-all-read`| Marks history as "notified". | `python main.py mark-all-read --yes` |
| `verify-config`| Self-diagnostic check for API/DB. | `python main.py verify-config` |

---

## 📸 See It In Action

### Rich Notifications
>
> **🚨 [HIGH] AWS Security: ALB Invalid Header Drop**
>
> **What:** AWS Application Load Balancer now supports "Drop Invalid Header Fields" to prevent HTTP Desync attacks.
> **Why:** Attackers can use malformed headers to bypass security controls or poison backend caches.
> **Impact:** HIGH (Potential for Request Smuggling)
> **Action:** Enable `routing.http.drop_invalid_header_fields.enabled` on all public ALBs.
>
> [Read Full Story]

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository.
2. **Clone** your fork locally.
3. **Install Dev Dependencies:**

    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

4. **Create a Branch** for your feature (`git checkout -b feature/amazing-feature`).
5. **Commit** your changes (`git commit -m 'Add amazing feature'`).
6. **Push** to the branch (`git push origin feature/amazing-feature`).
7. Open a **Pull Request**.

---

## ⚖️ License

Distributed under the **MIT License**. See `LICENSE` for more information.
