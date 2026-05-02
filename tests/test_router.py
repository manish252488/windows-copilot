from jarvis.actions.router import CommandRouter


def test_route_many_joins_results() -> None:
    router = CommandRouter()
    result = router.route_many("google testing testcase")
    assert result is not None
