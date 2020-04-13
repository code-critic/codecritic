# How to create a course?

Every course have its own Github repository which must be manually registered to the running CodeCritic server.
The course repository must contain folders named by years (2019, 2020, ...)
where each year can have its own configuration. The configuration is given by the 
single YAML file `{course repository}`/`{year}`/`config.yaml`.

Use [config_template.yaml](https://github.com/code-critic/codecritic/edit/master/doc/config_template.yaml)
as both the template and the documentation.

The year folder has the structure:
```
|- problem_1
|  |- input
|  |  case-1.s    # problem fixed inputs.  
|  |  ...
|  main.py        # problem script.
|  README.md      # problem description, markdown format
|- problem_2
|  ...
|- ...
| config.yaml     # course configuration.
| README.md       # course description, markdown format
```

Every problem is specified through the **script**. It can be written in any suppored language, but must be a single souce file. The script must behave as a reference solution when called without arguments with an input file redirected to its STDIN, e.g.

    python3 main.py < case-1.s

should solve the problem with input from `case-1.s`, solution is printed to the STDOUT.

Optionaly the script can support (pseudorandom) generation of the input files:

    python3 main.py -p <SIZE> -r <I>

should print the generated input file to the STDOUT. 
<SIZE> is the given problem size 
<I> is the subtest index 
These arguments can be used by the script to set the seed of pseudorandom generator and get a reproducible output.

