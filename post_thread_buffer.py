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
            "Manager: Can you come in this Saturday?\n\nEmployee: Sure.\n\nManager: And Sunday as well. Client deadline.\n\nEmployee: Okay.\n\nThree months later.\n\nEmployee: I need Friday off. My sister's wedding.\n\nManager: That's short notice.\n\nEmployee: I requested it 3 weeks ago.\n\nManager: We have a lot going on right now.\n\nEmployee: I have worked 11 of the last 12 weekends.\n\nManager: We all make sacrifices here.\n\nEmployee: I am not asking for a day off.\n\nManager: Sorry?\n\nEmployee: I am taking the day I already earned.\n\nManager: That is not how leave works here.\n\nEmployee: I have 18 unused leave days.\n\nManager: Those require approval.\n\nEmployee: I am requesting approval.\n\nManager: Denied.\n\nEmployee: Noted.\n\nTwo weeks later the employee resigned.\n\nExit interview.\n\nHR: Why are you leaving?\n\nEmployee: I needed one day.\n\nHR: I am sure we could have worked something out.\n\nEmployee: You had 3 weeks to work it out.\n\nHR: (Silence)\n\nThe job was posted the next day.\n\nThey hired two people to replace one.",
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
