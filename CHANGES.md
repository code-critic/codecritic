# Update 1.0.1

## Core
  - [feat] Notifications are now available, when commention on code
    or when requesting code review, user will see a notification icon.
  - [fix] various UI bugs.
  - [fix] submitting solution on page which was left opened for a while.
    did not produce any output.
  - [fix] vairous engine bugs, mainly statuses.
  - [feat] - speed up docker containerization.
  - [security] - use ssl when reconnecting from Shibboleth.
  - [ci] added travis continuous integration.
  - [ci] added simple integration tests.
  - [ci] added code coverage.


## Students
  - [feat] there is now option to mark code for review
    and notify teacher(s).
  - [feat] adding comments on submitted code is now available.
  - [feat] see previously submitted solutions.

## Teachers
  - [feat] code review is available, a simple way to provide
    feedback to the student.
  - [feat] browse result, extensive search options now allow
  - teachers to browse results from the students.
  - [feat] file browser was added, no need to SSH to the server anymore.
  - [feat] courses via user defined repository. When managing a course,
    no need to directly update code of the entire repository, teachers
    can now use custom repository, which is registred as submodule
    to the main repository.