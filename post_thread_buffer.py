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
BUFFER_API_URL = "https://api.buffer.com/graphql"

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


def post_to_buffer(tweet_text: str) -> str:
    """Post a single tweet to Buffer queue."""
    api_key = os.environ["BUFFER_API_KEY"]

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            status
          }
        }
        ... on PostActionError {
          message
        }
      }
    }
    """

    variables = {
        "input": {
            "channelId": BUFFER_CHANNEL_ID,
            "text": tweet_text,
            "schedulingType": "queue",
            "mode": "CLEAN"
        }
    }

    response = requests.post(
        BUFFER_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={"query": mutation, "variables": variables}
    )

    data = response.json()
    print(f"  Raw response: {json.dumps(data)}")

    if "errors" in data:
        raise Exception(f"Buffer API error: {data['errors']}")

    post_id = data.get("data", {}).get("createPost", {}).get("post", {}).get("id") or "queued"
    return post_id


def post_thread_to_buffer(tweets: list) -> None:
    """Post all tweets to Buffer queue."""
    print(f"Queuing {len(tweets)} tweets to Buffer...")

    for i, tweet_text in enumerate(tweets):
        print(f"  Queuing tweet {i+1}/{len(tweets)}: {tweet_text[:60]}...")
        post_id = post_to_buffer(tweet_text)
        print(f"  Queued — Buffer post ID: {post_id}")
        time.sleep(2)

    print(f"\nAll {len(tweets)} tweets queued in Buffer!")
    print(f"Buffer will post them to @kaelai_x automatically.")


def main():
    print("Sabapna Twitter Bot starting...")

    topic = random.choice(TOPICS)
    print(f"Topic: {topic}\n")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("No ANTHROPIC_API_KEY — using hardcoded test thread")
        tweets = [
            "This boy from Muzaffarpur, Bihar sent 340 job applications. Got 2 replies. Both rejections. Then his cousin showed him one thing. 3 weeks later he had an offer letter.",
            "Meet Rajan Kumar. 2023 BCA passout. Patna University. First in his family to get a degree. His father sells vegetables at the local mandi.",
            "For 8 months after graduation, Rajan woke up at 6am, opened Naukri.com, and applied to every IT job he could find. Data entry. Support roles. Anything.",
            "His mother stopped telling relatives he was looking for a job. The questions were too painful. Beta kab lagega? He stopped going to weddings.",
            "His resume looked like this: 12 pages long. Every school certificate listed. Participated in college fest 2019. Hobbies: Cricket and Listening Music.",
            "His cousin Vikash, working in Pune, visited during Chhath. Opened Rajan's resume. Went silent for 10 seconds. Then said: Yaar, ye delete kar. Sab kuch.",
            "They rebuilt it in one evening. 1 page. Clean. 3 projects on top. A GitHub link. Skills listed properly. No Objective line. No hobbies. No 12th marksheet.",
            "Rajan uploaded the new resume on a Monday night. By Thursday he had 2 calls. By the following week — an interview in Noida. 3.8 LPA. He took it without blinking.",
            f"He called his father from Patna station before boarding the train to Noida. His father cried. So did he. First salary 5000 sent home on day 1.\n\nFresh jobs daily at {WEBSITE_URL}\n#FresherJobs #Naukri",
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
