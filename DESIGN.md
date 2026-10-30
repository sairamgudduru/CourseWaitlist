# Design Notes

## Scope

`CourseRegistrationService` looks after a single course offering. It has four public methods: `enroll(learner_id)`, `drop(learner_id)`, `add_learner(learner)` and `snapshot()`. I did not add an HTTP API, frontend, identity provider or database, since the assessment allows an in-memory service when no starter project is given.

## Data model

- `Learner` has a non-empty ID and a fixed set of completed course IDs.
- `Offering` has an ID, a capacity (zero or more), the prerequisite course IDs, an ordered list of enrolled learners and an ordered waitlist.
- `OperationResult` has a status, a readable message and, when someone was promoted, that learner's ID.

## Rules I decided on

The assessment leaves some behaviour open, so these are the choices I made:

1. A learner can enroll only if they have completed every prerequisite for the offering.
2. A learner can be in the enrolled list or on the waitlist, never both, and never twice in the same list.
3. A duplicate enrollment request gets its own result status and changes nothing.
4. A learner who fails the prerequisite check is rejected straight away. They are not added to the waitlist.
5. When a seat opens, the waitlist is checked from oldest to newest and the first learner who is currently eligible gets the seat.
6. Waitlisted learners who are not eligible are skipped for that promotion but keep their place in the queue. They are checked again the next time a seat opens. I chose this because the assessment asks the candidate to state a policy here instead of giving one.
7. A learner who dropped can enroll again later. The uniqueness rule applies to current state only, not history.
8. Unknown learner IDs are rejected. Dropping someone who is not enrolled returns `NOT_ENROLLED`.
9. Each service instance covers one offering. Any learners already enrolled or waitlisted at the start must be registered learners.
10. The starting state is validated: capacity must be valid, there can be no duplicate IDs, and nobody can be in both the enrolled list and the waitlist.

## Invariants

These should hold after every operation:

- The number of enrolled learners is between 0 and the capacity.
- IDs in the enrolled list are unique, and so are IDs in the waitlist.
- The enrolled list and the waitlist never share an ID.
- An invalid request leaves the state unchanged.
- A drop promotes at most one learner. If someone is promoted, the enrolled count stays the same. If nobody is, it goes down by one.
- Promotion picks the first eligible learner in waitlist order, and anyone skipped keeps their relative position.
- `snapshot()` returns copies of the lists, so changing the result does not change the service.

## Concurrency and persistence

A re-entrant lock wraps each operation and each snapshot, so calls from multiple threads in one Python process are handled one at a time. The tests cover several threads enrolling different learners and several threads sending the same request.

This does not work across processes or machines. A real deployment would need a database with transactions and row locking, or some other atomic approach. Also, everything is held in memory and is lost when the process stops.

## Tradeoffs

I aimed for something short and easy to read, with explicit result statuses instead of exceptions for normal outcomes. The cost is that there is no persistence, no HTTP layer, no authentication, no audit history, no notifications and no support for several offerings.
