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
            "A girl from a village in Madhya Pradesh had no smartphone.\n\nNo laptop. No WiFi. No coaching.\n\nEveryone said: Nothing will happen from here.\n\nShe got a job before her engineering friends did. 🧵",
 
            f"I share stories like this every week.\n\nIf you are still searching — sabapna.com posts fresh jobs daily. For freshers, 12th pass, graduates — everyone is welcome.\n\nThis is Rekha's story. 👇",
 
            "Rekha Patel. 22 years old. Sehore, Madhya Pradesh.\n\nPopulation of her village: ~800 people.\nNearest city: 40km away.\nHer father: daily wage labourer. ₹300-350/day.\nHer phone: a basic keypad Nokia. No internet.\n\nShe passed 12th with 74%. Commerce stream.\nDistrict school. Hindi medium.",
 
            "After 12th, her options were:\n\n• Get married (relatives' suggestion)\n• Work at a local kirana store (₹2,500/month)\n• Go to Bhopal, find something somehow\n\nHer father said: You will have to go to Bhopal. Nothing will come of staying here.\n\nHe had ₹8,000 saved.\nGave her ₹6,000.\nKept ₹2,000 for the house.\n\nShe took a bus to Bhopal alone for the first time in her life.",
 
            "Bhopal was overwhelming.\n\nShe did not know how to use a smartphone properly.\nCould not operate a laptop.\nHer Hindi-medium background made her freeze in interviews.\n\nFirst week:\n• 3 walk-in interviews\n• 3 rejections\n• Reason given: No computer knowledge\n\nShe called her father that night.\n\nHe said: Stay. One more week.\n\nShe stayed.",
 
            "A woman at her PG — Savitri — worked at a computer training institute.\n\nShe saw Rekha sitting alone one evening. Asked what happened.\n\nRekha told her everything.\n\nSavitri said: Come with me tomorrow. I will teach you for free.\n\nFor 3 weeks, Rekha went every morning.\n\nMS Excel. MS Word. Basic typing. Email writing.\n\nShe practiced on the institute computers. 2 hours every day. For free.",
 
            "After 3 weeks she could:\n\n• Type 40 WPM\n• Make basic Excel sheets\n• Write a proper email in English\n• Operate a computer without freezing\n\nShe made a 1-page resume. Savitri helped her write it.\n\nApplied to 14 companies in Bhopal.\nWalk-ins. Job fairs. WhatsApp groups.\n\nHer engineering friends back home were still waiting for campus placements.",
 
            "Company number 9 called back.\n\nA small logistics firm. Data entry and billing work.\n\nInterview: 20 minutes.\nTyping test: cleared.\nBasic English: fine.\n\nOffer:\n• ₹10,500/month\n• In-office. Bhopal.\n• Start Monday.\n\nShe read the offer letter 3 times.\n\nThen went to a STD booth and called her father.\n\nHis first question: Are you okay? Are you eating properly?",
 
            f"Fresh jobs at {WEBSITE_URL} 👇\n12th pass, fresher, graduate — everyone is welcome.\n\n—\n\nShe sent ₹3,000 home on her first salary day.\n\nHer father called back.\n\nHe said: Do not send so much. Keep it for yourself.\n\nShe said: You gave me ₹6,000. I am returning half.\n\nLong silence.\n\nThen: Come home once. Your mother has been asking about you.\n\nHer engineering friends got placed 4 months later.\nRekha had already completed her probation.\n\nNo smartphone. No laptop. No WiFi.\n\nJust one woman who said: Come with me tomorrow.\n\n#FresherJobs #WomenWhoWork #RuralIndia",
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
