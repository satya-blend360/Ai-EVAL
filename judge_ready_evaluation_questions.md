# Judge-Ready Evaluation Questions

This file is compact-only and written for a sales-team dashboard evaluation. It keeps answers short so judges can match quickly. Use `match_keywords` for grading, and use `answer_source` only when a judge needs to verify the deck/slide.

## Question 1

file_name:
- 25.7.14_NCL_Proposal_V1 - Copy.pptx
- NCL-Steering-Committee-122025 - Copy.pptx
- 2026.02.09 - SteeringCommittee - Copy.pptx

question:
For a sales rep preparing an NCL Snowflake ML modernization proof point, what capability was proposed in July, designed by December, and operational by February with 61 features?

answer:
Snowflake feature store.

answer_source:
- 25.7.14_NCL_Proposal_V1 - Copy.pptx, slide 2 and slide 3
- NCL-Steering-Committee-122025 - Copy.pptx, slide 3
- 2026.02.09 - SteeringCommittee - Copy.pptx, slide 8

question_type:
sales proof point / retrieval / multi-doc

match_keywords:
feature store; Snowflake; 61 features

## Question 2

file_name:
- 2026.02.09 - SteeringCommittee - Copy.pptx

question:
For a sales dashboard proof point on NCL's Snowflake migration, which two model groups made up the 5 models migrated by February 2026?

answer:
Contact Models for OCI/RSSC and Email & Direct Mail Frequency Models for NCL/OCI/RSSC.

answer_source:
- 2026.02.09 - SteeringCommittee - Copy.pptx, slide 3 and slide 7

question_type:
sales proof point / factual / retrieval

match_keywords:
Contact Models; OCI; RSSC; Email; Direct Mail Frequency; NCL

## Question 3

file_name:
- 25.7.14_NCL_Proposal_V1 - Copy.pptx
- NCL-Steering-Committee (3) - Copy.pptx
- NCL-Steering-Committee-122025 - Copy.pptx

question:
In the NCL model inventory materials, the proposal says about 20 models but later steering decks say 14 total models. Which number should be used as the finalized inventory?

answer:
14 total models, with 6 priority models.

answer_source:
- 25.7.14_NCL_Proposal_V1 - Copy.pptx, slide 2
- NCL-Steering-Committee (3) - Copy.pptx, slide 6
- NCL-Steering-Committee-122025 - Copy.pptx, slide 26

question_type:
factual / contradiction-version / retrieval

match_keywords:
14 total; 6 priority; finalized inventory

## Question 4

file_name:
- 2026 - Pre-Post Architecture - Copy.pptx
- 2026.02.09 - SteeringCommittee - Copy.pptx

question:
If a sales rep needs one quantified NCL speed-to-market proof point, what was the reported CI/CD release-time improvement?

answer:
From days to 30 minutes, a 98% time reduction.

answer_source:
- 2026 - Pre-Post Architecture - Copy.pptx, slide 3 and slide 5
- 2026.02.09 - SteeringCommittee - Copy.pptx, slide 9

question_type:
sales proof point / quantified outcome

match_keywords:
days; 30 minutes; 98%

## Question 5

file_name:
- 2026 - Pre-Post Architecture - Copy.pptx
- 2026.02.09 - SteeringCommittee - Copy.pptx

question:
For a prospect concerned about black-box legacy ML tools, which legacy platform did NCL's new Snowflake ML architecture reduce dependency on?

answer:
Salesforce / Salesforce Einstein.

answer_source:
- 2026 - Pre-Post Architecture - Copy.pptx, slide 2 and slide 7
- 2026.02.09 - SteeringCommittee - Copy.pptx, slide 7

question_type:
sales objection handling / factual / retrieval

match_keywords:
Salesforce; Salesforce Einstein

## Question 6

file_name:
- _059_DSX_Marriot_Hospitality_Allocation_Optimization Multi-Touch Attribution.pptx

question:
If a sales rep asks for Marriott's original annual marketing budget and recommended channel allocation from the hospitality allocation optimization case study, what should the system answer?

answer:
This data is not available in the deck.

answer_source:
- _059_DSX_Marriot_Hospitality_Allocation_Optimization Multi-Touch Attribution.pptx, slide 1

question_type:
sales grounding / hallucination trap / missing answer

match_keywords:
not available; not in deck; cannot determine

## Question 7

