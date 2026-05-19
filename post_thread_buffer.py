"""
Sabapna.com - Twitter Story Thread Bot (via Buffer API)
Generates story threads using Claude API and posts via Buffer → X (Twitter)
Runs daily via GitHub Actions cron job. FREE to run.
"""

import os
import time
import json
import random
import requests
import anthropic

# ── Config ────────────────────────────────────────────────────────────────────
WEBSITE_URL = "https://sabapna.com"
BUFFER_CHANNEL_ID = "6a0c3e98090476fb99371f8e"
BUFFER_ORG_ID = "6a0c3e251cfeb0c86e94338c"
BUFFER_API_URL = "https://api.buffer.com"

# ── Topic Pool ────────────────────────────────────────────────────────────────
TOPICS = [
    "A fresher from Muzaffarpur, Bihar who sent 340 applications, got 0 replies, then changed 1 thing and got 3 interviews",
    "A commerce graduate from Patna who cracked a software company job without a CS degree",
    "A 2023 passout who was unemployed for 8 months in UP, then got 3 offers in 1 week",
    "A girl from a small town in Bihar who got a remote job and works from home",
    "A fresher who made one simple change to their resume and got instant callbacks",
    "A BCA graduate from Ranchi who got hired at a product startup over IIT graduates",
    "A fresher who failed 12 interviews but cracked the 13th at a top MNC",
    "Someone who used LinkedIn wrong for 6 months, then fixed it and got hired in 2 weeks",
    "A 2024 passout who got ghosted by 30 companies, then discovered why and fixed it",
    "A fresher who built one small project and got an off-campus offer",
    "Someone who switched from BPO to IT using one free certification",
    "A fresher who cracked a government job while everyone told them to try private sector",
    "A girl who got rejected for lack of communication skills and what she did next",
    "A fresher from Jharkhand who negotiated salary and got 1.5L more than initial offer",
    "A 2022 passout who was about to give up job search but got hired the next week",
]

SYSTEM_PROMPT = """You are a Twitter content writer for Sabapna.com, a job platform for Indian freshers and young job seekers.

Write viral story-style Twitter threads that feel real, human, and relatable to Indian freshers (2020-2024 graduates) struggling to find jobs.

Rules:
- Write in simple, conversational English. Not corporate. Not fancy.
- Each tweet must be under 270 characters.
- Make it feel like a real story with struggle, turning point, and lesson.
- Use specific details: months, rejection count, salary, city, college tier, family context.
- Use emojis sparingly — max 1-2 per tweet.
- NO hashtags except in the last CTA tweet (max 2-3 there).
- Hook (tweet 1) must make someone stop scrolling.
- Tweets 2-8: story unfolds, one idea per tweet.
- Tweet 9: soft CTA with website link.

Return ONLY a JSON array of 9 tweet strings, nothing else:
["tweet 1", "tweet 2", ..., "tweet 9"]"""


def generate_thread(topic: str) -> list:
    """Generate story thread using Claude API."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Write a 9-tweet story thread about:
"{topic}"

Tweet 1: Powerful hook. Specific. No link.
Tweets 2-8: Story unfolds. Real details. One idea per tweet.
Tweet 9: End with: "Fresh jobs posted daily at {WEBSITE_URL} 👇 #FresherJobs #Naukri"

Return ONLY the JSON array of 9 strings."""
        }]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    tweets = json.loads(raw)
    assert len(tweets) >= 3, "Too few tweets"

    for i, tweet in enumerate(tweets):
        if len(tweet) > 280:
            tweets[i] = tweet[:277] + "..."

    return tweets


