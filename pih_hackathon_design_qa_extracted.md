INTERNAL HACKATHON — DESIGN DOCUMENT

Project Intelligence Hub (PIH)

Turning scattered project knowledge into answers

Event date: July 24, 2026 · Starts 6:30 AM ET · 10 hours · Globally synced

Offices: Hyderabad (4:00 PM IST) · Bogotá (5:30 AM COT) · Uruguay (7:30 AM UYT) · Maryland (6:30 AM EDT) · Denver (4:30 AM MDT) · Online

Includes: full event design + the company-wide Q&A (Section 10)

Contents

1. Executive summary3

2. The problem we're solving3

3. The goal3

3.1 Answer what we can answer3

3.2 Flag, guide, and capture what we can't4

3.3 Generate a project one-pager4

4. What we're asking teams to build4

4.1 Examples of valid shapes (all equally welcome)4

5. Event format & logistics4

5.1 When & where4

5.2 Tooling & accounts (provided)5

5.3 Data & infrastructure — deliberately simplified5

6. Teams5

7. Deliverable & submission5

8. Evaluation scorecard7

8.1 How we kept technical scoring fair from a video7

8.2 Scoring mechanics8

9. Addressing early feedback8

10. Q&A9

Appendix A — Project one-pager: reference format12

1. Executive summary

Every project we deliver generates knowledge worth keeping: who led it, who signed the deal, what we built, which techniques and tech stack we used. Almost none of it lands somewhere a colleague can find later. It's spread across SharePoint decks, email attachments, and individual laptops, and the most useful details often aren't written down at all; they live in the head of whoever did the work. So people rebuild an understanding of work we've already done, write capability stories from a blank page, and let relevant past engagements go unmentioned in the sales cycle when they'd have helped.

The hackathon in one sentence

A 10-hour, company-wide, cross-geography build: teams create something that lets anyone ask a question about our past projects and get a real answer, and that, when the answer isn't in our materials, flags the gap and captures what's missing so it's there next time.

Early feedback flagged two worries, so let's settle both now. This hackathon is not:

A data-science-only event. No technical background is needed to take part or to win. Insight into the problem, a usable result, and real-world potential count for as much in the scoring as the engineering does.

An app-building exercise. A Claude skill, a Cowork or Codex way of working, or an agent all count as full submissions. A traditional dashboard is welcome, but nobody has to build one.

2. The problem we're solving

Say someone needs to know more about a past project: who led it, who signed the deal, what shipped, what technique or stack was used. There's no single place that holds the answer. The pieces are scattered:

A deck sitting in SharePoint

A Word document buried in an email attachment

A file on someone's laptop

And plenty that was never written down, living only in someone's memory.

Three costs follow from that:

Re-discovery tax. Time goes into rebuilding an understanding of work already done.

Narratives from scratch. Capability stories and case studies get written from a blank page instead of assembled from what we already know.

Missed sales moments. A relevant prior engagement stays buried during the sales cycle, right when it would have made the strongest proof point.

3. The goal

We want a solution that can answer questions about our existing projects — and turn what it knows into shareable artifacts. It has three aspects, and all three matter for a strong submission.

3.1 Answer what we can answer

A user should be able to search or ask a question in natural language and get an answer grounded in the materials we already have — decks, documents, and other project files.

3.2 Flag, guide, and capture what we can't

When a question can't be answered from existing materials, the solution shouldn't just say "I don't know." It should:

Flag the gap clearly (e.g. "we have no material describing the tech stack for this project").

Suggest how to close it: for example, surface the name of the project lead and prompt the user to reach out and ask.

Capture the answer and make it stick. Once the user hears back, there has to be a way to add that answer into the system so every future session already has it.

3.3 Generate a project one-pager

Beyond answering point questions, the solution should be able to pull everything it knows about a single project into a polished, shareable one-pager — a case-study / sales-brief style summary (executive summary, the challenge, our solution, key features, and who delivered it) generated from the underlying materials rather than written from a blank page. This is the direct answer to the “narratives from scratch” cost above: the same knowledge that powers Q&A also composes the narrative artifact that sales and delivery teams reuse. Where the materials don’t cover a section, the one-pager should flag the gap (as in 3.2) rather than invent it.

4. What we're asking teams to build

Deliverables can take almost any form: an app, an agent, a Claude skill, a documented way of working, or something we haven't thought of. There are only two hard requirements:

