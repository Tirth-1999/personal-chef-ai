# Sous — Personal Chef AI

A LangChain agent that suggests recipes from your leftovers, searches the web with Tavily, understands fridge photos, and remembers your conversation.

Built as a portfolio project from the [LangChain Academy](https://academy.langchain.com/) Introduction to LangChain course.

## Features

- Chat with a personal chef agent (`create_agent`)
- Web recipe search via Tavily (toggle in sidebar)
- Fridge photo upload (Gemini or Groq vision)
- Conversation memory across follow-up messages
- **How it works** page explaining the architecture

## Run locally

```bash
git clone https://github.com/YOUR_USERNAME/personal-chef-ai.git
cd personal-chef-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp example.env .env   # then edit .env with your keys
streamlit run app.py
```

Open http://localhost:8501

## API keys (local)

Copy `example.env` to `.env` and fill in:

| Key | Required? | Get it from |
|-----|-----------|-------------|
| `GOOGLE_API_KEY` | One of Google or Groq | [Google AI Studio](https://aistudio.google.com/apikey) |
| `GROQ_API_KEY` | One of Google or Groq | [Groq Console](https://console.groq.com) |
| `TAVILY_API_KEY` | If web search is on | [Tavily](https://tavily.com) |

You need **at least one** LLM key (Google or Groq). Tavily is only needed when “Search the web for recipes” is enabled.

## Deploy on Streamlit Cloud (public link)

1. Push this repo to **your** GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select this repository, branch `main`, main file path: **`app.py`**.
4. Open **Settings → Secrets** and paste:

```toml
GOOGLE_API_KEY = "your-google-key"
GROQ_API_KEY = "your-groq-key"
TAVILY_API_KEY = "your-tavily-key"
```

5. Click **Deploy**. Share the `*.streamlit.app` URL.

### How visitors use your hosted app

**You (the app owner) add the API keys once** in Streamlit Cloud secrets. Visitors open the public URL and use the app **without entering any keys**.

- Keys are stored securely on Streamlit’s servers — not in the GitHub repo.
- **Every visitor’s chat uses your API keys**, so usage counts against your Google/Groq/Tavily accounts.
- For a portfolio demo this is normal; monitor usage on each provider’s dashboard.
- To reduce cost: use free-tier Gemini/Groq and turn off Tavily search in the sidebar by default.

**Never commit `.env` or real keys to GitHub.**

## Project structure

```
personal-chef-ai/
├── app.py              # Main Streamlit app (entry point)
├── how_it_works.py     # Architecture page
├── requirements.txt    # Python dependencies
├── example.env         # Key template (safe to commit)
├── .streamlit/
│   └── config.toml
└── README.md
```

## Tech stack

Streamlit · LangChain · LangGraph · Gemini / Groq · Tavily

## License

MIT (or adjust as you prefer)
