"""In-memory course enrollment service for one course offering."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Iterable


class Status(str, Enum):
    ENROLLED = "enrolled"
    WAITLISTED = "waitlisted"
    ALREADY_ENROLLED = "already_enrolled"
    ALREADY_WAITLISTED = "already_waitlisted"
    PREREQUISITE_FAILED = "prerequisite_failed"
    DROPPED = "dropped"
    NOT_ENROLLED = "not_enrolled"
    UNKNOWN_LEARNER = "unknown_learner"


@dataclass(frozen=True)
class Learner:
    learner_id: str
    completed_courses: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.learner_id, str) or not self.learner_id.strip():
            raise ValueError("Learner ID must be a non-empty string.")
        object.__setattr__(self, "completed_courses", frozenset(self.completed_courses))


@dataclass
class Offering:
    offering_id: str
    capacity: int
    required_prerequisites: set[str] = field(default_factory=set)
    enrolled: list[str] = field(default_factory=list)
    waitlist: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OperationResult:
    status: Status
    message: str
    promoted_learner_id: str | None = None


class CourseRegistrationService:
    """Thread-safe, in-memory registration service for a single offering.

    Waitlist policy: when a seat opens, scan in FIFO order and promote the first
    currently eligible learner. Skip (but retain) ineligible learners, preserving
    their relative queue order. Eligibility is checked again at the next promotion.
    """

    def __init__(self, offering: Offering, learners: Iterable[Learner] | None = None):
        if not isinstance(offering.offering_id, str) or not offering.offering_id.strip():
            raise ValueError("Offering ID must be a non-empty string.")
        if isinstance(offering.capacity, bool) or not isinstance(offering.capacity, int) or offering.capacity < 0:
            raise ValueError("Offering capacity must be a non-negative integer.")

        learner_list = list(learners or [])
        learner_map: dict[str, Learner] = {}
        for learner in learner_list:
            if not isinstance(learner, Learner):
                raise TypeError("learners must contain Learner instances.")
            if learner.learner_id in learner_map:
                raise ValueError(f"Duplicate learner ID: {learner.learner_id}.")
            learner_map[learner.learner_id] = learner

        enrolled = list(offering.enrolled)
        waitlist = list(offering.waitlist)
        if len(set(enrolled)) != len(enrolled):
            raise ValueError("Offering contains duplicate enrolled learner IDs.")
        if len(set(waitlist)) != len(waitlist):
            raise ValueError("Offering contains duplicate waitlist learner IDs.")
        if set(enrolled) & set(waitlist):
            raise ValueError("A learner cannot be both enrolled and waitlisted.")
        if len(enrolled) > offering.capacity:
            raise ValueError("Enrolled learners exceed offering capacity.")
        unknown_ids = (set(enrolled) | set(waitlist)) - set(learner_map)
        if unknown_ids:
            raise ValueError(f"Offering references unknown learner IDs: {sorted(unknown_ids)}.")

        # Copy mutable input collections so later edits to the caller's objects do
        # not silently alter service state.
        self.offering = Offering(
            offering_id=offering.offering_id,
            capacity=offering.capacity,
            required_prerequisites=set(offering.required_prerequisites),
            enrolled=enrolled,
            waitlist=waitlist,
        )
        self.learners = learner_map
        self._lock = RLock()

    def add_learner(self, learner: Learner) -> None:
        """Add a learner or update their completed courses (e.g. eligibility changes)."""
        if not isinstance(learner, Learner):
            raise TypeError("learner must be a Learner instance.")
        with self._lock:
            self.learners[learner.learner_id] = learner

    def _is_eligible(self, learner_id: str) -> bool:
        learner = self.learners[learner_id]
        return self.offering.required_prerequisites.issubset(learner.completed_courses)

    def _promote_next_eligible(self) -> str | None:
        for index, learner_id in enumerate(self.offering.waitlist):
            if self._is_eligible(learner_id):
                self.offering.waitlist.pop(index)
                self.offering.enrolled.append(learner_id)
                return learner_id
        return None

    def enroll(self, learner_id: str) -> OperationResult:
        with self._lock:
            if not isinstance(learner_id, str) or not learner_id.strip():
                return OperationResult(Status.UNKNOWN_LEARNER, "Learner ID must be a non-empty string.")
            if learner_id not in self.learners:
                return OperationResult(Status.UNKNOWN_LEARNER, f"Unknown learner: {learner_id}.")
            if learner_id in self.offering.enrolled:
                return OperationResult(Status.ALREADY_ENROLLED, f"{learner_id} is already enrolled.")
            if learner_id in self.offering.waitlist:
                return OperationResult(Status.ALREADY_WAITLISTED, f"{learner_id} is already on the waitlist.")
            if not self._is_eligible(learner_id):
                return OperationResult(Status.PREREQUISITE_FAILED, f"{learner_id} has not met all prerequisites.")
            if len(self.offering.enrolled) < self.offering.capacity:
                self.offering.enrolled.append(learner_id)
                return OperationResult(Status.ENROLLED, f"{learner_id} enrolled successfully.")
            self.offering.waitlist.append(learner_id)
            return OperationResult(Status.WAITLISTED, f"{learner_id} added to the waitlist.")

    def drop(self, learner_id: str) -> OperationResult:
        with self._lock:
            if not isinstance(learner_id, str) or learner_id not in self.offering.enrolled:
                return OperationResult(Status.NOT_ENROLLED, f"{learner_id} is not currently enrolled.")
            self.offering.enrolled.remove(learner_id)
            promoted = self._promote_next_eligible()
            message = f"{learner_id} dropped successfully."
            if promoted is not None:
                message += f" {promoted} was promoted from the waitlist."
            else:
                message += " No eligible learner was available for promotion."
            return OperationResult(Status.DROPPED, message, promoted_learner_id=promoted)

    def snapshot(self) -> dict:
        """Return a defensive copy of state for display and verification."""
        with self._lock:
            return {
                "offering_id": self.offering.offering_id,
                "capacity": self.offering.capacity,
                "enrolled": list(self.offering.enrolled),
                "waitlist": list(self.offering.waitlist),
                "available_seats": self.offering.capacity - len(self.offering.enrolled),
            }