It tackles the problem statement. The focus is on solidifying the vision of the solution and building a foundation that can be worked on further — not on shipping something production-perfect in 10 hours.

It has an interface a user can interact with directly. This does not have to be a pre-built dashboard or custom UI — having Claude present information in chat or Cowork is perfectly fine. But it cannot be only a backend API with no way for a person to interact with it.

4.1 Examples of valid shapes (all equally welcome)

A Streamlit app that runs locally, where the user uploads the files, processes them, and sees a dashboard.

An AWS (or Snowflake) pipeline that processes the files into a knowledge base, with a chatbot in front for the user to interact with.

A Claude or Codex skill that tells the agent how to extract information from the files, answer questions, and generate an interface directly in the chat.

5. Event format & logistics

5.1 When & where

Detail

Value

Date

Friday, July 24, 2026

Start (reference)

6:30 AM ET — the globally synced kickoff time

Start (local time by office)

Hyderabad — 4:00 PM IST

Uruguay — 7:30 AM UYT

Maryland — 6:30 AM EDT

Bogotá — 5:30 AM COT

Denver — 4:30 AM MDT

Duration

10 hours, globally synced across US, LATAM, and India

In-office locations

Hyderabad · Bogotá · Uruguay · Maryland · Denver

Online

Fully supported — anyone can participate from anywhere

Food

Breakfast / lunch / dinner provided depending on office (per local schedule)

5.2 Tooling & accounts (provided)

Resource

What each participant / team gets

Claude Enterprise

$120-tier Claude Enterprise limit for every participant

Codex Enterprise

Codex Enterprise account for every participant

API keys (on request)

Per team: one OpenAI or Anthropic API key with a $50 limit

Cloud (on request)

AWS or Snowflake resources available if a team wants them

5.3 Data & infrastructure — deliberately simplified

We are removing infrastructure from the equation so teams focus on the solution, not on wrestling with plumbing.

Project files in all common formats (PPTX, DOCX, Markdown, etc.) will be provided from a downloadable location at the start.

The project files come with two question sets: a train set with correct answers, for building and self-checking, and a test set of questions only, which teams answer and submit for judging (ground-truth answers stay with the judges).

No real-time system connections required. Teams are not expected to connect to SharePoint, S3, or any external system live. Working entirely with data on the local machine is expected and fine.

Deploy anywhere — or nowhere. There is no requirement on where development happens or where it deploys. Working completely local is 100% acceptable.

6. Teams

Team size is 3–5 people, with no exceptions.

Cross-functional and cross-geography teams are strongly encouraged.

Through the sign-up form, teammates can enter the same team name to be grouped together.

Participants without a team can sign up without a team name and will be matched to the best available team. The form asks only for name, geography, and "superpowers."

7. Deliverable & submission

Each team submits a video recording that demonstrates their solution.

The solution does not need to be deployed or hosted anywhere.

It may be tested if the team provides access, so judges can assess its capabilities more thoroughly — but a working demo video is the required artifact.

We recommend every team read the evaluation scorecard (Section 8) before and during the build, so the demo speaks directly to how they'll be judged.

Alongside the video, each team submits answers to a held-out test set. Two sets go out with the project files at kickoff: a train set that includes the correct answers, for teams to build and check against, and a test set of questions only. Teams run their solution over the test set and submit its answers. Judges hold the ground-truth answers for the test set and score each submission against them, so accuracy is measured on questions the teams never saw answered — not on material they could tune to.

Default format: a spreadsheet (CSV), one row per test question, with a column for the answer and one for the source where applicable — openable by anyone, no technical setup.

Alternative: the same test set as JSON, for teams who'd rather submit programmatically.

Answering unanswerable questions counts. If a team's solution can't find an answer in the materials and instead flags the gap and points to who could answer it, that's recorded as the answer — a correct "we don't have this, here's who to ask" is a valid result, not a blank.

Alongside the video and the test-set answers, each team also submits one generated project one-pager. Using its own solution, the team picks a single project from the provided materials and generates a polished, shareable summary of it — a case-study / sales-brief style page covering the executive summary, the challenge, our solution, and key features, assembled from the materials rather than written from scratch. This is where the solution shows it can do more than answer questions: it composes the kind of capability story we reuse in the sales cycle. Layout polish matters less than that the page is genuinely built from the project knowledge; any form works — a document, a Cowork or Claude artifact, or an exported file.

What a great demo video shows

A real question answered from the provided materials, with the answer visibly grounded in a source.

