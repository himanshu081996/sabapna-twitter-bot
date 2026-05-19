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
    "This fresher applied to 200 jobs. Got 0 replies. Then changed 1 thing. Got 3 interviews in a week. 🧵",
    "His name is Rohit. 2023 passout from a tier-3 college in UP. Civil engineering. No coding background.",
    "For 6 months he applied on Naukri every day. Same resume. Same cover letter. Nothing worked.",
    "His resume had this at the top: 'Objective: To work in a reputed organization and grow my skills.'",
    "That line alone was getting him rejected before anyone read further. Recruiters see 300 resumes a day.",
    "He rewrote the top section. Instead of objective, he wrote 3 bullet points of actual skills and projects.",
    "Week 1 after the change: 2 calls. Week 2: 1 more. He hadn't changed anything else. Just that one section.",
    "He got placed at ₹4.2 LPA. Not a dream job. But a start. And he negotiated it up from ₹3.8 LPA.",
    "If you're a fresher still searching, daily job openings are posted at https://youthnaukri.com 👇 #FresherJobs #Naukri",
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