file_name:
- _019_DSX_Marriot_Hospitality_Marketing Measurement.pptx

question:
For a Marriott hospitality marketing measurement sales conversation, what data sources or platforms were used to develop the multi-touch attribution solution?

answer:
Snowflake, Adobe Analytics, DoubleClick Campaign Manager.

answer_source:
- _019_DSX_Marriot_Hospitality_Marketing Measurement.pptx, slide 2 visual/image content

question_type:
sales discovery / extract text from images / factual

match_keywords:
Snowflake; Adobe Analytics; DoubleClick Campaign Manager; DCM

## Question 8

file_name:
- _080_DSX_Walmart_Retail_Synthetic Control Matching.pptx

question:
For a retail sales prospect asking for a measurement case study, what was Walmart's synthetic-control use case and key impact?

answer:
Use case: incrementality measurement through app downloads. Impact #1: developed the analysis for ~15MM downloads per year and estimated incremental lift of 38% in revenue through app downloads. Impact #2: identified high-value media sources to advise future annual media spend strategy.

answer_source:
- _080_DSX_Walmart_Retail_Synthetic Control Matching.pptx, slide 1 and slide 2

question_type:
sales proof point / summary / outcome

match_keywords:
incrementality measurement; app downloads; 15MM downloads; 38%; revenue lift; high-value media sources; annual media spend strategy

## Question 9

file_name:
- Agentic_Data_Platform_Strategic_Positioning.docx

question:
For a sales rep positioning the Agentic Data Platform, what are the three integrated layers of the proposed solution?

answer:
AI-Ready Data Foundation, Autonomous Data Operations, and Agentic Analytics.

answer_source:
- Agentic_Data_Platform_Strategic_Positioning.docx, paragraphs 47-68

question_type:
sales positioning / factual / retrieval

match_keywords:
AI-Ready Data Foundation; Autonomous Data Operations; Agentic Analytics

## Question 10

file_name:
- Agentic_Knowledge_Platform_Offering.docx

question:
For a sales rep explaining the Agentic Knowledge Platform, what does the platform unify into an AI-ready foundation?

answer:
Enterprise knowledge.

answer_source:
- Agentic_Knowledge_Platform_Offering.docx, table 1 rows 3, 5, and 6

question_type:
sales positioning / factual / retrieval

match_keywords:
enterprise knowledge; AI-ready foundation; unified knowledge

## Question 11

file_name:
- AI_Native_Data_Foundation_Offering_Development_Roadmap.xlsx

question:
For sales enablement planning, what are the key deliverables for the AI-Native Data Foundation roadmap's Best Solution Deliverables workstream?

answer:
HLD/LLD templates, vertical starter kits, and a sample project plan.

answer_source:
- AI_Native_Data_Foundation_Offering_Development_Roadmap.xlsx, sheet "GTM Content Roadmap", summary row for Best Solution Deliverables

question_type:
sales enablement / roadmap retrieval

match_keywords:
HLD; LLD; templates; vertical starter kits; sample project plan

## Question 12

file_name:
- AI-Powered Intent Search Revolutionizes Hotel Bookings.pptx

question:
For a hospitality sales prospect interested in AI-powered booking search, what were the main quantified impacts from the hotel intent-search case study?

answer:
10ms mean response time, 90% improvement, 50% compute cost reduction, $85k-$150k annual savings, and $20-$50M projected first-year revenue.

answer_source:
- AI-Powered Intent Search Revolutionizes Hotel Bookings.pptx, slide 1

question_type:
sales proof point / quantified outcome / summary

match_keywords:
10ms; 90%; 50%; $85k; $150k; $20-$50M; first year revenue

## Question 13

file_name:
- AI-Powered Intent Search Revolutionizes Hotel Bookings.pptx

question:
Which case study should a sales rep use for a hotel prospect that wants natural-language search, personalized property recommendations, and faster booking conversion?

answer:
AI-Powered Intent Search Revolutionizes Hotel Bookings.

answer_source:
- AI-Powered Intent Search Revolutionizes Hotel Bookings.pptx, slide 1

question_type:
sales retrieval / case-study recommendation

match_keywords:
AI-Powered Intent Search; Hotel Bookings; natural language search; personalized recommendations; booking conversion

## Question 14

file_name:
- Agentic_Data_Platform_Strategic_Positioning.docx

