#!/bin/python3
# author: Jan Hybs

import pytest


@pytest.mark.general
def test_javafix_fixes():
    a = '''
import java.util.Scanner;
package foo.bar;
public class foobar {
'''
    b = '''
import java.util.Scanner;
// package foo.bar;
public class main {
'''

    from utils.javafix import fix_java_solution

    assert '\n'.join(fix_java_solution(a).splitlines()) == '\n'.join(b.splitlines())
