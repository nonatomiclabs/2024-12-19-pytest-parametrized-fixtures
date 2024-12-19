The purpose of this repo is to highlight a potential misunderstanding of how parametrized fixtures work.

> A Docker image accompanies the repo if you want to re-run the examples, just build it with `docker build . -t "pytest-parametrized-fixtures"`.

### What are parametrized fixtures anyway?

Pytest allows you to run the same test with different test values with the `@pytest.mark.parametrize` decorator:

```python
import pytest

@pytest.mark.parametrized("color", ["red", "blue"])
def test_dummy(color):
    ...
```

Similarly, you can also parametrize fixtures that are used by a test. In fact, the above example could be rewritten as:

```python
import pytest

@pytest.fixture(params=["red", "blue"])
def color(request):
    return request.param

def test_dummy(color):
    ...
```

In this new example, the fixture `color` is parametrized with the values `"red"` and `"blue"`.

### A fixture's lifecycle

Having said that the fixture is parametrized doesn't tell us how it will be instantiated: will both `red` and `blue` value be created at the beginning of the test session and destroyed at the end, or will they be individually created and destroyed on the fly?

The Pytest option `--setup-plan` serves exactly that purpose:

```bash
$ docker run --rm pytest-parametrized-fixtures 1
───────┬────────────────────────────────────────────────────────────────────────
       │ File: test_dummy_single.py
───────┼────────────────────────────────────────────────────────────────────────
   1   │ import pytest
   2   │ 
   3   │ @pytest.fixture(params=["red", "blue"])
   4   │ def color(request):
   5   │     return request.param
   6   │ 
   7   │ def test_dummy(color):
   8   │     ...
───────┴────────────────────────────────────────────────────────────────────────
+ pytest --setup-plan test_dummy_single.py
============================= test session starts ==============================
platform linux -- Python 3.13.1, pytest-8.3.4, pluggy-1.5.0
rootdir: /home
collected 2 items

test_dummy_single.py 
        SETUP    F color['red']
        test_dummy_single.py::test_dummy[red] (fixtures used: color, request)
        TEARDOWN F color['red']
        SETUP    F color['blue']
        test_dummy_single.py::test_dummy[blue] (fixtures used: color, request)
        TEARDOWN F color['blue']

============================ no tests ran in 0.01s =============================
```

So we see that Pytest will:
- first, go through the setup of the `color` fixture with the value `red`
- then, run the test
- finally, go through the teardown of the `color` fixture, still with the value `red`

It will then proceed to do the same with the value `blue`.


### Adding another fixture

We can easily add another fixture to see how it impacts the setup plan. Let's not parametrize it for now.

```bash
$ docker run --rm pytest-parametrized-fixtures 2
───────┬────────────────────────────────────────────────────────────────────────
       │ File: test_dummy_2.py
───────┼────────────────────────────────────────────────────────────────────────
   1   │ import pytest
   2   │ 
   3   │ @pytest.fixture(params=["red", "blue"])
   4   │ def color(request):
   5   │     return request.param
   6   │ 
   7   │ @pytest.fixture
   8   │ def size():
   9   │     return "small"
  10   │ 
  11   │ def test_dummy(color, size):
  12   │     ...
───────┴────────────────────────────────────────────────────────────────────────
+ pytest --setup-plan test_dummy_2.py
============================= test session starts ==============================
platform linux -- Python 3.13.1, pytest-8.3.4, pluggy-1.5.0
rootdir: /home
collected 2 items

test_dummy_2.py 
        SETUP    F color['red']
        SETUP    F size
        test_dummy_2.py::test_dummy[red] (fixtures used: color, request, size)
        TEARDOWN F size
        TEARDOWN F color['red']
        SETUP    F color['blue']
        SETUP    F size
        test_dummy_2.py::test_dummy[blue] (fixtures used: color, request, size)
        TEARDOWN F size
        TEARDOWN F color['blue']

============================ no tests ran in 0.01s =============================
```