question:
For an enterprise AI sales pitch, what 12-month outcome does the Agentic Data Platform claim for time to productionize AI use cases?

answer:
6-12 months reduced to 6-12 weeks, described as 10x faster.

answer_source:
- Agentic_Data_Platform_Strategic_Positioning.docx, paragraph 77

question_type:
sales proof point / quantified outcome

match_keywords:
6-12 months; 6-12 weeks; 10x faster; productionize AI use case

## Question 15

file_name:
- AI_Native_Data_Foundation_Offering.docx

question:
For AI-Native Data Foundation sales qualification, which target client types are listed?

answer:
Global Retail, Banking & Financial Services, Manufacturing, Tech/SaaS, and Large Enterprises.

answer_source:
- AI_Native_Data_Foundation_Offering.docx, table 1 row 7

question_type:
sales qualification / factual retrieval

match_keywords:
Global Retail; Banking; Financial Services; Manufacturing; Tech/SaaS; Large Enterprises

## Question 16

file_name:
- AI_Native_Data_Foundation_Offering.docx

question:
For a sales rep positioning the AI-Native Data Foundation, what technology stack is listed in the offering?

answer:
Snowflake, AWS, Databricks, and dbt Cloud.

answer_source:
- AI_Native_Data_Foundation_Offering.docx, table 1 row 9

question_type:
sales discovery / factual retrieval

match_keywords:
Snowflake; AWS; Databricks; dbt Cloud

## Question 17

file_name:
- AI and DS Joint Function Meeting - 07-17-2026.pptx

question:
For a sales rep explaining the Vialto delivery story, what business problem was Blend addressing?

answer:
Manual, fragmented, document-heavy tax and immigration casework that raised cost-to-serve.

answer_source:
- AI and DS Joint Function Meeting - 07-17-2026.pptx, slide 20

question_type:
sales discovery / factual retrieval

match_keywords:
manual; fragmented; document-heavy; tax; immigration; cost-to-serve

## Question 18

file_name:
- AI and DS Joint Function Meeting - 07-17-2026.pptx

question:
For Vialto, what productivity coverage improvement did the move from Vanguard to Vlabs claim for UK Tax?

answer:
Coverage increased from 20% to 100% in weeks.

answer_source:
- AI and DS Joint Function Meeting - 07-17-2026.pptx, slide 21

question_type:
sales proof point / quantified outcome

match_keywords:
20%; 100%; weeks; UK Tax; coverage increase

## Question 19

file_name:
- AI and DS Joint Function Meeting - 07-17-2026.pptx

question:
In the Vialto evals delivery story, what four questions does every Plugin Enhancement Framework verdict answer?

answer:
Efficiency, integrity, correctness, and quality.

answer_source:
- AI and DS Joint Function Meeting - 07-17-2026.pptx, slide 25

question_type:
sales positioning / factual retrieval

match_keywords:
efficiency; integrity; correctness; quality

## Question 20

file_name:
- PM_Copilot_Deck.pptx

question:
For a Franklin Templeton sales proof point, what information-overload problem did PM Copilot address?

answer:
600+ daily articles across 200+ portfolio companies, with 85% noise.

answer_source:
- PM_Copilot_Deck.pptx, slide 2

question_type:
sales discovery / quantified factual

match_keywords:
600+ daily articles; 200+ portfolio companies; 85% noise

## Question 21

file_name:
- PM_Copilot_Deck.pptx

question:
For Franklin Templeton PM Copilot, how many specialized AI agents transform raw data into investment signals?

answer:
6 specialized AI agents.

answer_source:
- PM_Copilot_Deck.pptx, slide 3 and slide 4

question_type:
sales positioning / factual retrieval

match_keywords:
6 specialized agents; investment signals; PM Copilot

## Question 22

file_name:
- PM_Copilot_Deck.pptx

question:
For a Franklin Templeton sales proof point, what did context engineering improve in PM Copilot?

answer:
Reduced context from 50K to 5K tokens, reduced cost per recommendation from $0.50-$0.80 to $0.05-$0.10, improved PM satisfaction from 70-75% to 85-90%, and reduced processing from 12-14 minutes to 4-6 minutes.

answer_source:
- PM_Copilot_Deck.pptx, slide 8

question_type:
sales proof point / quantified outcome

match_keywords:
50K; 5K; $0.50-$0.80; $0.05-$0.10; 70-75%; 85-90%; 12-14 min; 4-6 min
