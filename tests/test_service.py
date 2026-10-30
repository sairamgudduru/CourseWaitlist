import threading

import pytest

from course_registration import CourseRegistrationService, Learner, Offering, Status


def learner(learner_id, *completed):
    return Learner(learner_id, frozenset(completed))


def make_service(capacity=2, required=None, learners=None):
    return CourseRegistrationService(
        Offering("COURSE-101", capacity, set(required or [])),
        learners or [],
    )


def assert_invariants(service):
    state = service.snapshot()
    assert 0 <= len(state["enrolled"]) <= state["capacity"]
    assert len(state["enrolled"]) == len(set(state["enrolled"]))
    assert len(state["waitlist"]) == len(set(state["waitlist"]))
    assert set(state["enrolled"]).isdisjoint(state["waitlist"])
    assert state["available_seats"] == state["capacity"] - len(state["enrolled"])


def test_enrolls_when_capacity_is_available():
    service = make_service(2, learners=[learner("A"), learner("B")])
    assert service.enroll("A").status == Status.ENROLLED
    assert service.snapshot()["enrolled"] == ["A"]
    assert service.snapshot()["available_seats"] == 1
    assert_invariants(service)


def test_eligible_learner_joins_waitlist_when_full():
    service = make_service(1, learners=[learner("A"), learner("B")])
    service.enroll("A")
    assert service.enroll("B").status == Status.WAITLISTED
    assert service.snapshot()["waitlist"] == ["B"]
    assert_invariants(service)


def test_duplicate_enrollment_does_not_duplicate_enrolled_or_waitlist_records():
    service = make_service(1, learners=[learner("A"), learner("B")])
    service.enroll("A")
    assert service.enroll("A").status == Status.ALREADY_ENROLLED
    service.enroll("B")
    assert service.enroll("B").status == Status.ALREADY_WAITLISTED
    assert service.snapshot()["enrolled"] == ["A"]
    assert service.snapshot()["waitlist"] == ["B"]
    assert_invariants(service)


def test_drop_promotes_earliest_waitlisted_learner_fifo():
    service = make_service(1, learners=[learner("A"), learner("B"), learner("C")])
    service.enroll("A")
    service.enroll("B")
    service.enroll("C")
    result = service.drop("A")
    assert result.status == Status.DROPPED
    assert result.promoted_learner_id == "B"
    assert service.snapshot()["enrolled"] == ["B"]
    assert service.snapshot()["waitlist"] == ["C"]
    assert_invariants(service)


def test_prerequisite_failure_prevents_enrollment_and_waitlisting():
    service = make_service(1, required={"INTRO"}, learners=[learner("A")])
    before = service.snapshot()
    assert service.enroll("A").status == Status.PREREQUISITE_FAILED
    assert service.snapshot() == before
    assert_invariants(service)


def test_multiple_prerequisites_must_all_be_completed():
    service = make_service(2, required={"INTRO", "MATH"}, learners=[
        learner("A", "INTRO"), learner("B", "INTRO", "MATH")
    ])
    assert service.enroll("A").status == Status.PREREQUISITE_FAILED
    assert service.enroll("B").status == Status.ENROLLED
    assert service.snapshot()["enrolled"] == ["B"]


def test_ineligible_waitlisted_learner_is_skipped_and_retained():
    service = make_service(
        1, required={"INTRO"},
        learners=[learner("A", "INTRO"), learner("B", "INTRO"), learner("C", "INTRO")]
    )
    service.enroll("A")
    service.enroll("B")
    service.enroll("C")
    service.add_learner(learner("B"))  # Eligibility changes after joining the queue.
    result = service.drop("A")
    assert result.promoted_learner_id == "C"
    assert service.snapshot()["enrolled"] == ["C"]
    assert service.snapshot()["waitlist"] == ["B"]
    assert_invariants(service)


def test_ineligible_waitlisted_learner_can_be_promoted_after_becoming_eligible():
    service = make_service(
        1, required={"INTRO"},
        learners=[learner("A", "INTRO"), learner("B", "INTRO")]
    )
    service.enroll("A")
    service.enroll("B")
    service.add_learner(learner("B"))
    result = service.drop("A")
    assert result.promoted_learner_id is None
    assert service.snapshot()["enrolled"] == []
    assert service.snapshot()["waitlist"] == ["B"]
    service.add_learner(learner("B", "INTRO"))
    service.enroll("A")
    result = service.drop("A")
    assert result.promoted_learner_id == "B"
    assert service.snapshot()["enrolled"] == ["B"]
    assert service.snapshot()["waitlist"] == []


def test_drop_without_waitlist_leaves_one_seat_open():
    service = make_service(2, learners=[learner("A")])
    service.enroll("A")
    result = service.drop("A")
    assert result.status == Status.DROPPED
    assert result.promoted_learner_id is None
    assert service.snapshot()["enrolled"] == []
    assert service.snapshot()["available_seats"] == 2
    assert_invariants(service)


def test_invalid_and_repeated_drops_do_not_change_state():
    service = make_service(1, learners=[learner("A"), learner("B")])
    before = service.snapshot()
    assert service.drop("A").status == Status.NOT_ENROLLED
    assert service.snapshot() == before
    service.enroll("A")
    service.drop("A")
    after = service.snapshot()
    assert service.drop("A").status == Status.NOT_ENROLLED
    assert service.snapshot() == after
    assert_invariants(service)


