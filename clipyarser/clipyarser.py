import inspect
import sys
import types
from argparse import ArgumentParser
from typing import Callable, Dict, Optional, Any


class Clipyarser:
    """
    Simple, declarative and easy-testable command line argument parser.
    Inspired by https://github.com/tiangolo/typer
    """

    name: str
    """The name of the CLI program."""

    description: str
    """A description for the CLI program."""

    _subcommand_functions: Dict[str, Callable]
    """All registered functions used as subcommands."""

    _main_function: Optional[Callable]
    """The main function, which is called for every run of the CLI program."""

    SUBCOMMAND_DEST: str = '__SUBCOMMAND'
    """The key in the ArgumentParser where the subcommand name is stored in."""

    def __init__(self, name: str = sys.argv[0], description: str = ''):
        """Creates a new CLI with an optional name and description."""
        self.name = name
        self.description = description
        self._subcommand_functions = {}
        self._main_function = None

    def subcommand(self, function: Callable):
        """Adds the decorated function as a subcommand do the CLI."""
        function_name = function.__name__
        self._subcommand_functions[function_name] = function
        return function

    def main(self, function: Callable):
        """Adds the decorated function as main function. This function is called for every run of the CLI."""
        self._main_function = function
        return function

    @staticmethod
    def add_args(*, function: Callable, parser: ArgumentParser):
        """Adds the arguments needed by function to the given ArgumentParser."""
        for arg in inspect.signature(function).parameters.values():
            # Add all arguments from this function to the parser
            arg_name = arg.name
            if arg.default is not inspect.Parameter.empty:
                # Argument has a default value, so make it a command line option
                cli_option_prefix = '--'
                arg_name = cli_option_prefix + arg_name
            parser.add_argument(arg_name, type=arg.annotation, default=arg.default)

    def create_main_parser(self):
        """Creates the main ArgumentParser and includes the arguments of self._main_function."""
        parser = ArgumentParser(prog=self.name, description=self.description)
        if self._main_function:
            Clipyarser.add_args(parser=parser, function=self._main_function)
        return parser

    def create_subparsers(self, parser: ArgumentParser):
        """Creates all subparsers for every subcommand in self._functions and adds them to the parser."""
        subparsers = parser.add_subparsers(dest=Clipyarser.SUBCOMMAND_DEST)
        for function_name, function in self._subcommand_functions.items():
            # Create subparser for this function
            subparser = subparsers.add_parser(function_name)
            Clipyarser.add_args(parser=subparser, function=function)

    @staticmethod
    def call_function(*, function: Callable, parsed_args: Dict[str, Any]):
        """Calls the function with its needed arguments as subset from parsed_args"""
        function_signature = inspect.signature(function)
        function_parameters = function_signature.parameters
        call_args = {}
        for function_param in function_parameters.values():
            # Get each function parameter from the argparser
            arg_param = parsed_args[function_param.name]
            call_args[function_param.name] = arg_param
        return_values = function(**call_args)
        if not return_values:
            # Function didn't return anything
            return
        if isinstance(return_values, types.GeneratorType):
            for line in return_values:
                print(line)
        else:
            print(return_values)

    def run(self):
        """Runs the CLI program."""
        parser = self.create_main_parser()
        self.create_subparsers(parser)
        args = vars(parser.parse_args())
        if not args[Clipyarser.SUBCOMMAND_DEST] and not self._main_function:
            # No subcommand provided and no main function registered
            parser.error('No subcommand provided and no main function registered')
            return
        if self._main_function:
            # If main function is set, call it
            self.call_function(function=self._main_function, parsed_args=args)
        if args[Clipyarser.SUBCOMMAND_DEST]:
            # Get subcommand function from specified subcommand
            function = self._subcommand_functions[args[Clipyarser.SUBCOMMAND_DEST]]
            # Call subcommand function
            Clipyarser.call_function(function=function, parsed_args=args)
