#!/bin/python3
# author: Jan Hybs

from typing import Optional, List
import pathlib
from dataclasses import dataclass, field, asdict


Text = List[str]


@dataclass
class ICrate:
    def peek(self, full=True):
        return asdict(self)


@dataclass
class Attachment(ICrate):
    name: str
    path: pathlib.Path


@dataclass
class CaseResult(ICrate):
    id: str
    status: str
    duration: float
    returncode: int
    message: str

    score: Optional[int] = None
    scores: Optional[List[int]] = None
    cmd: Optional[str] = None
    uuid: Optional[str] = None

    console: Optional[Text] = field(default_factory=list)
    message_details: Optional[Text] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)


@dataclass
class TestResult(ICrate):
    action: str
    user: str
    course: str
    problem: str
    docker: bool
    result: Optional[CaseResult] = None
    results: List[CaseResult] = field(default_factory=list)

    _id: Optional[str] = None
    uuid: Optional[str] = None
    lang: Optional[str] = None
    solution: Optional[str] = None
    output_dir: Optional[str] = None
    attempt: Optional[int] = None
    review: Optional[dict] = None
    review_request: Optional[dict] = None

    compilation: any = None

    @property
    def ref_course(self):
        """
        :rtype: database.objects.Course
        """
        from database.objects import Courses
        return Courses()[self.course]

    @property
    def ref_problem(self):
        """
        :rtype: database.objects.Problem
        """
        return self.ref_course.problem_db[self.problem]


@dataclass
class Comment(ICrate):
    pass


@dataclass
class ActionResult(ICrate):
    pass