def post_thread_to_buffer(tweets: list) -> None:
    """Post all 9 tweets as a single Twitter thread via Buffer API."""
    from datetime import datetime, timezone, timedelta

    api_key = os.environ["BUFFER_API_KEY"]

    # Tweet 1 is the main text (shown as the post preview)
    # ALL tweets including tweet 1 go into thread array so nothing is skipped
    main_text = tweets[0]
    threaded_posts = [{"text": t} for t in tweets]  # all 9 tweets in thread

    # Schedule 30 seconds from now
    due_at = (datetime.now(timezone.utc) + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    mutation = """
    mutation CreateThread($text: String!, $channelId: ChannelId!, $dueAt: DateTime!, $thread: [ThreadedPostInput!]!) {
      createPost(input: {
        text: $text
        channelId: $channelId
        schedulingType: automatic
        mode: customScheduled
        dueAt: $dueAt
        metadata: {
          twitter: {
            thread: $thread
          }
        }
      }) {
        ... on PostActionSuccess {
          post {
            id
            text
            dueAt
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """

    variables = {
        "text": main_text,
        "channelId": BUFFER_CHANNEL_ID,
        "dueAt": due_at,
        "thread": threaded_posts,
    }

    print(f"Posting thread of {len(tweets)} tweets to Buffer...")
    print(f"Scheduled for: {due_at}")

    response = requests.post(
        BUFFER_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={"query": mutation, "variables": variables}
    )

    data = response.json()
    print(f"Raw response: {json.dumps(data)}")

    if "errors" in data:
        raise Exception(f"Buffer API error: {data['errors']}")

    result = data.get("data", {}).get("createPost", {})
    if "message" in result:
        raise Exception(f"Buffer post failed: {result['message']}")

    post_id = result.get("post", {}).get("id") or "unknown"
    due = result.get("post", {}).get("dueAt", "")
    print(f"\nThread scheduled! Buffer post ID: {post_id}")
    print(f"Will post as a thread at: {due}")


def main():
    print("Sabapna Twitter Bot starting...")

    topic = random.choice(TOPICS)
    print(f"Topic: {topic}\n")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("No ANTHROPIC_API_KEY — using hardcoded test thread")
        tweets = [
            "A girl passed her 12th from a government school in Varanasi.\n\nNo degree. No connections. No English.\n\nEveryone said: ab shaadi kar lo. Kya hoga padh ke?\n\nShe proved every single one of them wrong. 🧵",
 
            "I share real stories like this every week.\n\nIf you're searching for work right now — sabapna.com has fresh jobs updated daily. For freshers, 12th pass, graduates — everyone.\n\nAb Sunita ki baat karte hain. 👇",
 
            "Sunita Yadav. 2022. 12th pass. Commerce stream. Government inter college, Varanasi.\n\nHer father drives an e-rickshaw. Earns ₹400-500 on a good day.\n\nShe has two younger sisters. Both still in school.\n\nAfter 12th, her relatives said one thing unanimously: ladki hai. Ghar sambhalo. Degree ki kya zaroorat?\n\nHer mother quietly disagreed. Never said it loudly. But disagreed.",
 
            "Sunita wanted to work. Earn. Contribute.\n\nBut nobody would hire a 12th pass girl with no experience and broken English.\n\nShe went to 6 shops in her area asking for billing or counter work.\n\nAll 6 said no.\n\nOne shopkeeper said: 'Degree lao pehle.'\n\nShe didn't have money for degree. That was the whole problem.",
 
            "Month 5 of searching.\n\nHer cousin's wedding came. Everyone dressed up. Photos everywhere.\n\nA relative pulled her mother aside: 'Sunita ka kya plan hai? Rishte dekhne chahiye ab.'\n\nHer mother smiled and said nothing.\n\nThat night Sunita heard her parents talking in the kitchen. Her father said: 'Padhai mein itna invest kar diya. Kuch kaam ka nikla nahi.'\n\nShe put a pillow on her face and screamed into it.",
 
            "Her school friend Meenu called her one evening.\n\nMeenu had joined a data entry job. ₹8,000/month. Work from home. Company hired 12th pass.\n\nSunita said: 'Mujhe bhi batao kaise kiya?'\n\nMeenu sent her the company's form. And one more thing — a free typing speed course link on YouTube.\n\nSunita had never thought of typing as a skill. She could type fast. She'd just never called it a skill.",
 
            "She practiced typing for 3 weeks. 45 minutes every morning before anyone woke up.\n\nWent from 20 words per minute to 55.\n\nMade a simple one-page resume on her phone using a free template.\n\nWrote: 'Typing speed: 55 WPM. MS Excel basic. Hindi and English data entry.'\n\nApplied to 11 companies that said '12th pass welcome.'\n\nWrote each application by hand in a notebook first, then typed it. She wanted every word to be right.",
 
            "Company number 7 replied.\n\nA small fintech startup in Noida needed a data entry operator for their KYC team. Remote work allowed.\n\nOne typing test online. One 10-minute phone call.\n\nThe HR asked: 'Aapko WFH mein comfortable rehna hai?'\n\nSunita said: 'Haan bilkul.'\n\nOffer: ₹9,500/month. Work from home. Start in 2 weeks.\n\nShe read the email 4 times to make sure it was real.",
 
            f"Fresh jobs at {WEBSITE_URL} 👇\n12th pass, graduate, fresher — sab ke liye.\n\n—\n\nShe didn't tell anyone for one full day.\n\nJust kept the email open on her phone. Read it every hour.\n\nThe next morning she told her mother.\n\nHer mother held her face in both hands and said nothing for a long time.\n\nThen: 'Tere baap ko batate hain. Aaj achha khana banega.'\n\nHer father came home at 8pm. Tired as always. She showed him the email.\n\nHe read it slowly. Looked up. Said: 'Shukriya beta.'\n\nHer younger sisters don't know yet what she proved that day. But they will.\n\n#12thPassJobs #FresherJobs #WomenWhoWork",
        ]
    else:
        print("Generating thread with Claude...")
        tweets = generate_thread(topic)
        print(f"Generated {len(tweets)} tweets\n")

    print("--- THREAD PREVIEW ---")
    for i, tweet in enumerate(tweets):
        print(f"[{i+1}] ({len(tweet)} chars)\n{tweet}\n")
    print("----------------------\n")

    post_thread_to_buffer(tweets)


if __name__ == "__main__":
    main()
