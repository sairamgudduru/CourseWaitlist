# Limitations and Follow-up Risks

- All state is in memory and disappears when the process exits.
- The lock only protects threads inside one process. Running several processes or servers would need a database with transactions and proper concurrency control.
- There is no HTTP API or command-line interface. The service is meant to be called directly from Python.
- Prerequisite data comes from the caller. There is no course catalog or transcript system behind it.
- Ineligible learners on the waitlist are skipped, not removed. A product owner might prefer to remove them or handle them another way.
- One service instance manages one offering. It is not a full registration system.
- Authentication, authorization, a lasting audit trail, notifications, persistence, deployment and integration testing are all out of scope.
- The lock cannot stop someone from changing `service.offering` or `service.learners` directly, so callers need to use the service methods. A production version should hide that state more carefully.
- `add_learner` can change what a learner has completed, but waitlisted learners are only re-checked when a seat opens. Someone who becomes eligible stays in the queue until then.
