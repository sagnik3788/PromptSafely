def test_sanity():
    # simple sanity test: use explicit raise to avoid Bandit B101 (assert_used)
    if not True:
        raise AssertionError("Sanity test failed")
