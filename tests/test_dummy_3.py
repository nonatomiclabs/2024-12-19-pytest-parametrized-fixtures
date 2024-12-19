import pytest

@pytest.fixture(params=["red", "blue"], scope="session")
def color(request):
    return request.param

@pytest.fixture(scope="session")
def size():
    return "small"

def test_dummy(color, size):
    ...
