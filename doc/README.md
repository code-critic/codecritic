# Code-Critic docs

## Terminology
  - **course**
    - A course can be think of as a single **subject**.
      Subjects can be divided into years so are courses.
      Each course can have **year** which corresponds to a
      folder (i.e. 2020) which is located in a course.

  - **problem**
    - A problem corresponds to a single excersice, which
      student can solve. Each problem is divided into tests.
      Each test having unique ID (more below).

      Each problem have several key files/folders:
        - input
          - this folder *can* contain input files, which will be
            redirected to the stdin stream when running the tests
        - output
          - this folder *can* contain output files, which will
            be used in comparison (there correct solutions are
            called **reference outputs**)
        - error
          - no use as of now, only captures stderr from the run.
        - assets
          - this folder contains files, which will be
            available during the execution in student current
            working directory.
          - this folder can contain for example `.mat`,
            `.csv` or `.xls` files which can be loaded
            for an example in a m-file script.
          - if you want to include files which are different
            for each test, you can do so by creating
            *directory* in a assets *directory* having the
            name of a test's id and put the files there.
          - i.e.:
            ```
            assets/
            ├── foo.mat
            ├── TEST-A
            │   └── data.mat
            └── TEST-B
                └── data.mat
            ```
            this will allow to include file `foo.mat`, which
            will be available in every test. In test `TEST-A`,
            file `data.mat` will now by also available and in
            test `TEST-B` different file `data.mat` will be
            available to the student to work with.

    - General use case of solution handeling:
      1) Student will submit a solution to this problem.
      2) Stdout from the application run is saved to a file.
      3) This files will be compared line by line to 
         reference file.
      4) If everything matches (ignoring whitespaces here and
         there), solution is correct.
      5) Based on a allowed duration, result may be affected
         (Let's say the allowed time in problem was 1sec but the
         solution was running for a 1.5 sec, then even though the
         solution is correct, result will be
         `ANSWER_CORRECT_TIMEOUT` rather than `ASNWER_CORERCT`)

  - **test**
    - Each test is a part of a specific problem. Each test must 
      have unique id, by which is referenced. An Id will also be
      used in a file system (files/folder) so be sure to not
      inlcude any path dangerous characters such as
      slashes, question marks, colons, ...
    - For each test you can specify timeout in seconds (float value)
      and if runtime of a submitted solution is over this value,
      student will be warned and solution will be flagged as having 
      overstepped the allowed time limit. 
    - A test can be either:
      - static - which means that input and output files **must**
        be present in a repository, and the test name must and with
        `.s`, such as `TEST.A.s`, and input file located in
        `<course>/<year>/problems/<problem>/input/TEST.A.s`
        must exists (same with the output file).
      - dynamic - this typo of tests requires on a reference
        solution, which **must** be part of a repository.
        Teacher has an option to generate input and output files
        using this reference solution. Test can have a optional 
        property `size`, which will be passed to the reference 
        solution as an parameter `-p`, i.e.:

        ```yaml
        tests:
          - id:   TEST-A
            size: 42
        ```

        and reference solution will be called with as:

        `<reference-solution-name> -p 42`

        You can also generate several sub tests from this test when using proprty `random`, If you set random to 3, it will generate 3 subtests. The id if subtest will be original test id suffixed with `.<subtest index>` i.e. `.0`, `.1`, and `.2`.

        i.e.:

        ```yaml
        tests:
          - id:     TEST-A
            random: 3
            size:   42
        ```

        will generate 3 subtests `TEST-A.0`, `TEST-A.1` and `TEST-A.2`. For each subtest you generate input and output files. Reference solution will be called with:

        `<reference-solution-name> -p 42 -r 0` in case of `TEST-A.0`

        `<reference-solution-name> -p 42 -r 1` in case of `TEST-A.1`

        `<reference-solution-name> -p 42 -r 2` in case of `TEST-A.2`

        
