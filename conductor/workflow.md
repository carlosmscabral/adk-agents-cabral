# Project Workflow

This document defines the standard development workflow and protocols for the project.

## Testing Requirements
- **Coverage Target:** 80% test coverage.
- **Demo-Oriented Approach:** To ensure rapid development for these demo agents, avoid heavy, rigorous unit testing overhead. Prefer lightweight programmatic scripts (e.g., `run_agent.py`) or basic integration checks that validate core agent behavior without delaying progress.

## Commit Protocol
- **Frequency:** Commits should be made **Per Phase** (i.e., upon the completion of all tasks in a single phase of the implementation plan).
- **Task Summaries:** Task summaries and metadata must be recorded using **Git Notes** attached to the commit, rather than in the commit message body.

## Phase Completion Verification and Checkpointing Protocol
- Run the provided tests or programmatic scripts to ensure the agent functions properly.
- Ensure all relevant documentation and comments are updated per the Product Guidelines.
- Perform the Phase commit.

## Track Finalization Protocol
- When an agent/track is finalized or archived, you must update the table in the root `README.md` to document the new agent, providing a link and a brief explanation of what the agent does.
