# LiteLLM Proxy Stack: Gemini AI Studio (Free Tier) → Vertex AI (Credits) Fallback

A production-ready Docker Compose & Dockge stack running **LiteLLM Proxy** backed by **PostgreSQL**. This setup automatically maximizes free tier usage from **Google AI Studio** and seamlessly fails over to **Google Cloud Vertex AI** (using GCP credits) whenever rate limits (HTTP 429) or high demand spikes (HTTP 503) occur.

---

## 🚀 Key Features

* **Instant Native Failover:** Zero-downtime routing from Google AI Studio (Free Tier) to Vertex AI (GCP Credits).
* **Preconfigured Reasoning Variants:** Dedicated model aliases for `-high`, `-medium`, and `-low` reasoning effort across the entire Gemini 3.7, 3.6, 2.5, and Pro model families.
* **Unrestricted Content Filtering (`BLOCK_NONE`):** Safety thresholds set to `BLOCK_NONE` across all 5 Google harm categories.
* **Accurate Spend Tracking:** AI Studio free tier models recorded at `$0.00/token`, while Vertex AI fallback models track actual GCP token rates in the PostgreSQL-backed Admin UI.
* **Auto Router Endpoints:** Unified aliases (`gemini-auto`, `auto`, `reasoning-high`, etc.) with `usage-based-routing` load balancing.
* **Dockge Compatible:** Native `compose.yaml` and `.env` structure designed for Docker Compose and Dockge self-hosted stack management.
* **Secret Isolation:** All API keys and GCP service account credentials remain in environment variables or git-ignored secrets folders.

---

## 📐 Architecture & Routing Strategy

```
                          ┌──────────────────────────┐
                          │    Client Application    │
                          │   (OpenAI SDK / Agent)   │
                          └─────────────┬────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────┐
                          │   LiteLLM Proxy (Port)   │
                          │      http://:4000/v1     │
                          └─────────────┬────────────┘
                                        │
                         Attempt 1 (Primary - Free Tier)
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │    Google AI Studio API     │
                         │   (gemini/gemini-3.7-flash) │
                         └──────────────┬──────────────┘
                                        │
                              HTTP 429 / 503 Error
                                        │
                            Instant 60s Cooldown
                                        │
                         Attempt 2 (Fallback - Credits)
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │    GCP Vertex AI Engine     │
                         │ (vertex_ai/gemini-2.5-flash)│
                         └─────────────────────────────┘
```

---

## 🎛️ Model Matrix & Aliases

### 1. Gemini Flash Suite (Fast, Large 1M+ Context)

| Requested Alias | Reasoning Level | Primary (AI Studio) | Fallback (Vertex AI) |
| :--- | :--- | :--- | :--- |
| `gemini-3.7-flash-high` | High | `gemini/gemini-3.7-flash` | `vertex_ai/gemini-2.5-flash` |
| `gemini-3.7-flash-medium` | Medium | `gemini/gemini-3.7-flash` | `vertex_ai/gemini-2.5-flash` |
| `gemini-3.7-flash-low` | Low | `gemini/gemini-3.7-flash` | `vertex_ai/gemini-2.5-flash` |
| `gemini-3.7-flash` | Medium (Default) | `gemini/gemini-3.7-flash` | `vertex_ai/gemini-2.5-flash` |
| `gemini-3.6-flash-high` | High | `gemini/gemini-3.6-flash` | `vertex_ai/gemini-3.6-flash` |
| `gemini-3.6-flash-medium` | Medium | `gemini/gemini-3.6-flash` | `vertex_ai/gemini-3.6-flash` |
| `gemini-3.6-flash-low` | Low | `gemini/gemini-3.6-flash` | `vertex_ai/gemini-3.6-flash` |
| `gemini-2.5-flash-high` | High | `gemini/gemini-2.5-flash` | `vertex_ai/gemini-2.5-flash` |
| `gemini-2.5-flash` / `gemini-flash` | Medium (Default) | `gemini/gemini-2.5-flash` | `vertex_ai/gemini-2.5-flash` |
| `gemini-flash-lite` | Medium (Default) | `gemini/gemini-2.5-flash-lite` | `vertex_ai/gemini-2.5-flash-lite` |

