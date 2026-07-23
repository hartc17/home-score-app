from app.auth.ratelimit import SlidingWindowLimiter


def test_allows_up_to_max_then_blocks():
    limiter = SlidingWindowLimiter(3, 60.0)
    assert [limiter.allow("k", 0.0) for _ in range(4)] == [True, True, True, False]


def test_window_slides_and_frees_capacity():
    limiter = SlidingWindowLimiter(2, 60.0)
    assert limiter.allow("k", 0.0)
    assert limiter.allow("k", 30.0)
    assert not limiter.allow("k", 59.0)
    assert limiter.allow("k", 61.0)


def test_keys_are_isolated():
    limiter = SlidingWindowLimiter(1, 60.0)
    assert limiter.allow("a", 0.0)
    assert limiter.allow("b", 0.0)
    assert not limiter.allow("a", 1.0)


def test_reset_clears_all_state():
    limiter = SlidingWindowLimiter(1, 60.0)
    assert limiter.allow("k", 0.0)
    limiter.reset()
    assert limiter.allow("k", 1.0)
