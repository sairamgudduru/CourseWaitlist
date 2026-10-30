# AI Usage Record

I used an AI assistant while working on this task. This document lists what I asked it, what it produced, and what I decided to keep. I reviewed the code, tests and documents myself before submitting.

## What I asked and what came back

| What I asked | What the AI did | What I did with it |
|---|---|---|
| Read the company assessment PDF and break down the task | Summarised the feature (enroll, drop, first-come waitlist) and listed what had to be delivered: code, tests, a design document, an AI-use record, run instructions and limitations | Used it as my starting checklist and compared it with the PDF |
| Told it that only the PDF was supplied and asked it to build the project | Drafted a small in-memory Python service, a pytest suite and the supporting documents, using the fallback the assessment allows | Kept the small design. I did not add a frontend or database |
| Asked whether everything was implemented and for a thorough re-check | Found that the first 10 tests missed constructor validation and several edge cases, then tightened the validation, added tests and clarified the policy notes | Accepted the changes after reading them |
| Asked it to check correctness and the documentation | Ran the suite with coverage, including invariant checks, queue policy, invalid input and concurrent calls | Recorded the result below |

## Suggestions I accepted

| Suggestion | Decision | Reason and how I checked |
|---|---|---|
| Use an in-memory service since there was no starter project | Accepted | The assessment explicitly allows it |
| Return explicit statuses for enroll and drop outcomes | Accepted | Tests cover success, duplicate, missing prerequisite, unknown learner and invalid drop |
| Use a lock around state-changing operations | Accepted | Concurrency tests check capacity and uniqueness under simultaneous requests. The lock only works within one process, and the design notes say so |
| Skip ineligible waitlisted learners but keep their order | Accepted as my policy choice | Tests cover skipping, keeping the order, and a learner becoming eligible later |
| Validate the starting state and learner registry | Added during review | Tests cover bad capacity values, duplicate or overlapping IDs, missing learner references and duplicate learner definitions |
| Leave out frontend, database and outside integrations | Accepted | Keeps the work within what was asked |

## Test evidence

Recorded run: Python 3.13.5.

```bash
python -m pytest -q --cov=course_registration --cov-report=term-missing
```

Result: 26 tests passed, with 100% statement coverage of `course_registration` (112 statements, none missed).

Full coverage only shows that every line ran during the tests. It does not prove the code has no bugs.

The environment that produced the recorded run printed an unrelated warning from its own tooling at startup. It did not come from this project and the tests still passed.

## Files covered

- `course_registration/service.py`
- `tests/test_service.py`
- `README.md`
- `DESIGN.md`
- `LIMITATIONS.md`
- `TEST_RESULTS.txt`

## Points I can explain in a review

- Why capacity is checked while the lock is held.
- Why a learner has to be eligible before being enrolled or waitlisted.
- Why promotion skips ineligible learners instead of removing them.
- Which invariants each test checks.
- Why 100% coverage does not mean the code is free of bugs.
- What would need to change to use a database and run several application processes.
