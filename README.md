# Course Registration Service

This is a small Python service that handles enrolling in a course, dropping it, checking prerequisites, and moving people off a waitlist in first-come, first-served order. It covers one course offering at a time. No starter project came with the assessment, so I built it as an in-memory service, which the assessment allows in that case.

## Requirements

- Python 3.10 or newer
- `pytest` (listed in `requirements.txt`)

## Setup and running the tests

Run everything from the project folder (the one that contains `requirements.txt`).

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Install the dependencies and run the tests:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

## Quick example

```python
from course_registration import CourseRegistrationService, Learner, Offering

offering = Offering(
    offering_id="COURSE-101",
    capacity=1,
    required_prerequisites={"INTRO"},
)
learners = [
    Learner("A", {"INTRO"}),
    Learner("B", {"INTRO"}),
]
service = CourseRegistrationService(offering, learners)

print(service.enroll("A"))    # A gets the only seat
print(service.enroll("B"))    # B goes on the waitlist
print(service.drop("A"))      # A leaves, B is promoted
print(service.snapshot())
```

## What is in the project

- `DESIGN.md` explains the data model, the rules I chose, and how concurrency is handled.
- `AI_USAGE.md` records where I used an AI assistant and how I checked its work.
- `LIMITATIONS.md` lists what the service does not do and where it would need work for real use.
- `TEST_RESULTS.txt` has the output of a recorded test run.

## What I left out

I kept the scope small on purpose. There is no frontend, database, course catalog, payment handling, login or identity integration, deployment setup, or configurable policy system.