def test_unknown_and_empty_learner_ids_are_rejected_without_mutation():
    service = make_service(1, learners=[learner("A")])
    before = service.snapshot()
    assert service.enroll("missing").status == Status.UNKNOWN_LEARNER
    assert service.enroll("").status == Status.UNKNOWN_LEARNER
    assert service.enroll("   ").status == Status.UNKNOWN_LEARNER
    assert service.snapshot() == before


def test_zero_capacity_places_eligible_learner_on_waitlist():
    service = make_service(0, learners=[learner("A")])
    assert service.enroll("A").status == Status.WAITLISTED
    assert service.snapshot()["available_seats"] == 0
    assert_invariants(service)


def test_dropped_learner_can_request_enrollment_again():
    service = make_service(1, learners=[learner("A")])
    assert service.enroll("A").status == Status.ENROLLED
    assert service.drop("A").status == Status.DROPPED
    assert service.enroll("A").status == Status.ENROLLED
    assert service.snapshot()["enrolled"] == ["A"]
    assert_invariants(service)


def test_duplicate_drop_does_not_promote_waitlist_twice():
    service = make_service(1, learners=[learner("A"), learner("B"), learner("C")])
    service.enroll("A")
    service.enroll("B")
    service.enroll("C")
    assert service.drop("A").promoted_learner_id == "B"
    after_first_drop = service.snapshot()
    assert service.drop("A").status == Status.NOT_ENROLLED
    assert service.snapshot() == after_first_drop
    assert_invariants(service)


def test_constructor_rejects_negative_or_non_integer_capacity():
    for capacity in (-1, 1.5, True):
        with pytest.raises(ValueError):
            make_service(capacity)


def test_constructor_rejects_duplicate_or_overlapping_initial_state():
    learners = [learner("A"), learner("B")]
    with pytest.raises(ValueError):
        CourseRegistrationService(Offering("C", 2, enrolled=["A", "A"]), learners)
    with pytest.raises(ValueError):
        CourseRegistrationService(Offering("C", 2, enrolled=["A"], waitlist=["A"]), learners)
    with pytest.raises(ValueError):
        CourseRegistrationService(Offering("C", 0, enrolled=["A"]), learners)


def test_constructor_rejects_roster_ids_missing_from_learner_registry():
    with pytest.raises(ValueError, match="unknown learner"):
        CourseRegistrationService(Offering("C", 1, enrolled=["missing"]), [])


def test_constructor_rejects_duplicate_learner_definitions():
    with pytest.raises(ValueError, match="Duplicate learner ID"):
        make_service(1, learners=[learner("A"), learner("A")])


def test_input_mutations_do_not_change_copied_initial_state():
    enrolled = []
    waitlist = []
    prerequisites = {"INTRO"}
    offering = Offering("C", 1, prerequisites, enrolled, waitlist)
    learners = [learner("A", "INTRO")]
    service = CourseRegistrationService(offering, learners)
    prerequisites.add("MATH")
    enrolled.append("unknown")
    waitlist.append("unknown")
    assert service.snapshot()["enrolled"] == []
    assert service.snapshot()["waitlist"] == []
    assert service.enroll("A").status == Status.ENROLLED


def test_concurrent_distinct_enrollments_never_exceed_capacity():
    learners = [learner(f"L{i}") for i in range(20)]
    service = make_service(5, learners=learners)
    barrier = threading.Barrier(len(learners))

    def enroll_one(learner_id):
        barrier.wait()
        service.enroll(learner_id)

    threads = [threading.Thread(target=enroll_one, args=(item.learner_id,)) for item in learners]
    for thread in threads:
        thread.start()
    for thread in threads:
            thread.join()

    state = service.snapshot()
    assert len(state["enrolled"]) == 5
    assert len(state["waitlist"]) == 15
    assert_invariants(service)


def test_concurrent_duplicate_requests_create_only_one_active_record():
    service = make_service(1, learners=[learner("A")])
    barrier = threading.Barrier(12)

    def enroll_same():
        barrier.wait()
        service.enroll("A")

    threads = [threading.Thread(target=enroll_same) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert service.snapshot()["enrolled"] == ["A"]
    assert service.snapshot()["waitlist"] == []
    assert_invariants(service)


def test_learner_rejects_empty_identifier():
    with pytest.raises(ValueError, match="Learner ID"):
        Learner(" ")


def test_constructor_rejects_empty_offering_id():
    with pytest.raises(ValueError, match="Offering ID"):
        CourseRegistrationService(Offering(" ", 1), [])


def test_constructor_rejects_non_learner_entries():
    with pytest.raises(TypeError, match="Learner instances"):
        CourseRegistrationService(Offering("C", 1), [object()])


def test_constructor_rejects_duplicate_waitlist_ids():
    with pytest.raises(ValueError, match="duplicate waitlist"):
        CourseRegistrationService(
            Offering("C", 1, waitlist=["A", "A"]),
            [learner("A")],
        )


def test_add_learner_rejects_non_learner_object():
    service = make_service(1, learners=[learner("A")])
    with pytest.raises(TypeError, match="Learner instance"):
        service.add_learner(object())
