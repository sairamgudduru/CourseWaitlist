# AI Usage and Development Approach

## 1. How I approached the problem

I started by reviewing the assessment requirements and identifying the
core problem: managing course enrollment when an offering has limited
capacity, while maintaining a fair waitlist when the course is full.

I broke the requirements into the main workflows:

-   Enroll a learner when a seat is available.
-   Add an eligible learner to the waitlist when the offering is full.
-   Prevent duplicate enrollment and duplicate waitlist entries.
-   Check learner eligibility and prerequisites.
-   Handle drops and make newly available seats available to the next
    eligible learner.
-   Preserve waitlist order during promotion.
-   Handle invalid requests and repeated operations safely.

I used AI to discuss the requirements, identify possible edge cases, and
explore a simple design that met the assessment scope. I kept the
solution focused on the requested course-registration workflow rather
than adding unrelated features.

## 2. Information gathering and design

I used AI as a discussion and review partner while translating the
assessment requirements into implementation rules. I asked it to clarify
expected behavior, identify less-obvious scenarios, and compare possible
approaches for maintaining FIFO waitlist order.

The discussions covered cases such as duplicate requests, a full
offering, an ineligible learner at the front of the waitlist, and
repeated drop requests. I also used AI to help identify assumptions that
needed to be documented.

One design decision was how to handle a waitlisted learner who is not
eligible when a seat becomes available. The implemented policy is to
skip that learner for the current promotion attempt while retaining the
learner in the waitlist. This avoids losing their place solely because
they are temporarily ineligible.

I reviewed the suggested approaches against the assessment requirements
and selected the behavior and design that best fit the problem.

## 3. Python implementation and code review

I used AI iteratively as a development assistant while working through
the Python service and its supporting logic. I used it to discuss the
behavior of individual operations, review the implementation, and look
for missing conditions or edge cases.

The review focused on whether:

-   Enrollment checks capacity and eligibility before changing the
    offering.
-   Duplicate enrollment and waitlist requests are handled consistently.
-   A drop only succeeds when the learner is currently enrolled.
-   A newly available seat is offered to the earliest eligible
    waitlisted learner.
-   Waitlist processing preserves FIFO order.
-   Rejected operations leave the service state consistent.
-   The implementation remains understandable and appropriately scoped.

I asked AI to inspect the main Python implementation for potential
defects and gaps. I evaluated the feedback against the documented
requirements rather than accepting every suggestion automatically.

## 4. Test design and validation

I used AI to help translate the business rules into test scenarios and
review whether the test script covered normal and exceptional behavior.

The test scenarios included:

-   Successful enrollment when seats are available.
-   Enrollment when the offering is full.
-   Waitlist ordering and FIFO promotion.
-   Eligibility and prerequisite failures.
-   Duplicate enrollment and duplicate waitlist requests.
-   Successful and unsuccessful drop operations.
-   Promotion when the next learner is eligible.
-   Skipping an ineligible learner while retaining their waitlist entry.
-   Invalid inputs and repeated operations.
-   State consistency after rejected operations.

I asked AI to review the tests against the acceptance criteria and
suggest additional cases that could expose gaps. I then used the test
suite to validate the service behavior and reviewed failures or
unexpected results instead of relying only on whether the code executed.

## 5. Rigorous testing

I specifically asked AI to help conduct a rigorous review of the
implementation and test suite, including checking edge cases and looking
for gaps between the requirements and the code.

For the reviewed project version, the recorded test run reported:

-   **26 tests passed**
-   **100% statement coverage**
-   **112 statements**
-   **0 missed statements**

These results are recorded in `TEST_RESULTS.txt`. They apply to the
reviewed project version; running the tests in another environment or
after changing the code may produce different results.

Passing tests and coverage are useful evidence, but they do not prove
that every possible defect has been eliminated. I treated them as
validation of the scenarios covered by the test suite, together with the
design and code review.

## 6. Design decisions and scope

The implementation uses an in-memory service because the assessment
focuses on registration and waitlist behavior rather than persistence or
deployment.

The main design decisions include:

-   Keeping the solution small and focused on one course offering.
-   Separating service logic from tests.
-   Maintaining FIFO ordering for waitlist promotion.
-   Skipping currently ineligible waitlisted learners without removing
    them from the waitlist.
-   Using a lock to protect operations within a single running process.

The in-memory approach means data is not retained after the application
stops. The lock does not provide coordination across multiple
application processes or machines. These limitations are documented in
`LIMITATIONS.md`.

## 7. Responsible use of AI

AI supported the development process by helping me reason through
requirements, explore design options, review implementation logic,
identify edge cases, strengthen the test suite, and interpret validation
results.

I treated AI output as suggestions rather than as authoritative answers.
I reviewed the suggestions against the assessment requirements,
considered the trade-offs, and retained the approaches that were
appropriate for the scope and expected behavior of the application.

The final implementation, assumptions, design choices, limitations, and
test evidence are documented in the project so the approach can be
reviewed and discussed independently of the AI-assisted development
process.

## 8. Project files

-   `course_registration/` --- Python implementation of the
    course-registration service.
-   `tests/` --- Automated tests for the service behavior.
-   `README.md` --- Setup instructions and an overview of how to run the
    project.
-   `DESIGN.md` --- Design decisions, rules, and workflow details.
-   `LIMITATIONS.md` --- Known limitations and scope boundaries.
-   `TEST_RESULTS.txt` --- Recorded test results for the reviewed
    project version.

------------------------------------------------------------------------

**Summary:** I used AI as a development assistant throughout the
assessment to help interpret requirements, explore design options,
review the Python implementation, identify edge cases, and strengthen
the test suite. I evaluated the suggestions and used the assessment
requirements and recorded test results to guide the final solution.
