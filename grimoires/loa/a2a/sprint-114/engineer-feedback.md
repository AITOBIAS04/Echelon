All good.

Clean implementation of SDD §2.3. Same-event priority over overlap-scope is correct. Scope key normalization via `.key()` addresses SDD §4.4 risk. Match strength thresholds (EXACT/PARTIAL/WEAK) well-tested. Python 3.9 compat fix (Optional[] instead of X|None) noted.