### 2. Gemini Pro Suite (Deep Reasoning & Architecture)

| Requested Alias | Reasoning Level | Primary (AI Studio) | Fallback (Vertex AI) |
| :--- | :--- | :--- | :--- |
| `gemini-3.1-pro-high` / `gemini-pro-high` | High | `gemini/gemini-3.1-pro-preview` | `vertex_ai/gemini-2.5-pro` |
| `gemini-3.1-pro` / `gemini-pro` | Medium | `gemini/gemini-3.1-pro-preview` | `vertex_ai/gemini-2.5-pro` |
| `gemini-2.5-pro` | Medium | `gemini/gemini-2.5-pro` | `vertex_ai/gemini-2.5-pro` |

### 3. Global Shortcuts & Auto Router

| Requested Alias | Target Behavior |
| :--- | :--- |
| `gemini-auto` / `auto` | Auto-routes to optimal Flash model with usage-based balancing & Vertex fallback |
| `reasoning-high` | Routes to Pro reasoning tier with Vertex fallback |
| `reasoning-medium` | Routes to Flash balanced tier with Vertex fallback |
| `reasoning-low` | Routes to Flash Lite tier with Vertex fallback |

---

## 🛠️ Quickstart Installation

### 1. Clone Repository & Setup Files

```bash
git clone https://github.com/Paulusbremmer/litellm-stack.git /opt/stacks/litellm
cd /opt/stacks/litellm
cp .env.example .env
```

### 2. Configure Environment Variables (`.env`)

Edit `.env` (or use the Dockge UI editor):

```env
# Master Proxy Secret Key
LITELLM_MASTER_KEY=sk-litellm-your-secure-master-key

# Database Settings (For Admin UI & Spend Tracking)
POSTGRES_USER=litellm
POSTGRES_PASSWORD=your_secure_db_password
POSTGRES_DB=litellm

# Primary: Google AI Studio API Key (Free Tier)
GEMINI_API_KEY=AIzaSy...

# Fallback: Google Cloud Vertex AI Settings
VERTEX_PROJECT=your-gcp-project-id
VERTEX_LOCATION=us-central1

# Service Account Key (If using keyfile authentication for Vertex AI)
GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/gcp-key.json
```

### 3. (Optional) Service Account JSON Key

If using keyfile authentication for Vertex AI, save your GCP Service Account JSON key as:
```path
/opt/stacks/litellm/secrets/gcp-key.json
```
Ensure your service account has the **Vertex AI User** (`roles/aiplatform.user`) role granted in GCP IAM.

### 4. Deploy Stack

#### Dockge:
Open your Dockge Web UI, click **Scan Stacks** or navigate to the `litellm` stack, and click **Start**.

#### Docker Compose CLI:
```bash
docker compose up -d
```

---

## 💻 Client Integration Examples

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-litellm-your-secure-master-key"
)

# 1. Standard Flash Request (Free Tier -> Vertex Fallback)
response = client.chat.completions.create(
    model="gemini-3.7-flash",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# 2. High Reasoning Request
response = client.chat.completions.create(
    model="gemini-3.7-flash-high",
    messages=[{"role": "user", "content": "Solve this multi-step logic problem..."}]
)
print(response.choices[0].message.content)
```

### cURL

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-your-secure-master-key" \
  -d '{
    "model": "gemini-3.7-flash-high",
    "messages": [
      {"role": "user", "content": "Explain step by step..."}
    ]
  }'
```

---

## 📊 Admin UI & Spend Tracking

* **Admin UI URL:** `http://<your-server-ip>:4000/ui`
* **Login:** Authenticate using your `LITELLM_MASTER_KEY`.
* **Database:** Backed by PostgreSQL container `litellm-db`.
* **Spend Analytics:** Automatically records `$0.00` for AI Studio Free Tier calls, and logs exact token usage costs for Vertex AI fallbacks.

---

## 🔒 Security & Privacy

* `.env` and `/secrets/*.json` are explicitly ignored in `.gitignore`.
* All API keys in `config.yaml` are loaded dynamically via `os.environ/*`.
* All container volume mounts for config and secret keys use read-only (`:ro`) access modes.
