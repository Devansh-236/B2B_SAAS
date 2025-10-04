# `prompts.py` - Prompts for the Talent Scout Agent

## Overview

This file centralizes all the prompt templates used by the `TalentScoutAgent`. By separating the prompts from the agent's logic (`scout_agent.py`), we achieve a cleaner and more maintainable codebase. This separation makes it easier to experiment with and refine the prompts without altering the core application logic.

## Purpose of Prompts

Prompts are carefully constructed text inputs that guide the behavior of the Large Language Model (LLM). For the `TalentScoutAgent`, the prompts are designed to instruct the LLM to perform specific Natural Language Processing (NLP) tasks with a high degree of accuracy and to return the output in a structured, predictable format (like JSON).

## Prompts Included

1.  **`create_resume_parsing_prompt`**:
    -   **Goal**: To instruct the LLM to read the raw text of a resume and extract key information.
    -   **Output Format**: A canonicalized JSON object containing fields like `name`, `email`, `skills`, `experience_years`, `seniority`, and `education`. This structured output is essential for the downstream tasks of scoring and comparison.

2.  **`create_scoring_prompt`**:
    -   **Goal**: To guide the LLM in evaluating a parsed resume against a given job brief.
    -   **Output Format**: A JSON object that includes an `absolute_score` (on a scale of 1-100, indicating how well the candidate meets the job requirements) and a `rationale` (a brief explanation justifying the score).

3.  **`create_interview_question_prompt`**:
    -   **Goal**: To have the LLM generate a list of relevant and insightful interview questions based on the candidate's resume and the job description.
    -   **Output Format**: A JSON object containing a list of strings, where each string is a recommended interview question. This helps in preparing the hiring manager for the interview.

## Best Practices for Prompt Engineering

-   **Be Specific and Clear**: The prompts are designed to be unambiguous to reduce the chances of the LLM misinterpreting the request.
-   **Define the Output Structure**: Each prompt explicitly asks for the output to be in a JSON format with a predefined schema. This is crucial for programmatic parsing of the LLM's response.
-   **Use Examples (Few-shot Prompting)**: While not implemented in the current version for brevity, adding examples of desired inputs and outputs within the prompt can significantly improve the accuracy and consistency of the LLM's responses.

This modular approach to prompt management allows for easy updates and A/B testing of different prompt strategies to optimize the performance of the `TalentScoutAgent`.