A question that can't be answered — and the solution flagging it, suggesting who to ask, and then capturing the returned answer.

Proof that the captured answer persists: ask again in a fresh session and it's now known.

A quick nod to accuracy against the golden set.

8. Evaluation scorecard

Judges come from all functions — not just engineering — which keeps scoring honest to the fact that a great solution is as much about insight and usability as it is about technical depth. The scorecard below adapts a standard hackathon rubric to our problem, and adds a dedicated technical dimension that can realistically be assessed from a demo video (with optional hands-on testing).

Five criteria, each scored 1–4. Total possible: 20 points.

Criteria

Underachieving — 1

Average — 2

Proficient — 3

Exceptional — 4

Creativity, insight & relevance

Idea is basic, unclear, or only loosely tied to the project-knowledge problem.

Addresses the problem in a straightforward way, but the approach feels familiar or limited in originality.

Clearly solves the problem and adds creative features, workflows, or use cases that improve it.

Solves it in a highly original, thoughtful way. Shows deep insight into the real user need and stands out from typical approaches.

Answering from existing materials

Little or no working retrieval; test-set answers are absent, wrong, or ungrounded.

Answers some of the test set from the files, but coverage is thin and grounding to sources is weak or unclear.

Reliably answers a range of the test set, grounded in the provided materials, with visible sourcing.

Answers the held-out test set accurately and grounded, and clearly works beyond it — handling questions, phrasings, or materials it was never shown, rather than fitting to the test set.

Gap-flagging & knowledge capture

No handling of unanswerable questions; gaps go unflagged and nothing is captured.

Flags some gaps, but guidance is generic and captured info doesn't reliably persist.

Flags gaps, suggests how to close them (e.g. names the lead), and captures answers that persist to future sessions.

A smooth flag → guide → capture → persist loop that demonstrably enriches the system, with thoughtful UX around who to ask and how info re-enters.

Usable experience (MVP)

More concept than product; a user would struggle to understand or use it.

Works in a limited way, but the experience is rough or needs the team to explain it.

Usable and demonstrates the core experience clearly; a user can complete the main workflow (chat, Cowork, or UI).

Feels like a complete, usable product or way of working — intuitive and smooth end-to-end, whatever the interface.

Impact & potential

Limited practical value or unclear future use; hard to expand or apply at Blend.

Some useful potential, but audience, scale, or real-world application aren't fully developed.

Clear real-world value; could grow into a more complete tool with more time or resources.

Strong potential to become a real, scalable Blend tool — important need, clear audience, realistic path to adoption.

8.1 How we kept technical scoring fair from a video

We added a technical dimension ("Answering from existing materials" plus the technical half of "Gap-flagging & capture") but scoped it to what a judge can actually see in a recording:

Grounding is shown, not claimed. Teams demo answers with the source visible, so retrieval quality is observable rather than asserted.

Accuracy against the golden set. Because ground-truth answers are provided, teams can show a quick correct-vs-total tally on camera — lightweight, credible evaluation evidence.

Persistence is demonstrable. "Ask, get a gap flag, add the answer, ask again in a fresh session" is a visible loop, not an internal detail.

Optional hands-on testing. Teams may share access; judges can probe further, but no submission is penalized for keeping it to the video.

8.2 Scoring mechanics

Each criterion is scored 1–4 by each judge; scores are averaged across judges.

Maximum total is 20 points (5 criteria × 4).

Judges span all functions so that non-technical strengths (insight, usability, impact) carry equal weight to technical execution.

9. Addressing early feedback

When we first floated this internally, two concerns came back. We've designed the event — and will communicate it — to directly resolve both.

What we heard

How this design answers it

"This is a data-science-team, very technical hackathon."

Judging weights insight, usability, and impact equally with technical execution; judges come from all functions; teams are required to be cross-functional. Non-technical contributors are essential to a winning team, not optional.

"You're making everyone build an app — that feels old-school in a Cowork/Codex world."

No app is required. A Claude skill, a Cowork/Codex way of working, or an agent are first-class deliverables. The only interface requirement is that a human can interact with it — chat counts.

"There's already an existing initiative (X) working on this — the hackathon duplicates that effort."

The two don't overlap, even though the problems sound alike on the surface. Initiative X is a defined effort with its own scope; this hackathon is an open, exploratory event pushing people to test the boundaries of a new way of working, with no fixed solution in mind. The rubric explicitly rewards scalable, extensible submissions, so whatever comes out is built to plug into existing or future initiatives — including X — rather than compete with them. It also widens participation well beyond the technical team, bringing in people from every function to contribute and apply their own backgrounds, which is a different goal from what X is set up to do.

