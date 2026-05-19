"""
TEST VERSION - No Claude API needed.
Tests only the Twitter posting logic with a hardcoded thread.
Once this works, switch to post_thread.py (the real version).
"""

import os
import time
import tweepy

# ── Hardcoded test thread ─────────────────────────────────────────────────────
TEST_TWEETS = [
    "This boy from Muzaffarpur, Bihar sent 340 job applications. Got 2 replies. Both rejections. Then his cousin showed him one thing. 3 weeks later he had an offer letter. 🧵",
    "Meet Rajan Kumar. 2023 BCA passout. Patna University. First in his family to get a degree. His father sells vegetables at the local mandi.",
    "For 8 months after graduation, Rajan woke up at 6am, opened Naukri.com, and applied to every IT job he could find. Data entry. Support roles. Anything.",
    "His mother stopped telling relatives he was looking for a job. The questions were too painful. 'Beta kab lagega?' He stopped going to weddings.",
    "His resume looked like this: 12 pages long. Every school certificate listed. 'Participated in college fest 2019.' Hobbies: 'Cricket and Listening Music.'",
    "His cousin Vikash, working in Pune, visited during Chhath. Opened Rajan's resume. Went silent for 10 seconds. Then said — 'Yaar, ye delete kar. Sab kuch.'",
    "They rebuilt it in one evening. 1 page. Clean. 3 projects on top. A GitHub link. Skills listed properly. No 'Objective' line. No hobbies. No 12th marksheet.",
    "Rajan uploaded the new resume on a Monday night. By Thursday he had 2 calls. By the following week — an interview in Noida. ₹3.8 LPA. He took it without blinking.",
    "He called his father from the Patna railway station before boarding the train to Noida. His father cried. So did he. First salary — ₹5,000 sent home on day 1. 🙏\n\nIf you're a fresher still searching, fresh jobs posted daily at https://sabapna.com 👇\n#BiharKaBeta #FresherJobs #Naukri",
]


def post_thread(tweets: list[str]) -> None:
    """Post tweets as a thread using Twitter API v2."""
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
        print(f"  ✅ Tweet ID: {previous_tweet_id}")

        if i < len(tweets) - 1:
            time.sleep(3)

    print(f"\n🎉 Test thread posted! Check your Twitter profile.")


def main():
    print("🧪 TEST MODE — Using hardcoded thread (no Claude API)\n")

    print("--- THREAD PREVIEW ---")
    for i, tweet in enumerate(TEST_TWEETS):
        print(f"[{i+1}] ({len(tweet)} chars) {tweet}")
    print("----------------------\n")

    print("🐦 Posting to Twitter...")
    post_thread(TEST_TWEETS)


if __name__ == "__main__":
    main()