Interestingly, we see that we go through the setup and teardown of `size` twice, even though it's not parametrized.

### How a fixture scope impacts its lifecycle

This is because of the fixture scope, which is set to `function` by default. This means that the fixture is created and destroyed for each execution of the test function, a sensible default to be sure to limit side effects that could arise when re-using a fixture.

Let's change both fixtures' scopes to be `session` instead, the longest lasting scope offered by Pytest, which corresponds to the entire test session.

```bash
$ docker run --rm pytest-parametrized-fixtures 3
───────┬────────────────────────────────────────────────────────────────────────
       │ STDIN
───────┼────────────────────────────────────────────────────────────────────────
   1   │ --- test_dummy_2.py 2024-12-19 11:16:02.975354853 +0000
   2   │ +++ test_dummy_3.py 2024-12-19 11:27:28.565153276 +0000
   3   │ @@ -1,12 +1,12 @@
   4   │  import pytest
   5   │  
   6   │ -@pytest.fixture(params=["red", "blue"])
   7   │ +@pytest.fixture(params=["red", "blue"], scope="session")
   8   │  def color(request):
   9   │      return request.param
  10   │  
  11   │ -@pytest.fixture
  12   │ +@pytest.fixture(scope="session")
  13   │  def size():
  14   │      return "small"
  15   │  
  16   │  def test_dummy(color, size):
  17   │      ...
───────┴────────────────────────────────────────────────────────────────────────
+ pytest --setup-plan test_dummy_3.py
============================= test session starts ==============================
platform linux -- Python 3.13.1, pytest-8.3.4, pluggy-1.5.0
rootdir: /home
collected 2 items

test_dummy_3.py 
SETUP    S color['red']
SETUP    S size
        test_dummy_3.py::test_dummy[red] (fixtures used: color, request, size)
TEARDOWN S color['red']
SETUP    S color['blue']
        test_dummy_3.py::test_dummy[blue] (fixtures used: color, request, size)
TEARDOWN S color['blue']
TEARDOWN S size

============================ no tests ran in 0.01s =============================
```

There are two interesting things to see here:

1. We now go only once through the setup and teardown of the `size` fixture, as we expect
2. The setup plan for the `color` fixture is unchanged though, as we still need to go through it for each parameter value

### Expectations on parametrizing the `size` fixture

If we parametrize the `size` fixture with the values `big` and `small`, here are the combinations we will cover:

- red and big
- red and small
- blue and big
- blue and small

From this list, I would expect that we go through four setup/teardown "cycles": once for `red`, once for `blue`, once for `small` and once for `big`.

### What actually happens

Let's see if that expectations holds:

```bash
$ docker run --rm pytest-parametrized-fixtures 4
───────┬────────────────────────────────────────────────────────────────────────
       │ STDIN
───────┼────────────────────────────────────────────────────────────────────────
   1   │ --- test_dummy_3.py 2024-12-19 11:27:28.565153276 +0000
   2   │ +++ test_dummy_4.py 2024-12-19 12:18:00.521651984 +0000
   3   │ @@ -1,12 +1,12 @@
   4   │  import pytest
   5   │  
   6   │  @pytest.fixture(params=["red", "blue"], scope="session")
   7   │  def color(request):
   8   │      return request.param
   9   │  
  10   │ -@pytest.fixture(scope="session")
  11   │ -def size():
  12   │ -    return "small"
  13   │ +@pytest.fixture(params=["big", "small"], scope="session")
  14   │ +def size(request):
  15   │ +    return request.param
  16   │  
  17   │  def test_dummy(color, size):
  18   │      ...
───────┴────────────────────────────────────────────────────────────────────────
+ pytest --setup-plan test_dummy_4.py
============================= test session starts ==============================
platform linux -- Python 3.13.1, pytest-8.3.4, pluggy-1.5.0
rootdir: /home
collected 4 items

test_dummy_4.py 
SETUP    S color['red']
SETUP    S size['big']
        test_dummy_4.py::test_dummy[red-big] (fixtures used: color, request, size)
TEARDOWN S size['big']
SETUP    S size['small']
        test_dummy_4.py::test_dummy[red-small] (fixtures used: color, request, size)
TEARDOWN S color['red']
SETUP    S color['blue']
        test_dummy_4.py::test_dummy[blue-small] (fixtures used: color, request, size)
TEARDOWN S size['small']
SETUP    S size['big']
        test_dummy_4.py::test_dummy[blue-big] (fixtures used: color, request, size)
TEARDOWN S size['big']
TEARDOWN S color['blue']

============================ no tests ran in 0.01s =============================
```

