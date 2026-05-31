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
    seeds = random.sample(TOPIC_SEEDS, 3)
    seeds_text = "\n".join("- " + s for s in seeds)

    system = f"""You are a viral Twitter content strategist for Indian workplace audience.

These real posts went viral on Twitter — study the style:

{viral_context}

Generate ONE original workplace injustice topic for Indian professionals.

Use ONE of these seeds as inspiration:

{seeds_text}

STRICT RULES:
- One sentence only — maximum 15 words
- Must use Indian context — salaries in LPA, real situation
- NEVER use dollar signs or US context
- NEVER mention specific companies like Infosys, TCS, Wipro
- Include one specific detail (years, LPA amount, months, role)
- Return ONLY the topic sentence — nothing else"""

    return call_groq(system=system, user="Generate topic now. Max 15 words. Indian context. LPA only.", max_tokens=60)


CONTENT_FORMATS = (
    ["story"] * 4 +
    ["tips"] * 3 +
    ["question"] * 2 +
    ["hook_story"] * 1
)


def load_viral_examples(csv_path: str, top_n: int = 5) -> str:
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


def call_groq(system: str, user: str, max_tokens: int = 800) -> str:
    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
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
    seeds = random.sample(TOPIC_SEEDS, 3)
    seeds_text = "\n".join("- " + s for s in seeds)

    system = f"""You are a viral Twitter content strategist for Indian workplace audience.

These real posts went viral on Twitter — study the style:

{viral_context}

Generate ONE original workplace injustice topic for Indian professionals.

Use ONE of these seeds as inspiration:

{seeds_text}

STRICT RULES:
- One sentence only — maximum 15 words
- Must use Indian context — salaries in LPA, real situation
- NEVER use dollar signs or US context
- NEVER mention specific companies like Infosys, TCS, Wipro
- Include one specific detail (years, LPA amount, months, role)
- Return ONLY the topic sentence — nothing else"""

    return call_groq(system=system, user="Generate topic now. Max 15 words. Indian context. LPA only.", max_tokens=60)


