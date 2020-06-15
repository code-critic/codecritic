#!/bin/python3
# author: Jan Hybs

from typing import Optional, List
import pathlib
from dataclasses import dataclass, field, asdict
from utils.crypto import sha1
from loguru import logger

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
    id: str = None
    status: str = None
    duration: float = None
    returncode: int = None
    message: Optional[str] = None

    score: Optional[int] = None
    scores: Optional[List[int]] = None
    cmd: Optional[str] = None
    uuid: Optional[str] = None

    console: Optional[Text] = field(default_factory=list)
    message_details: Optional[Text] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)

    def __post_init__(self):
        if self.id and not self.uuid:
            self.uuid = sha1(self.id)


@dataclass
class TestResult(ICrate):
    user: str
    course: str
    problem: str
    action: str = None
    docker: bool = None
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
    time: any = None
    active: any = None
    points: float = 0.0

    def __post_init__(self):
        if self._id and not self.time:
            try:
                import datetime
                self.time = datetime.datetime.timestamp(self._id.generation_time)
            except:
                self.time = 0

        try:
            if self.results:
                for i, x in enumerate(self.results):
                    if isinstance(x, dict):
                        self.results[i] = CaseResult(**x)
        except Exception as e:
            logger.exception("Error wile converting dict to CaseResult")

    @property
    def firstname(self):
        try:
            return str(self.user.split('.')[0]).capitalize()
        except:
            return self.user

    @property
    def lastname(self):
        try:
            return str(self.user.split('.')[-1]).capitalize()
        except:
            return self.user

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
