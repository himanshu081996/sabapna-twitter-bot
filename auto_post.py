"""
Sabapna.com - Fully Autonomous Twitter Bot
Uses Groq API (free) to generate topics + viral stories
Learns from Simon's viral posts via CSV
Posts via Buffer to X every hour from 9am to 8pm IST
"""

import os
import requests
import csv
import random
from datetime import datetime, timezone, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
WEBSITE_URL = "https://sabapna.com"
BUFFER_CHANNEL_ID = "6a0c3e98090476fb99371f8e"
BUFFER_API_URL = "https://api.buffer.com"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
CSV_FILE = "simon.csv"

# ── 50 Topic Seeds ────────────────────────────────────────────────────────────
TOPIC_SEEDS = [
    "salary gap discovered between two colleagues doing identical work",
    "promotion given to less experienced person who joined 6 months ago",
    "manager takes full credit for employee's project in board meeting",
    "employee works 14 weekends straight, asks for one day off, denied",
    "company announces no bonus, CEO buys new car same week",
    "employee who trained entire team gets paid less than everyone they trained",
    "5 year employee laid off over video call with no prior warning",
    "outstanding performer gets average rating because manager dislikes them",
    "company says family first, fires employee who took leave for surgery",
    "new joiner negotiates 40% more than 3-year veteran for same role",
    "candidate clears 6 rounds, offer comes 50% below job posting",
    "employee catches error saving company 1 crore, gets thank you email",
    "WFH denied for employee, manager works from home same day",
    "employee resigns, suddenly gets everything denied for 2 years",
    "HR shares employee salary complaint with the very manager complained about",
    "company freezes hikes citing losses, hires 5 senior managers at double pay",
    "employee asked to train replacement before their own layoff",
    "performance improvement plan given to employee who just had best quarter",
    "long-serving employee skipped for promotion, external hire gets role and team",
    "employee discovers colleague with same title earns 15 LPA more",
    "company celebrates work-life balance award, team averaging 70 hour weeks",
    "employee takes mental health day, manager schedules meeting during it",
    "candidate rejected for overqualification, role unfilled for 8 months after",
    "employee asks for raise, denied. Gets competing offer. Company suddenly has budget.",
    "manager micromanages every email but takes credit for all results",
    "employee given impossible deadline, works through weekend, deadline shifted anyway",
    "CEO says people are our biggest asset. Layoffs announced next day.",
    "employee with 8 years experience rejected internally, role given to fresher at lower cost",
    "star employee poached by competitor at double salary. Previous company had refused 20% raise.",
    "employee flagged a compliance issue. Got fired for raising it.",
    "team lead position promised verbally for 2 years. Given to someone who joined 3 months ago.",
    "employee asked to mentor junior. Junior promoted above them. Mentor still waiting.",
    "company policy: no salary discussion. Two employees talk. 30% gap revealed.",
    "employee on medical leave gets performance warning for low productivity",
    "joining bonus clawed back when employee quits after 11 months. Bond was 12 months.",
    "remote work approved. Manager counts it against employee in annual review.",
    "employee relocates city for job. Role eliminated 3 months after joining.",
    "company values say speak up. Employee speaks up. Gets managed out.",
    "full time employee replaced by contractor doing same work at lower cost. No benefits.",
    "employee asked to do two roles after colleague laid off. Salary stays same.",
    "exit interview feedback shared with the manager being complained about",
    "company sends wellness email during mass layoff week",
    "employee works notice period fully. Reference withheld over minor dispute.",
    "team hits record numbers. Bonuses cancelled due to global headwinds.",
    "employee promoted with no salary increase. Just a new title.",
    "company fires employee for social media post praising a competitor product",
    "manager gives glowing verbal feedback. Submits poor written review.",
    "employee takes paternity leave. Comes back to find role restructured away.",
    "candidate given verbal offer. Quits current job. Offer rescinded a week later.",
    "employee rated top performer 3 years running. Denied promotion for lacking executive presence.",
]


def load_viral_examples(csv_path: str, top_n: int = 5) -> str:
    """Load top viral posts from CSV as style reference."""
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        posts = list(reader)

    posts_sorted = sorted(posts, key=lambda x: int(x.get('View Count', 0) or 0), reverse=True)

    seen = set()
    top_posts = []
    skip_words = ['cv', 'resume', 'ats', 'linkedin tip', 'interview tip', 'hire me']

    for p in posts_sorted:
        if p['Text'] in seen:
            continue
        seen.add(p['Text'])
        if any(word in p['Text'].lower() for word in skip_words):
            continue
        top_posts.append(p)
        if len(top_posts) >= top_n:
            break

    context = ""
    for i, p in enumerate(top_posts):
        context += f"EXAMPLE {i+1} — {int(p['View Count']):,} views:\n\n{p['Text']}\n\n{'='*40}\n\n"

    return context


