"""
Youth Naukri - Twitter Story Thread Bot
Generates a story-style thread using Claude API and posts via Twitter API.
Runs daily via GitHub Actions cron job.
"""

import os
import time
import json
import random
import tweepy
import anthropic

# ── Config ────────────────────────────────────────────────────────────────────
WEBSITE_URL = "https://youthnaukri.com"
WEBSITE_LABEL = "Youth Naukri"

# Topic pool — Claude picks one randomly each day for variety
TOPICS = [
    "A fresher from a tier-3 college who got rejected 50 times but landed a ₹6LPA job",
    "A commerce graduate who cracked a software company job without a CS degree",
    "A 2023 passout who was unemployed for 8 months, then got 3 offers in 1 week",
    "A girl from a small town who got a remote job and works from home",
    "A fresher who made one simple change to their resume and got instant callbacks",
    "A student who skipped placement drives and still got a better job than classmates",
    "A fresher who failed 12 interviews but cracked the 13th at a top MNC",
    "Someone who used LinkedIn wrong for 6 months, then fixed it and got hired in 2 weeks",
    "A BCA graduate who got hired at a product startup over IIT graduates",
    "A fresher who negotiated salary and got ₹1.5L more than the initial offer",
    "A 2024 passout who got ghosted by 30 companies, then discovered why and fixed it",
    "A fresher who built one small project and got an off-campus offer",
    "Someone who switched from BPO to IT using one free certification",
    "A fresher who cracked a government job while everyone told them to try private sector",
    "A girl who got rejected for 'lack of communication skills' and what she did next",
]

SYSTEM_PROMPT = """You are a Twitter content writer for Youth Naukri, a job platform for Indian freshers and young job seekers.

Your job is to write viral story-style Twitter threads that feel real, human, and relatable to Indian freshers (2020-2024 graduates) who are struggling to find jobs.

Rules:
- Write in simple, conversational English. Not corporate. Not fancy.
- Each tweet must be under 270 characters.
- Make it feel like a real story — with struggle, turning point, and lesson.
- Use numbers and specifics to make it feel authentic (months, rejection count, salary, city, college tier).
- Use emojis sparingly — only 1-2 per tweet max.
- DO NOT use hashtags in every tweet. Max 2-3 hashtags only in the last CTA tweet.
- The hook (tweet 1) must be so compelling that someone stops scrolling.
- Tweets 2-8 tell the story with one idea per tweet.
- Tweet 9 is the soft CTA with the website link.

Output format — return ONLY a JSON array of tweet strings, nothing else:
["tweet 1 text", "tweet 2 text", ..., "tweet 9 text"]
"""


def get_topic() -> str:
    """Pick a random topic from the pool."""
    return random.choice(TOPICS)


def generate_thread(topic: str) -> list[str]:
    """Call Claude API to generate the story thread."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_prompt = f"""Write a 9-tweet story thread about this topic:

"{topic}"

Remember:
- Tweet 1: Powerful hook. Specific. No link.
- Tweets 2-8: The story unfolds. One idea per tweet. Real details.
- Tweet 9: Soft CTA. End with: "Find daily fresher job openings at {WEBSITE_URL} 👇 #FresherJobs #Naukri"

Return ONLY the JSON array of 9 tweet strings."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": user_prompt}],
        system=SYSTEM_PROMPT,
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    tweets = json.loads(raw)
    assert isinstance(tweets, list), "Expected a list of tweets"
    assert len(tweets) >= 3, "Too few tweets generated"

    # Validate character limits
    for i, tweet in enumerate(tweets):
        if len(tweet) > 280:
            print(f"⚠️  Tweet {i+1} is {len(tweet)} chars — trimming")
            tweets[i] = tweet[:277] + "..."

    return tweets


def post_thread(tweets: list[str]) -> None:
    """Post the tweets as a thread using Twitter API v2."""
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )

    previous_tweet_id = None

    for i, tweet_text in enumerate(tweets):
        print(f"Posting tweet {i+1}/{len(tweets)}: {tweet_text[:60]}...")

        if previous_tweet_id:
            response = client.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=previous_tweet_id
            )
        else:
            response = client.create_tweet(text=tweet_text)

        previous_tweet_id = response.data["id"]
        print(f"  ✅ Posted tweet ID: {previous_tweet_id}")

        # Delay between tweets to avoid rate limits
        if i < len(tweets) - 1:
            time.sleep(3)

    print(f"\n🎉 Thread posted successfully! {len(tweets)} tweets.")


def main():
    print("🚀 Youth Naukri Twitter Bot starting...")

    # Step 1: Pick topic
    topic = get_topic()
    print(f"📝 Topic: {topic}")

    # Step 2: Generate thread with Claude
    print("🤖 Generating thread with Claude...")
    tweets = generate_thread(topic)
    print(f"✅ Generated {len(tweets)} tweets")

    # Step 3: Preview
    print("\n--- THREAD PREVIEW ---")
    for i, tweet in enumerate(tweets):
        print(f"\n[{i+1}] ({len(tweet)} chars)\n{tweet}")
    print("----------------------\n")

    # Step 4: Post to Twitter
    print("🐦 Posting to Twitter...")
    post_thread(tweets)


if __name__ == "__main__":
    main()