10. Q&A

Two myths, busted before we start

① You do not need to be technical, and you do not need to be on the data science team. Judging rewards insight, usability, and impact just as much as engineering — and every team is cross-functional on purpose.

② You do not have to build an app. A Claude skill, a Cowork or Codex way of working, or an agent all count. If Claude answers in chat, that's a valid interface. Building a dashboard is optional.

The basics

Q  What are we actually building?

A   A solution that answers questions about the projects we've delivered — who led it, who signed the deal, what we built, what techniques and tech stack we used — by drawing on our existing project materials.

And crucially: when a question can't be answered from what we have, the solution should flag the gap, suggest how to get the answer (like pointing you to the project lead to ask), and give you a way to add that answer back in so it's remembered for everyone next time.

Q  Why are we doing this?

A   Right now that knowledge is scattered — a deck in SharePoint, a doc in an email, a file on someone's laptop, and a lot of it only in people's heads. So we waste time re-discovering work we've already done, write capability narratives from scratch, and miss chances to bring relevant past work into live sales conversations. We want to fix that.

Q  When, how long, and where?

A   Friday, July 24, 2026, running 10 hours, globally synced across the US, LATAM, and India. The kickoff is 6:30 AM ET, which in local time is 4:00 PM in Hyderabad (IST), 5:30 AM in Bogotá (COT), 7:30 AM in Uruguay (UYT), 6:30 AM in Maryland (EDT), and 4:30 AM in Denver (MDT). Join in-office at Hyderabad, Bogotá, Uruguay, Maryland, or Denver — or fully online from anywhere. Depending on the office, breakfast, lunch, and/or dinner will be provided.

Teams & sign-up

Q  How big are teams?

A   Teams are 3–5 people, with no exceptions. We strongly encourage cross-functional and cross-geography teams.

Q  I don't have a team. Can I still join?

A   Yes! Sign up without a team name and we'll match you to the best available team. Just tell us your name, your geography, and your "superpowers." If you already have teammates, everyone enters the same team name on the form to be grouped together.

Q  I'm not a developer. Is there a place for me on a team?

A   Absolutely — and a strong team needs you. Understanding the real user need, designing a usable experience, shaping the way-of-working, and telling the story in the demo are all things the scorecard rewards. Cross-functional teams tend to do better, not worse.

"Is this really for me?"

Q  Isn't this a technical, data-science-team hackathon?

A   No. This is a company-wide event and judges come from every function. Of the five scoring criteria, three — creativity and insight, usability, and real-world impact — need no technical background at all. Technical execution is one part of the picture, not the whole thing.

Q  Do I have to build an app? That feels old-school with Cowork and Codex around.

A   You don't. We deliberately accept any shape of deliverable, including but not limit to:

A Claude skill that teaches the agent how to read the files, answer questions, and generate an interface in chat.

A Cowork or Codex way of working — a repeatable, agent-native approach.

An agent, a local Streamlit app, or an AWS/Snowflake pipeline with a chatbot — if that's your style.

The only interface rule: a human has to be able to interact with it directly. Claude answering in chat counts. A backend-only API with no way to interact does not.

Q  What makes a submission stand out?

A   Nailing the full loop: answer what we can from the materials, and for what we can't — flag it, guide the user to who can answer, capture that answer, and make it persist so the next person just gets it. That capture-and-remember loop is the heart of the problem.

Tools, data & logistics

Q  What tools and accounts do we get?

A   Every participant gets a $120-tier Claude Enterprise limit and a Codex Enterprise account for the hackathon. Each team can also request one OpenAI or Anthropic API key with a $50 limit, and AWS or Snowflake resources on request.

Q  What data will we work with, and do we connect to live systems?

A   At kickoff we'll provide project files in all common formats (PPTX, DOCX, Markdown, and more) from a downloadable location, plus a "golden set" of correct answers so you can show how accurate your solution is. You do not connect to SharePoint, S3, or any external system in real time — working entirely with the provided files on your local machine is expected and completely fine.

Q  Where do we have to deploy or host it?

A   Nowhere, if you don't want to. There's no requirement on where you build or deploy — working 100% locally is perfectly acceptable. Cloud resources are available on request if you'd like them.

Submission & judging

Q  What do we submit, and how are we judged?