def call_groq(system: str, user: str, max_tokens: int = 1500) -> str:
    """Call Groq API."""
    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.9
        }
    )

    data = response.json()
    if "error" in data:
        raise Exception(f"Groq error: {data['error']}")

    return data["choices"][0]["message"]["content"].strip()


def generate_topic(viral_context: str) -> str:
    """Generate fresh topic using random seeds."""
    seeds = random.sample(TOPIC_SEEDS, 3)
    seeds_text = "\n".join("- " + s for s in seeds)

    system = f"""You are a viral Twitter content strategist for Indian workplace audience.

These real posts went viral on Twitter — study the style:

{viral_context}

Now generate ONE original workplace injustice topic for a Twitter story.

Use ONE of these situation seeds as inspiration — but write a completely fresh, specific, human topic sentence around it:

{seeds_text}

Rules:
- Pick the seed that feels most emotionally powerful
- Write ONE specific topic sentence inspired by it — not a copy of it
- Make it feel like it happened to a specific real person in India
- Include one specific detail (years, salary, role, timing) to make it real
- One sentence only — punchy and clear

Return ONLY the topic sentence. Nothing else."""

    return call_groq(system=system, user="Generate the topic now.", max_tokens=120)


def generate_story(topic: str, viral_context: str) -> str:
    """Generate viral story using Groq."""
    system = f"""You are a viral Twitter content writer for Indian workplace audience.

Study these real posts that went viral — learn the exact style, tone, and flow:

{viral_context}

KEY THINGS TO COPY FROM THESE EXAMPLES:

1. NATURAL CONVERSATION — not formal exchanges
   Write like real humans talk. Interrupted. Emotional. Surprised.
   "Wait… today?" — that is shock. Real shock.
   "Interesting." — one word that says everything.

2. CONTRACTIONS ARE ALLOWED — write like humans speak
   Use "I'm", "we'll", "don't", "you've" — makes it feel real

3. VILLAIN SOUNDS CORPORATE BUT HOLLOW
   "This is simply company policy."
   "We appreciate the professionalism."
   These sound reasonable but are devastating in context.

4. HERO RESPONDS WITH HUMAN REACTIONS — not arguments
   "Wait… today?" — shock
   "Interesting." — quiet anger
   "That explains why he avoided me all day." — piecing things together

5. SPECIFIC DETAILS MAKE IT REAL
   "I was counting on that final week of pay."
   "IT will deactivate your access in 10 minutes."

6. ENDING IS A QUIET TRUTH — not a lesson
   "The company was never my safety net. I was supposed to build my own all along."

NOW write a completely NEW original story.

RULES:
- Indian workplace context — salaries in LPA
- 15 to 22 exchanges — tight and punchy
- One personal financial or family detail to make hero human
- Villain: HR / Manager / CEO — always calm, always corporate
- Hero: Employee / Candidate — real human reactions
- Ending: 2 to 3 short narrator lines — ironic, devastating, quotable
- No hashtags, no emojis, no links, no title
- Return ONLY the story"""

    return call_groq(
        system=system,
        user=f"Write the story about this topic:\n\n{topic}",
        max_tokens=1200
    )


def post_to_buffer(tweet_text: str) -> str:
    """Post tweet to Buffer."""
    due_at = (datetime.now(timezone.utc) + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    mutation = """
    mutation CreatePost($text: String!, $channelId: ChannelId!, $dueAt: DateTime!) {
      createPost(input: {
        text: $text
        channelId: $channelId
        schedulingType: automatic
        mode: customScheduled
        dueAt: $dueAt
      }) {
        ... on PostActionSuccess {
          post {
            id
            text
          }
        }
      }
    }
    """

    variables = {
        "text": tweet_text,
        "channelId": BUFFER_CHANNEL_ID,
        "dueAt": due_at,
    }

    response = requests.post(
        BUFFER_API_URL,
        headers={
            "Authorization": f"Bearer {os.environ['BUFFER_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={"query": mutation, "variables": variables}
    )

    data = response.json()
    if "errors" in data:
        raise Exception(f"Buffer API error: {data['errors']}")

    return data.get("data", {}).get("createPost", {}).get("post", {}).get("id") or "posted"


def main():
    print("Sabapna Auto Twitter Bot starting...")

    # Load viral examples
    print("Loading viral examples from CSV...")
    viral_context = load_viral_examples(CSV_FILE)
    print("Loaded!\n")

    # Generate topic
    print("Step 1: Generating topic...")
    topic = generate_topic(viral_context)
    print(f"Topic: {topic}\n")

    # Generate story
    print("Step 2: Generating story...")
    story = generate_story(topic, viral_context)
    print(f"\n--- STORY ---\n{story}\n-------------")
    print(f"Chars: {len(story)} | Words: {len(story.split())}\n")

    # Post to Buffer
    print("Step 3: Posting to Buffer...")
    post_id = post_to_buffer(story)
    print(f"Done! Buffer ID: {post_id}")


if __name__ == "__main__":
    main()
