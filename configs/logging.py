from os import system
from configs.settings import DEBUG, VERBOSE

dummy_print = lambda *y, **z: ""
print1 = print if DEBUG else dummy_print
print2 = print1 if VERBOSE > 1 else dummy_print
print3 = print1 if VERBOSE > 2 else dummy_print
print4 = print1 if VERBOSE > 3 else dummy_print
cls = lambda: system("cls") if DEBUG else dummy_print