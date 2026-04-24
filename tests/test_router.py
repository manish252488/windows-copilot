from jarvis.actions.router import CommandRouter


def test_route_many_joins_results() -> None:
    router = CommandRouter()
    result = router.route_many("google python and youtube ai news")
    assert result is not None
