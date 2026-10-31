# Auralis Hackathon Judge Notes

**Team:** Synergy  
**Lead:** Pushkkal Gupta  
**Submission:** Open-weight AI interview intelligence (GPT-OSS-20B via Groq)

## Problem
Static mock interview questions do not test the candidate's actual CV claims, job-specific skills or project engineering explanations. Opaque AI-generated scores provide little evidence.

## Solution
Auralis combines CV/job analysis, adaptive voice interviews, CodeProof Python source references, traceable question decisions, and report evidence. Candidates practice real engineering reasoning and receive specific next steps.

## What is original
1. CodeProof reads bounded Python ZIPs and identifies actual file/function/line excerpts without executing code.
2. Interview X-Ray links model questions to job competencies, answers and any valid source references.
3. Auralis's original state engine enforces session invariants, evidence validation, branch constraints, retry comparison and a consistent rubric.
4. A reusable standards-compliant Agent Skill guides candidate-grounded interview behavior.
5. Incident Room offers repeatable synthetic scenarios.

## How the open-weight model matters
The Groq-served GPT-OSS-20B model maps CV/job evidence into the plan, generates spoken interview questions and dynamic follow-ups, and assesses recorded answers. Removing the model removes the dynamic reasoning; the scripted demo is a separate clearly labeled mode with no scored evaluations.

## Working demonstration
Use included `examples/auralis_codeproof_demo.zip`, synthetic CV and Backend JD. Connect Groq live credentials. Show the method `reserve_slot`, ask a real model-generated concurrency question, answer verbally, open Interview X-Ray, and finish with Skill DNA. If a model answer is wrong, acknowledge it and show trace instead of pretending it is verified.

## Submission hygiene
Open-source source code under MIT; no actual `.env`, .data database, private candidate resumes or secrets. README, LICENSE, tests, architecture, Agent Skill, and third-party notices included. Before submitting, test one real Groq interview and your microphone on the presentation machine. Push source to a public GitHub repository under Team Synergy's account.
