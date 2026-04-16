import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# System connections
BLACK_BOOK_DB_URL = os.getenv("BLACK_BOOK_DB_URL")
MERIDIAN_VAULT_PATH = os.getenv("MERIDIAN_VAULT_PATH")
OLYMPUS_STATUS_PATH = os.getenv("OLYMPUS_STATUS_PATH")
APOLLO_MIND_VAULT_PATH = os.getenv("APOLLO_MIND_VAULT_PATH", r"C:\Users\Ignac\Dropbox\Apollo\mind_vault")

# Apollo internals
APOLLO_DB_PATH = r"C:\Users\Ignac\Dropbox\Apollo\data\apollo.db"
CHROMA_PATH = r"C:\Users\Ignac\Dropbox\Apollo\data\chroma"
AUDIT_LOG_PATH = r"C:\Users\Ignac\Dropbox\Apollo\logs\apollo_audit.log"
QUEUE_PATH = r"C:\Users\Ignac\Dropbox\Apollo\data\queue"

# Channels
WHATSAPP_BRIDGE_PORT = int(os.getenv("WHATSAPP_BRIDGE_PORT", "3001"))
BRIEF_DELIVERY_TIME = os.getenv("BRIEF_DELIVERY_TIME", "07:00")

# LLM settings
PRIMARY_MODEL = "claude-opus-4-6"
FAST_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

# Pantheon runtime
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
PANTHEON_MODEL = os.getenv("PANTHEON_MODEL", "llama3.2")
