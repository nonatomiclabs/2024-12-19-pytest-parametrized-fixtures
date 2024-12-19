import pytest

@pytest.fixture(params=["red", "blue"])
def color(request):
    return request.param

@pytest.fixture
def size():
    return "small"

def test_dummy(color, size):
    ...
