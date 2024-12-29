## Unit Tests

Unit testing is done with `pytest`.
To run all the tests, simply `cd` to the top level directory and type this shell command:

```bash
$ pytest
```

The tests are all in the `tests` directory:

* `test_main.py` has functions that test each of the paths defined in `main.py`
* `test_optipass.py` has functions that test the interface to OptiPass

You can run one set of tests by including the file name in the shell command, _e.g._

```bash
$ pytest test/test_optipass.py
```

### Tests for `main.py`

::: test.test_main
    options:
      heading_level: 4
      members_order: source

### Tests for `optipass,py`

::: test.test_optipass
    options:
      heading_level: 4
      members_order: source

