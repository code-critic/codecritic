## Docs for /`{course}`/`{year}`/`config.yaml`

```yaml
- id:       problem-1           # directory name!
  name:     Answer is 42!       # what student will see
  timeout:  120                 # max time per solution, default is 60
  avail:    2020-03-11 16:00:00 # problem will be active until YYYY-mm-dd HH:MM:SS
  reference:                    # purpose of reference is two fold:
                                #   1)  it can generate files which will be used as stdin 
                                #       when testing
                                #   2)  it can generate output files which will be used in comparison with a student stdout
                                #       generated files
                                #   3)  when unittest is on, the language in which reference is written will
                                #       be the only allowed programming language, student's can use

    name: main.py               # name of the script
    lang: PY-367                # and language ID from (cfg/langs.yaml) explicitely
                                # valid laguages: [PY-367, C, CPP, JAVA, PY-276, CS]
                                # see: https://github.com/code-critic/codecritic/blob/master/cfg/langs.yaml

  tests:
    - id: case-1.s              # by adding extension .s
                                # the input will be part of a repository
      timeout: 0.2              # value in seconds, allowed duration of the solution
                                # this value is scaled by
                                # programming language scale factor (cfg/langs.yaml)

    - id: case-2                # this file will be ignored by the git and won't 
      timeout: 5.0              # be part of this repository
                                # this usually means, the file will be created 
                                # using reference script
      size: 50                  # if size is specified, the will **can** be generated
                                # using reference script, the value is passed
                                # to the reference script which then generates
                                # input file by writing to standard output stream
                                # in this case the reference script will be called:
                                #     python3 main.py -p 50

    - id: case-3
      random: 5                 # this value indicate that there will be generated
      timeout: 0.2              # several input files (5 in this case)
                                # this will then generate subcases
                                # case-3.1, case-3.2, ..., case-3.5
                                # all cases will be tested when solution is submitted
      size: 15
                                # in this case the reference script will be called:
                                #     python3 main.py -p 15 -r

- id: problem-2
# to add more tests simple repeat the structure
# - id: foobar
#   ...
#   tests:
#     - id: ...

```
