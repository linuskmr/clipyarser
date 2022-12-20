# clipyarser

`clipyarser` is a simple, declarative and easy-testable command line argument parser.
It's inspired by [Typer](https://github.com/tiangolo/typer).

Simply decorate your _normal_ python functions with `@clipyarser.main` or `@clipyarser.subcommand` and
you have a fully working cli program.
`clipyarser` parses the arguments from the console and calls the matching function with the right arguments.


## Features

- No dependencies: Argument parsing is done with Python's [argparse](https://docs.python.org/3/library/argparse.html) module
- Parsing and validation based on *type hints*
- Global arguments via `@clipyarser.main`
- [Subcommands](#subcommands) with `@clipyarser.subcommand`
- [Default arguments](#default-argumentsoptions)
- [Easily testing](#testing), because functions `yield` instead of `print()` lines



## TL;DR — Show me the code

Example: Calculator with `add` and `sub` *subcommands*, and a *global* `verbose` switch.

```python3
from clipyarser import Clipyarser

clipyarser = Clipyarser()

verbose_output = None

@clipyarser.subcommand
def add(lhs: int, rhs: int):
	"""Compute lhs + rhs"""
	if verbose_output:
		yield f"Computing {lhs} + {rhs}"
	yield lhs + rhs

@clipyarser.subcommand
def sub(lhs: int, rhs: int = 0):
	"""Compute lhs - rhs"""
	if verbose_output:
		yield f"Computing {lhs} - {rhs}"
	yield lhs + rhs

@clipyarser.main
def main(verbose: bool = False):
	"""Useless calculator"""
	# main gets always called
	# We use it for arguments used in *all* subcommands
	global verbose_output
	verbose_output = verbose

if __name__ == '__main__':
	clipyarser.run()
```

Help message with doc comment for `main`:

```
$ python3 cli.py --help
usage: cli.py [-h] [--verbose VERBOSE] {add,sub} ...

Useless calculator

positional arguments:
  {add,sub}

optional arguments:
  -h, --help         show this help message and exit
  --verbose VERBOSE
```

Help message for `add`:

```
$ python3 cli.py add --help
usage: cli.py add [-h] lhs rhs

Compute lhs + rhs

positional arguments:
  lhs
  rhs

optional arguments:
  -h, --help  show this help message and exit
```

Invoke add:

```
$ python3 cli.py add 3 4
7
```

Invoke sub with default argument and use global `verbose` argument:

```
$ python3 cli.py --verbose True sub 5
Computing 5 - 0
5
```

Error handling:

```
$ python3 cli.py add
usage: cli.py add [-h] lhs rhs
cli.py add: error: the following arguments are required: lhs, rhs
```



## Tutorial

Here we will create a small command line application with `clipyarser`.

### Setup

Create a new directory and an empty `main.py` file.

In `main.py` import `clipyarser`:

```python
from clipyarser import CLI
```

### Create a CLI parser

To create a `clipyarser` parser, simply write this into the `main.py` file.

```python
from clipyarser import Clipyarser

clipyarser = Clipyarser()
```

Now we create a simple greeting function.

```python
@clipyarser.main
def main(name: str) -> str:
    return f'Hello {name}'
```

This function simply returns a string which says "hello" to a person.
The name of the person is specified in the arguments of the function.

Note that we use **type hints** in the function arguments.
This is necessary for `clipyarser`, because it parses the arguments from the console according to the specified types.
So when adding an argument `age` with type `int`, `clipyarser` does the parsing and validation of an `int` for you.

Now, we have to execute `clipyarser` when the program is run.

```python
if __name__ == '__main__':
    clipyarser.run()
```

And that is the first running example of `clipyarser`.

Now lets test it.

```shell
$ python3 main.py
usage: example.py [-h] name {} ...
example.py: error: the following arguments are required: name
```

Ok, we have to specify the name of the person we want to greet.
This makes sense, because we take `name` as argument in our `main()` function.

```shell
$ python3 main.py Linus
Hello Linus
```

Ok nice. That worked.

### Default Arguments/Options

Sometimes it is convenient that a function has default arguments, which can be overridden when calling the function.
This is also possible with `clipyarser`. Let's try to take our greeting function from above and extend it with an
optional argument.

```python
@clipyarser.main
def main(name: str, greeting: str = 'Hello') -> str:
  return f'{greeting} {name}'
```

So a user can customize the greeting. By default, the greeting is 'Hello', but it can be overridden.
Now let's see how this looks in the console.

```shell
$ python3 main.py Linus
Hello Linus
$ python3 main.py Linus --greeting Hi
Hi Linus
```

Pretty intiutive, right?

### Subcommands

In a bigger application, you may don't want all logic in a `main()` function.
Therefore, `clipyarser` allows you to add subcommands.

```python3
from clipyarser import Clipyarser

clipyarser = Clipyarser()

@clipyarser.subcommand
def add(a: int, b: int) -> int:
    return a + b
```

This subcommand is a function which adds to numbers together.

```shell
$ python3 main.py add 2 4
6
```

But what has happened to the main function? For simplicity, we have deleted it.
Let's try to add one again.

```shell
@clipyarser.main
def main(verbose: bool = False):
  return 'verbose is {verbose}'
```

Now, when calling our application, the `main()` function *always* runs.
This might be handy when you have some logic or arguments that are independent of am individual subcommand, like a 
more verbose output.

```shell
$ python3 main.py add 3 2
verbose is False
5
$ python3 main.py --verbose true add 3 2
verbose is True
5
```

### Printing multiple lines

Until now, when we want to print something to the console, we just returned it.
This might seem ok, but sometimes you want to print multiple lines or want to print something during a calculation.
But simple `print()`ing is not a good idea. We will se soon [why](#testing).

To print multiple lines, use the `yield` statement.

Back to our greeting example from the beginning.

```python3
from time import sleep
from clipyarser import Clipyarser

clipyarser = Clipyarser()


@clipyarser.main
def main(name: str):
    yield 'Hello'
    sleep(2)
    yield name
    yield 42
```

```shell
$ python3 main.py Linus
Hello
Linus
42
```

Because yield turns `main()` into a *generator function*, the output 'Hello' is printed *immediately*, but `name` takes 
two seconds to print.

Maybe one could think of another solution: Just add all things to be printed to a list and return this list at the 
end of the function.
This is bad, because the whole output would take two seconds to print, in particular the 'Hello' line.
This makes your `clipyarser` not very responsive to the end user.

Ok. But why is just printing a bad idea? Testing.

### Testing

The advantage of CLI is simple testing.
Functions like `main()` and `add()` are *normal python functions*, so you can call them like normal functions.
They take *normal* arguments. They return *normal* things, e.g. a generator instead of printing.
This means that you can also test these functions like normal functions.

```python3
import unittest
from clipyarser import Clipyarser

clipyarser = Clipyarser()


class TestMyCli(unittest.TestCase):
    def test_greet(self):
        actual = list(main('Linus'))
        expected = ['Hello', 'Linus', 42]
        self.assertEqual(actual, expected)
```

Since `main()` is a generator function, we can convert its output to a list and check if it is what we expect.
If using `print()`, this would not be as easy.

Ok, this is the end of the tutorial. Have fun using `clipyarser`.