A   A video recording that demonstrates your solution — it doesn't need to be deployed or hosted anywhere. You can optionally share access if you'd like judges to explore it further. Judging is on five criteria, each scored 1–4 (20 points total): creativity & insight; answering from existing materials; gap-flagging & knowledge capture; usable experience; and impact & potential. We recommend reading the scorecard (Section 8) before you build.

Q  How can judges assess the technical side fairly from just a video?

A   We scoped the technical criteria to what a recording can actually show: answers with the source visible (so grounding is seen, not claimed), a quick accuracy tally against the golden set, and a live demonstration of the flag → capture → persist loop (ask, get a gap flag, add the answer, ask again in a fresh session). Optional hands-on testing is available but never required.

Q  Besides the video, do we submit anything else?

A   Yes — your solution's answers to a test set. At kickoff you get two sets: a train set with answers, to build and check against, and a test set of questions without answers. You run your solution over the test set and submit what it produces (a spreadsheet by default, or JSON if you prefer), with a source for each answer where relevant. Judges score those against the ground-truth answers they hold. If your solution flags a question as unanswerable and names who could answer it, record that — it counts. You also submit one generated project one-pager: your solution's polished, shareable summary of a single project (executive summary, the challenge, our solution, key features), built from the materials rather than written by hand.

Still have a question?

Reach out to the hackathon committee via the announcement thread and we'll get you an answer — and add it here if it's one others will want too. We can't wait to see what you build.

Appendix A — Project one-pager: reference format

The one-pager deliverable (Section 7) should read like a short case study or sales brief for a single project, generated from that project’s materials — not filled in from a fixed template. The goal is a polished, shareable narrative. As a guide, a strong one-pager usually carries:

A title and one-line descriptor — the project name and, in a phrase, what it was.

A “generated on” date, signalling the page was assembled from materials rather than written by hand.

Executive summary — the engagement and its headline outcomes, in a few sentences.

The challenge — the situation before the work.

Our solution — what we built, and how the team was set up to deliver it.

res — the specific capabilities delivered.

The example below shows the shape — a real Blend360 case study rendered in this format. Teams don’t need to match its layout or length; it’s here to make the target concrete.

ML Data Science Model Workflows in Snowflake — Norwegian Cruise Line (NCL)

Generated 5/09/2026 · Sales Brief

Norwegian Cruise Line — A Blend360 Case Study

Executive summary

Blend360 partnered with Norwegian Cruise Line (NCL) to transform a fragmented, multi-platform data science environment into a unified, production-ready ML workflow platform built natively on Snowflake. The result: model build times dropped from six months to six weeks, feature engineering time fell from four weeks to one, and production release cycles compressed from multiple days to a matter of hours. This engagement is a showcase of Blend360’s end-to-end capability — from data engineering and MLOps architecture to business-facing monitoring tools — delivered by a focused, expert team that drove measurable impact at every stage of the ML lifecycle.

The challenge

NCL’s data science team was operating in isolation — building predictive models across a patchwork of disconnected platforms including R, SAS, Salesforce Einstein, and local Python environments. Each new modeling effort required manual data exports, redundant feature engineering, and independent infrastructure setup. Business-critical feature definitions varied from model to model. Models lived in silos with no centralized repository, no consistent governance framework, and no systematic way to monitor production performance or detect drift.

The cumulative cost was significant: slow time-to-insight, duplicated effort, data sprawl, and no scalable path forward. NCL needed more than a technical fix. They needed a platform — one that could unify their environment, govern their models, and scale with their ambitions.

Our solution

Blend360 designed and delivered a centralized, Snowflake-native ML platform that consolidated NCL’s entire data science operation under one governed architecture. Rather than patching existing workflows, we reimagined the full ML lifecycle from the ground up — migrating and reformulating legacy models from multiple platforms into a single, unified environment that the team could build on, monitor, and extend.

Our six-person delivery team — comprising a delivery lead, two data scientists, two data engineers, and a dedicated project manager — worked directly with NCL’s Director of Data Science to align technical execution with business priorities at every stage of the engagement.

Key features

Global Feature Store — A centralized Snowflake-native feature store that standardizes data definitions and makes reusable features available across all predictive models, eliminating the inconsistency and redundant engineering that previously plagued each new modeling effort.

Central Model Repository — A governed, centralized location for all predictive models, enabling consistent versioning, discovery, and reuse across the team.

The full brief continues with additional platform capabilities — production monitoring and drift detection, and business-facing dashboards — that round out the ML lifecycle.