from connectors.black_book import get_spending_summary
from core.memory import save_pattern
from core.audit import log
import anthropic
from config import ANTHROPIC_API_KEY, PRIMARY_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def analyze_spending_patterns():
    summary = get_spending_summary("month")
    if not summary["success"]:
        return
    prompt = f"""
    Analyze this spending data and identify 2-3 clear behavioral patterns.
    Be specific. Each pattern should be actionable.
    Data: {summary['data']}
    Format each as:
    PATTERN: [description]
    CONFIDENCE: [0.0-1.0]
    DATA_POINTS: [number]
    """
    response = client.messages.create(
        model=PRIMARY_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    for line in response.content[0].text.split("\n"):
        if line.startswith("PATTERN:"):
            description = line.replace("PATTERN:", "").strip()
            save_pattern("spending", description, 0.7, 30)
            log(f"Detected spending pattern: {description[:80]}", system="PATTERNS")

def run_pattern_detection():
    log("Starting pattern detection cycle", system="PATTERNS")
    analyze_spending_patterns()
    log("Pattern detection complete", system="PATTERNS")

if __name__ == "__main__":
    run_pattern_detection()
