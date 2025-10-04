# `scout_agent.py` - The Talent Scout Agent

## Overview

This file contains the core logic for the `TalentScoutAgent`, a crucial component of the multi-agent HR automation system. This agent is responsible for the initial stages of the recruitment pipeline: resume screening and candidate evaluation. It automates the tedious process of sifting through numerous resumes to identify the most promising candidates for a given job role.

## Key Responsibilities

1.  **Resume Parsing and Canonicalization**: The agent takes a list of resumes (in PDF or raw text format) and parses them into a standardized JSON format. This structured data includes key information such as the candidate's name, contact details, skills, years of experience, seniority level, and educational background.

2.  **Match Score Computation**: It evaluates each parsed resume against the provided job brief. The agent calculates both a relative match score (how a candidate compares to others) and an absolute score (how well a candidate meets the specific job requirements).

3.  **Candidate Shortlisting and Rationale Generation**: Based on the match scores and other constraints like diversity targets, the agent generates a shortlist of the top candidates. For each shortlisted candidate, it provides a concise rationale explaining why they are a good fit for the role.

4.  **Interview Question Generation**: To assist the hiring manager in the subsequent interview stages, the agent also generates a set of recommended interview questions tailored to each top candidate's profile and the job requirements.

## How It Works

The `TalentScoutAgent` utilizes a connection to a Large Language Model (LLM) via the `llm_connector.py` utility. It uses carefully crafted prompts (defined in `prompts.py`) to instruct the LLM on how to perform the tasks of parsing, scoring, and generating explanations.

The main method, `screen_resumes`, orchestrates the entire process. It iterates through each resume, calls the LLM for analysis, and then compiles the results into a structured output. This output can then be passed to the `Orchestrator` agent for the next steps in the hiring workflow.

## Dependencies

-   `google.generativeai`: The library for interacting with the Gemini API.
-   `core.utils.llm_connector`: A custom module to handle the connection and API calls to the Gemini model.
-   `agents.talent_scout.prompts`: A module containing the specific prompts used by this agent.
-   `core.utils.file_parser`: A utility to extract text from resume files (e.g., PDFs).
-   `config`: A configuration file to store the Gemini API key and other settings.

## Usage

The `TalentScoutAgent` is typically instantiated and called by the `Orchestrator` agent. An example of how to use it is provided in `main.py` and its functionality is tested in `tests/test_talent_scout.py`.