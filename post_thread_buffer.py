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
            "My father gave 31 years to a job.\n\nOn his last day I asked: any regrets?\n\nHe did not mention the salary.\nHe did not mention the missed promotions.\n\nWhat he said instead — I was not ready for it. 🧵",

            f"I share stories like this because they matter.\n\nIf you are searching for work right now — {WEBSITE_URL} posts fresh jobs daily. Freshers, graduates, everyone welcome.\n\nNow. My father's story. 👇",

            "His name is Rajendra.\n\nGovernment clerk. District office. Haryana.\n\nJoined in 1993 at age 24.\nSalary: ₹3,400/month.\n\nHe wore the same two formal shirts for the first 4 years.\nWashed them every night. Ironed them every morning.\n\nNobody at the office ever knew.",

            "He woke up at 5:30am every single day for 31 years.\n\nNo alarm needed. His body just knew.\n\nRain. Fever. Back pain. The day after my grandfather died.\n\nHe showed up.\n\nI was always asleep when he left.\n\nWe never once had breakfast together on a weekday.\n\nI only realized this when I was 19.",

            "When I was 14 I asked him why he never switched jobs.\n\nHalf our colony had moved to private companies.\nEveryone was talking about better salaries.\n\nHe looked at me and said:\n\n\"Beta, security matters more than salary.\nA government job means your family never sleeps hungry.\"\n\nI nodded. I did not argue.\n\nBut something about that answer never sat right with me.",

            "Things I found out about later. From my mother. Never from him.\n\n• His best friend's wedding in Chandigarh — he could not get leave.\n• My school annual function where I got first prize — he was in a file audit.\n• Our only family trip to Shimla — he got called back on day 2.\n\nHe never mentioned any of it.\n\nNot once.",

            "Last month he retired.\n\n31 years. Same desk. Same chair. Same office.\n\nSalary when he joined: ₹3,400/month.\nSalary when he retired: ₹41,000/month.\n\n31 years. ₹37,600 raise.\n\nThat is ₹1,213 per year.\n\nHis colleagues had a small lunch. Someone made a card. Everyone signed it.\n\nHe came home at 4pm with a cardboard box of his belongings.\n\nPut it in the corner of the bedroom. Did not say anything.",

            "That evening I sat with him.\n\nJust the two of us.\n\nI asked: \"Papa, any regrets?\"\n\nHe was quiet for a long time.\n\nI thought he would say the salary.\nOr the promotion that went to someone else in 2009.\nOr the transfer request that was rejected 3 times.\n\nHe said none of that.\n\nHe looked at me and said:\n\n\"I wish I had dropped you to school more.\"\n\nThat was it.\n\n31 years. And that was the only thing he wished he had done differently.",

            f"Fresh jobs at {WEBSITE_URL} 👇\nFind work that pays fairly. And gives you time.\n\n—\n\nMy father gave 31 years to a desk.\n\nHis only regret is time.\n\nTime he could not give to us.\n\nIf you are job hunting right now — find something that pays you well enough to live.\n\nBut also gives you time to drop your kids to school.\n\nThat is the job worth having.\n\nGo find it.\n\n#JobSearch #FresherJobs #LifeLesson",
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