Analyzing what Pytest does, we see it's actually not what we expect: there are 5 `SETUP` phases (and 5 corresponding `TEARDOWN` phases). Looking at the output, we see the `big` fixture value has to be created/destroyed twice, unlike others that all go through one cycle only.

This comes from the fact that, *even though both fixtures are session-scoped*, Pytest drops the `size['big']` fixture value in order to test the "red and small" combination, and it has to re-create `size['big']` later when it tests the "blue and big" combination.

### Adding fixture execution order to the mix

Of course, `size['big']` is the "culprit" here only because of how we parametrized our fixtures and our test. If we simply switch the `big` and `small` or if our test requests `size` before `color`, this changes everything:

```bash
$ docker run --rm pytest-parametrized-fixtures 5
───────┬────────────────────────────────────────────────────────────────────────
       │ STDIN
───────┼────────────────────────────────────────────────────────────────────────
   1   │ --- test_dummy_4.py 2024-12-19 12:18:00.521651984 +0000
   2   │ +++ test_dummy_5.py 2024-12-19 12:30:24.678568456 +0000
   3   │ @@ -1,12 +1,12 @@
   4   │  import pytest
   5   │  
   6   │  @pytest.fixture(params=["red", "blue"], scope="session")
   7   │  def color(request):
   8   │      return request.param
   9   │  
  10   │ -@pytest.fixture(params=["big", "small"], scope="session")
  11   │ +@pytest.fixture(params=["small", "big"], scope="session")
  12   │  def size(request):
  13   │      return request.param
  14   │  
  15   │ -def test_dummy(color, size):
  16   │ +def test_dummy(size, color):
  17   │      ...
───────┴────────────────────────────────────────────────────────────────────────
+ pytest --setup-plan test_dummy_5.py
============================= test session starts ==============================
platform linux -- Python 3.13.1, pytest-8.3.4, pluggy-1.5.0
rootdir: /home
collected 4 items

test_dummy_5.py 
SETUP    S size['small']
SETUP    S color['red']
        test_dummy_5.py::test_dummy[small-red] (fixtures used: color, request, size)
TEARDOWN S color['red']
SETUP    S color['blue']
        test_dummy_5.py::test_dummy[small-blue] (fixtures used: color, request, size)
TEARDOWN S size['small']
SETUP    S size['big']
        test_dummy_5.py::test_dummy[big-blue] (fixtures used: color, request, size)
TEARDOWN S color['blue']
SETUP    S color['red']
        test_dummy_5.py::test_dummy[big-red] (fixtures used: color, request, size)
TEARDOWN S color['red']
TEARDOWN S size['big']

============================ no tests ran in 0.01s =============================
```

Now, `color['red']` is the "culprit".

You can easily imagine the implications if `color` is a fixture that takes very long to execute. Or if there are not two parametrized fixtures involved but ten…

### What now?

There are a few things to conclude from this example:

1. Use the `--setup-plan` option when you need to know how Pytest will execute your tests.
2. Your (or really, my) mental model of fixtures might not match how Pytest really works.
3. Keep your (parametrized) fixtures as lightweight as possible. If your fixture has to do something "heavy", assume it might be called multiple times and prepare accordingly for it (return a cached result for instance).