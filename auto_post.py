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

# ── 150 Topic Seeds ───────────────────────────────────────────────────────────
TOPIC_SEEDS = [
    # SALARY INJUSTICE
    "salary gap discovered between two colleagues doing identical work",
    "new joiner negotiates 40% more than 3-year veteran for same role",
    "employee discovers colleague with same title earns 15 LPA more",
    "star employee poached by competitor at double salary. Previous company had refused 20% raise.",
    "employee rated top performer 3 years running. Denied raise for budget reasons. Gets LinkedIn message from competitor same week.",
    "company freezes hikes citing losses. Hires 5 senior managers at double pay same quarter.",
    "employee promoted with no salary increase. Just a new title and more work.",
    "HR says salary bands are confidential. Two employees compare notes. Gap is 8 LPA.",
    "employee asks for 15% raise after delivering record results. Offered 5%. Resigns. Counter offer is 25%.",
    "fresher joins at 4 LPA. Discovers colleague hired same day got 6 LPA for same role.",

    # PROMOTION INJUSTICE
    "promotion given to less experienced person who joined 6 months ago",
    "team lead position promised verbally for 2 years. Given to someone who joined 3 months ago.",
    "employee asked to mentor junior. Junior promoted above them. Mentor still waiting.",
    "long-serving employee skipped for promotion. External hire gets role and their team.",
    "employee given impossible targets for promotion. Hits them. Goalposts moved again.",
    "employee with 8 years experience rejected internally. Role given to fresher at lower cost.",
    "manager tells employee they are next for promotion. Announces own nephew's promotion next week.",
    "employee handles entire department during manager's 3 month leave. Gets no credit when manager returns.",

    # TOXIC MANAGER
    "manager takes full credit for employee's project in board meeting",
    "manager micromanages every email but takes credit for all results",
    "manager gives glowing verbal feedback. Submits poor written review.",
    "manager denies leave for employee's father's surgery. Takes 2 weeks vacation himself next month.",
    "manager publicly humiliates employee in team meeting for mistake manager caused",
    "manager assigns all interesting projects to favourite. Gives boring work to rest of team.",
    "manager reads employee's private chats on company laptop and shares with HR",
    "manager threatens bad reference if employee resigns before 6 months",
    "manager takes 3 days to reply to urgent emails. Expects employee reply within 10 minutes always.",

    # OVERWORK AND LEAVE
    "employee works 14 weekends straight, asks for one day off, denied",
    "employee takes mental health day, manager schedules 3 meetings during it",
    "company says family comes first. Employee takes leave for family emergency. Gets PIP next month.",
    "employee has 22 unused leaves expiring. Leave encashment policy quietly removed this year.",
    "employee works notice period fully. Reference withheld over minor dispute.",
    "employee given impossible deadline, works through weekend, deadline shifted anyway",
    "company emails: we respect your personal time. Meeting scheduled at 9pm same day.",
    "employee on medical leave gets performance warning for low productivity",
    "employee works 3 years without a single sick day. Gets denied leave for sister's wedding.",

    # LAYOFF AND FIRING
    "5 year employee laid off over video call with no prior warning",
    "employee asked to train replacement before their own layoff",
    "company sends wellness email during mass layoff week",
    "employee laid off on birthday. HR says timing was coincidental.",
    "employee discovers they were laid off when office access card stops working",
    "entire team laid off via automated email at midnight. No human contact.",
    "employee given 2 hours to clear desk after 7 years. Security escort included.",
    "company announces layoffs. CEO posts LinkedIn about resilience same day.",
    "employee rehired as contractor for same role after layoff. No benefits. Lower pay.",

    # HIRING HYPOCRISY
    "candidate clears 6 rounds, offer comes 50% below job posting",
    "candidate given verbal offer. Quits current job. Offer rescinded a week later.",
    "candidate rejected for overqualification. Role unfilled for 8 months after.",
    "company rejects experienced candidate. Hires less qualified at lower salary. Role vacant again in 3 months.",
    "job posting says 3-5 years experience. Candidate with 4 years rejected for lacking senior experience.",
    "HR ghosts candidate after final round for 3 weeks. Sends rejection after candidate joins competitor.",
    "company posts same job 4 times over 6 months. Never hires. Uses interviews to get market research.",
    "candidate asked to complete 8 hour assignment. Submits it. Never hears back.",
    "interviewer 45 minutes late. Asks candidate why they want to join. Ghosts them after.",

    # PERFORMANCE REVIEW INJUSTICE
    "outstanding performer gets average rating because manager dislikes them",
    "performance improvement plan given to employee who just had best quarter",
    "employee flagged a compliance issue. Got fired for raising it.",
    "employee catches error saving company 1 crore, gets thank you email. Colleague who did nothing gets bonus.",
    "employee with perfect attendance and delivery gets same rating as colleague who missed half the year.",
    "manager rates entire team average to avoid justifying high ratings to HR.",
    "employee gets poor rating for not being visible enough despite best results in team.",

    # LOYALTY PUNISHED
    "employee resigns, suddenly gets everything denied for 2 years",
    "company finds budget the moment employee puts in papers",
    "employee who trained entire team gets paid less than everyone they trained",
    "10 year employee gets same farewell as 6 month intern. Cake and a card.",
    "employee turns down 3 external offers out of loyalty. Company announces restructuring next month.",
    "long term employee asked to reapply for own role during restructuring. New hire gets it.",
    "employee covers for sick colleague for 3 months. Gets no recognition. Colleague gets promoted on return.",

    # WFH AND REMOTE WORK
    "WFH denied for employee, manager works from home same day",
    "remote work approved. Manager counts it against employee in annual review.",
    "company mandates return to office. CEO posts from beach same week.",
    "employee productive for 2 years WFH. Forced back to office. Resigns. Company allows WFH again.",
    "employee told WFH is permanent in offer letter. Policy reversed 6 months after joining.",
    "manager tracks employee mouse movement during WFH. Flags bathroom breaks as idle time.",
    "employee in another city asked to attend office 3 days a week. No relocation support offered.",

    # STARTUP CULTURE
    "startup founder promises ESOP. Company sold. Employees get nothing. Founder gets 40 crore.",
    "startup employee works 80 hour weeks for 2 years. Equity worthless. Founder raises new round at same valuation.",
    "startup promises market salary after funding. Gets funded. Salaries stay the same. Perks added instead.",
    "startup employee asked to do 4 roles. Told it is a learning opportunity.",
    "startup founder takes business class to investor meetings. Team flies economy for client visits.",
    "startup employee given stock options with 4 year cliff. Laid off after 3 years 11 months.",
    "startup celebrates culture of ownership. Employee who flagged process issue told to just execute.",
    "startup employee works weekends building product. Founder posts about hustle culture on LinkedIn.",

    # CAMPUS AND FRESHER
    "fresher joins dream company. Discovers onboarding batch of 200 has no projects assigned for 6 months.",
    "campus placement offer rescinded 2 months before joining. No explanation given.",
    "fresher negotiates salary. HR says it will affect team culture. Accepts lower offer. Senior colleague earns double.",
    "fresher assigned to bench for 8 months. Billed to client. Paid training stipend.",
    "intern completes project that goes to production. Gets certificate. No PPO. Senior gets promotion for it.",
    "fresher told role is in Bangalore. Joins. Posted to Indore on day one.",
    "campus hire given 1 year bond. Resigns after bond. Company withholds relieving letter anyway.",

    # GOVERNMENT JOB AND PSU
    "government employee works same post for 15 years. Junior with connections promoted twice.",
    "PSU employee given impossible transfer to punish them for raising complaint",
    "government employee denied promotion because they refused to pay bribe",
    "contract employee does same work as permanent for 10 years. Never made permanent.",
    "PSU employee performance review not done for 5 years. Promotion blocked as a result.",

    # FREELANCE AND GIG
    "freelancer completes full project. Client disappears before final payment.",
    "agency promises freelancer 3 month project. Cancels after 2 weeks. No kill fee.",
    "freelancer asked to do free sample work for big brand. Brand uses sample. Ghosts freelancer.",
    "gig worker works 60 hours in week. Platform changes algorithm. Earnings drop 40% overnight.",
    "freelancer raises invoice. Client says work quality was poor. Had approved same work 2 weeks ago.",

    # OFFICE POLITICS
    "employee reports workplace harassment. HR tells harasser. Employee transferred instead.",
    "HR shares employee salary complaint with the very manager complained about",
    "exit interview feedback shared with the manager being complained about",
    "employee with best results not considered for award. Colleague who lunches with manager wins.",
    "employee denied training budget. Manager uses same budget for team outing.",
    "company values say speak up. Employee speaks up. Gets managed out 3 months later.",
    "employee raises safety concern in factory. Flagged as troublemaker in performance review.",

    # CORPORATE HYPOCRISY  
    "company announces no bonus due to losses. CEO gets new car same week.",
    "company celebrates work-life balance award. Team averaging 70 hour weeks.",
    "CEO says people are our biggest asset. Layoffs announced next day.",
    "company sends mental health resources email. Fires employee who used them.",
    "company diversity report shows 40% women. All senior roles held by men.",
    "company posts about employee appreciation day. Same day announces salary freeze.",
    "company wins best employer award. Glassdoor rating is 2.1.",
    "company mandates unconscious bias training. Promotes same profile every cycle.",

    # NOTICE PERIOD AND EXIT
    "employee serves full 3 month notice. Relieving letter delayed 6 months.",
    "employee resigns. Company files lawsuit for taking client knowledge.",
    "employee asked to hand over work to team during notice. Team refuses to take handover.",
    "company holds last month salary as notice period buyout even though employee served full notice.",
    "employee on gardening leave during notice. Asked to attend calls daily.",
    "full time employee replaced by contractor for same role after resignation. No benefits. 30% lower cost.",

    # SALARY NEGOTIATION
    "employee asks for raise. Denied. Gets competing offer. Company suddenly has budget.",
    "employee negotiates salary during appraisal. Manager says it will be noted negatively.",
    "employee given counter offer to stay. Accepts it. Passed over for promotion that year for being disloyal.",
    "employee asks for market rate. HR says current salary is already competitive. LinkedIn shows otherwise.",
    "joining bonus clawed back when employee quits after 11 months. Bond was 12 months.",

    # MISCELLANEOUS REAL SITUATIONS
    "employee relocates city for job. Role eliminated 3 months after joining.",
    "employee takes paternity leave. Comes back to find role restructured away.",
    "team hits record numbers. Bonuses cancelled due to global headwinds.",
    "company fires employee for social media post praising a competitor product",
    "employee given two roles after colleague laid off. Salary stays same. Title stays same.",
    "company sends employee to expensive certification. Asks them to sign 2 year bond or repay.",
    "employee asks about career growth. Manager says just be patient. Manager leaves company next month.",
    "company announces ESOP. Fine print: vests only if company IPOs. Company never IPOs.",
    "employee transferred to new city. Moving allowance promised. Never paid.",
    "employee completes MBA sponsored by company. Immediately asked to repay full fees on resignation.",
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


# Content format weights — 40% story, 30% tips, 20% question, 10% hook
CONTENT_FORMATS = (
    ["story"] * 4 +
    ["tips"] * 3 +
    ["question"] * 2 +
    ["hook_story"] * 1
)


def generate_story(topic: str, viral_context: str) -> str:
    """Generate viral content using Groq — varies format each time."""

    content_format = random.choice(CONTENT_FORMATS)

    if content_format == "tips":
        system = """You are a viral Twitter content writer for Indian workplace audience.

Write a short punchy tips/list post. MAX 150 words total.

FORMAT:
Line 1: One shocking/bold statement (the hook). Make it specific with numbers.
Blank line.
4-5 numbered tips. Each tip max 10 words. Specific and actionable for Indian professionals.
Blank line.
End with ONE question to drive replies.

EXAMPLE:
Most Indians leave 5-8 LPA on the table every year. Here's why.

1. First offer is never the best offer — always counter
2. Internal raises average 8%. Switching gives 30-40%.
3. Low base salary compounds against you for years
4. Companies budget 20% above offer — they expect negotiation
5. One conversation can add 50L to your 10 year earnings

Have you ever negotiated your salary? What happened? 👇

RULES:
- Indian context, salaries in LPA
- No hashtags, no emojis except 👇
- Return ONLY the post"""

        user = f"Write a tips post about: {topic}"

    elif content_format == "question":
        system = """You are a viral Twitter content writer for Indian workplace audience.

Write a short controversial question post that sparks debate. MAX 50 words.

FORMAT:
Line 1-2: One bold controversial statement about Indian work culture. Specific, punchy.
Blank line.
Line 3: Direct question that makes people want to reply.
Line 4: "Drop your answer 👇" or "Yes or No? 👇"

EXAMPLES:
Indian companies don't reward performance. They reward visibility.

The best performer in your team is probably the lowest paid.

Agree or disagree? 👇

---

Switching jobs every 2 years is not disloyalty. It's financial intelligence.

Has job hopping ever worked in your favor? 👇

RULES:
- Max 50 words
- Must make Indian professionals feel seen or slightly angry
- No hashtags
- Return ONLY the post"""

        user = f"Write a debate question post inspired by: {topic}"

    elif content_format == "hook_story":
        system = f"""You are a viral Twitter content writer for Indian workplace audience.

Write a SHORT punchy hook + mini story. MAX 120 words.

FORMAT:
Line 1-2: POWERFUL HOOK — specific numbers, shocking statement, relatable pain.
Blank line.
3-5 exchanges of dialogue (just the key moment — not full story)
Blank line.
1 line lesson/takeaway
1 question to drive replies 👇

EXAMPLE:
Your junior who you trained is now earning 8 LPA more than you.
This is not an accident. This is policy.

Manager: We value your loyalty here.
Employee: My loyalty or my silence?
Manager: (Silence)

Companies don't reward loyalty. They rely on it.

Has this happened to you? 👇

RULES:
- Indian context, salaries in LPA
- NEVER use real names — only Employee, Manager, HR, CEO, Candidate, Boss
- Hook must use specific numbers or relatable situation
- Return ONLY the post"""

        user = f"Write a hook + mini story about: {topic}"

    else:
        # Story format — condensed and punchy
        system = f"""You are a viral Twitter content writer for Indian workplace audience.

Study these real viral posts and copy their style exactly:

{viral_context}

Write a SHORT punchy workplace dialogue story. MAX 200 words.

KEY RULES FROM VIRAL EXAMPLES:
- Start with the most tense moment — no setup needed
- Write like real humans talk — contractions, interruptions, short reactions
- "Interesting." "Wait… what?" "Noted." — these beat long sentences
- Villain sounds reasonable — that's what makes it devastating
- Hero reacts like a real person — shock, quiet anger, resignation
- Specific numbers make it real (years, LPA, days, %)
- One personal detail makes hero human (EMI, father's treatment, child's school)
- Each line 8 to 15 words — complete thought, not too short, not too long

STRUCTURE:
Hook line (1-2 lines setting the scene — punchy)
Blank line
10-14 dialogue exchanges (SHORT — under 10 words each)
Blank line
2 narrator lines (ironic devastating truth)
1 question line 👇

RULES:
- Indian workplace context, salaries in LPA
- NEVER use real names — only Employee, Manager, HR, CEO, Candidate, Boss
- No hashtags, no links, no title
- Return ONLY the story"""

        user = f"Write the condensed story about:\n\n{topic}"

    return call_groq(system=system, user=user, max_tokens=800)


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