def generate_story(topic: str, viral_context: str) -> str:
    content_format = random.choice(CONTENT_FORMATS)

    if content_format == "tips":
        system = """You are a viral Twitter content writer for Indian workplace audience.

Write a tips post that feels like real insider knowledge — something a senior professional whispers to a junior colleague.

FORMAT — follow this EXACTLY with blank lines between every element:

Line 1-2: Shocking hook with specific Indian numbers. No company names. Make it sting.

[blank line]

One short setup sentence that creates curiosity and makes people want to read all 5 tips.
Examples of good setup lines:
"Here is what nobody tells freshers before it costs them years:"
"I learned this the hard way so you don't have to:"
"Most people figure this out 5 years too late:"
"What HR knows but will never tell you:"
"The 5 things I wish I knew before wasting 3 years:"

[blank line]

Tip 1: [10-15 words of real specific advice]

[blank line]

Tip 2: [10-15 words of real specific advice]

[blank line]

Tip 3: [10-15 words of real specific advice]

[blank line]

Tip 4: [10-15 words of real specific advice]

[blank line]

Tip 5: [10-15 words of real specific advice]

[blank line]

One personal emotional question ending with 👇

GOOD EXAMPLE (copy this spacing exactly):
You stayed 8 years. They gave you 9% hike.
The new hire doing your job gets 6 LPA more.

Here is what nobody tells you before it is too late:

1. Never reveal your current salary — say "I'm looking for X LPA"

2. Always have a competing offer before you negotiate — leverage is everything

3. Internal hikes average 8-10%. Switching gives 25-40%. The math is simple.

4. Apply quietly while still employed — never resign without an offer letter in hand

5. Your loyalty is not an asset to them. Your market value is. Know the difference.

Have you ever realized too late that you stayed somewhere too long? 👇

BAD EXAMPLE — never write like this:
10 years at company, still 18 LPA.
1. Document achievements monthly
2. Get certified in emerging tech — 20% pay hike guaranteed
3. Skip one level, get 25% hike

(Bad because: uses company name, tips sound fake and guaranteed, no line spacing)

RULES:
- Indian context, salaries in LPA
- NEVER mention specific companies like Infosys, TCS, Wipro, Accenture
- Tips must be real tactics — never say "guaranteed" or fake percentages
- Blank line between EVERY element — hook, setup, each tip, question
- No hashtags, emojis only 👇 at end
- Return ONLY the post"""

        user = f"Write a tips post with blank lines between every element. Topic: {topic}"

    elif content_format == "question":
        system = """You are a viral Twitter content writer for Indian workplace audience.

Write a short controversial statement + question. MAX 40 words total.

Must make an Indian professional stop scrolling and want to reply.

FORMAT:
Line 1: Bold controversial truth about Indian work culture. Specific and stinging.
Line 2: One more line that deepens the pain.
Blank line.
Line 3: Direct personal question.
Line 4: "Agree or disagree? 👇" or "Yes or No? 👇" or "Drop your story 👇"

GOOD EXAMPLES:

Indian companies reward the loudest person in the room, not the hardest worker.

The quietest high performer is always the most underpaid.

Has this been your experience? 👇

---

Your company gave 8% hike. You switched and got 35%.

The math was always simple. You just trusted them too long.

Has switching ever changed your financial life? 👇

---

Loyalty in Indian IT means accepting less so your company can pay more to a new hire.

Drop your story 👇

BAD EXAMPLE — too weak and generic:
Is experience overrated in Indian IT?
Agree or disagree? 👇

RULES:
- Max 40 words
- Must feel personal and specific to Indian professionals
- No hashtags, no dollar signs
- Return ONLY the post"""

        user = f"Write an emotional debate question post about: {topic}"

    elif content_format == "hook_story":
        system = f"""You are a viral Twitter content writer for Indian workplace audience.

Write a hook + mini story that stops the scroll. Bigger conversation than usual.

FORMAT — follow spacing exactly:

Line 1: SHOCKING HOOK — specific number, years, salary. Hits immediately.
Line 2: One line that makes it worse.

[blank line]

8-10 dialogue exchanges. Each line 12-18 words. Real emotional human conversation.
Blank line between each exchange.

[blank line]

ONE devastating truth line — ironic, not a question.

[blank line]

Short question with 👇

GOOD EXAMPLE (copy spacing and conversation length exactly):
Your junior who you trained is now earning 8 LPA more than you.
The company called it "market correction." You call it betrayal.

Manager: We really value everything you've brought to this team over the years.

Employee: You valued it at 14 LPA for 4 years while he started at 22 LPA.

Manager: Salary bands are determined at the time of hiring, not by tenure.

Employee: I trained him for 3 months. He didn't know our systems at all.

Manager: He came in with strong negotiation skills during his offer process.

Employee: Nobody told me I could negotiate when I joined. I trusted the process.

Manager: That information has always been available to candidates who ask.

Employee: I've been here 4 years. I've never missed a deadline. Not once.

Manager: We genuinely appreciate your dedication to the team.

Employee: My EMI is 58,000 a month. I haven't asked for a raise in 2 years.

Manager: (Silence)

Employee: I have an offer. 21 LPA. I wanted to give you a chance first.

Manager: Let's explore what we can do on our end.

Employee: Where was this conversation 2 years ago?

Loyalty was never the deal. You just thought it was.

Has this been your experience? 👇

RULES:
- Indian context, salaries in LPA, no dollar signs
- Blank line between EVERY exchange
- Each line 12-18 words — complete emotional thought
- Contractions are essential: I've, don't, we'll, that's, you're
- NEVER use real names or company names
- Characters: Employee, Manager, HR, CEO, Candidate, Boss only
- No hashtags
- Return ONLY the post"""

        user = f"Write a hook + mini story with blank lines between every exchange. Make conversation bigger and more emotional. Topic: {topic}"

    else:
        system = f"""You are a viral Twitter content writer for Indian workplace audience.

Study these real viral posts and copy their exact style:

{viral_context}

Write a workplace dialogue story that feels like a real conversation overheard in an office.

STUDY THIS PERFECT EXAMPLE AND COPY THE STYLE EXACTLY:

---
Employee: I've been here 5 years. My appraisal was Outstanding. Again.

Manager: We really value everything you bring to the team.

Employee: The new joiner in my team is earning 8 LPA more than me.

Manager: Salary bands are determined by the time of hiring, not performance.

Employee: I trained him for 3 months. He arrived knowing nothing.

Manager: He negotiated well during his offer process.

Employee: I didn't know I was allowed to negotiate. Nobody told me.

Manager: That information is available to everyone.

Employee: My EMI is 62,000 a month. I've been managing on this for 2 years.

Manager: We understand that cost of living has gone up.

Employee: Then why hasn't my salary?

Manager: We'll take this up during the next compensation cycle.

Employee: You said the same thing last year.

Manager: (Silence)

Employee: I have an offer for 14 LPA. I wanted to give you a chance first.

Manager: We might be able to look at a retention discussion.

Employee: Where was this conversation 2 years ago?

He accepted the offer the next day.

The company posted a "we're hiring" job for his role the following week.

Same role. Higher salary band. For someone new.

Has this ever happened to you? 👇
---

WHAT MAKES THIS WORK:
- Lines are 10-18 words — complete thoughts, real human speech
- Emotion builds slowly — frustration, exhaustion, quiet anger
- "I didn't know I was allowed to negotiate. Nobody told me." — this is devastating because it's true
- Manager always sounds calm and reasonable — that's what makes it infuriating
- Personal detail (EMI 62,000) makes us feel the employee's pressure
- "Where was this conversation 2 years ago?" — hero's best line, quiet and devastating
- Ending is ironic — company immediately posts higher salary for same role

NOW write a completely NEW original story. Different topic, different situation, same emotional quality.

RULES:
- Each dialogue line must be 10-18 words — complete thought, real human emotion
- NO short choppy lines like "That's my work." or "Noted." — these kill the emotion
- Contractions are essential: "I've", "I'm", "don't", "you've", "we'll", "that's"
- Indian workplace context — salaries in LPA, no dollar signs
- One personal detail that makes hero human (EMI, sick family member, child, financial pressure)
- Villain sounds professional and calm throughout — never aggressive
- Hero sounds tired and human — not angry, not formal, just real
- 14-18 dialogue exchanges
- End with 2 ironic narrator lines + 1 short question with 👇
- NEVER use real names — only Employee, Manager, HR, CEO, Candidate, Boss
- No specific company names, no hashtags, no links
- Return ONLY the story"""

        user = f"Write a story where the dialogue feels like real exhausted humans talking, not robots. Topic:\n\n{topic}"

    result = call_groq(system=system, user=user, max_tokens=900)
    print(f"Format selected: {content_format}")
    return result


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
    print(f"\n--- POST ---\n{story}\n------------")
    print(f"Chars: {len(story)} | Words: {len(story.split())}\n")

    # Post to Buffer
    print("Step 3: Posting to Buffer...")
    post_id = post_to_buffer(story)
    print(f"Done! Buffer ID: {post_id}")


if __name__ == "__main__":
    main()
