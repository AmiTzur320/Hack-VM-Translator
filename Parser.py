"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing

ARITHMETIC = {
    "add", "sub", "neg", "eq", "gt", "lt",
    "and", "or", "not", "shiftleft", "shiftright"
}
COMMANDTYPE = {"push": "C_PUSH", "pop": "C_POP", "label": "C_LABEL", "goto": "C_GOTO", "if-goto": "C_IF",
               "function": "C_FUNCTION", "call": "C_CALL", "return": "C_RETURN"}


class Parser:
    """
    # Parser
    
    Handles the parsing of a single .vm file, and encapsulates access to the
    input code. It reads VM commands, parses them, and provides convenient 
    access to their components. 
    In addition, it removes all white space and comments.

    ## VM Language Specification

    A .vm file is a stream of characters. If the file represents a
    valid program, it can be translated into a stream of valid assembly 
    commands. VM commands may be separated by an arbitrary number of whitespace
    characters and comments, which are ignored. Comments begin with "//" and
    last until the line's end.
    The different parts of each VM command may also be separated by an arbitrary
    number of non-newline whitespace characters.

    - Arithmetic commands:
      - add, sub, and, or, eq, gt, lt
      - neg, not, shiftleft, shiftright
    - Memory segment manipulation:
      - push <segment> <number>
      - pop <segment that is not constant> <number>
      - <segment> can be any of: argument, local, static, constant, this, that, 
                                 pointer, temp
    - Branching (only relevant for project 8):
      - label <label-name>
      - if-goto <label-name>
      - goto <label-name>
      - <label-name> can be any combination of non-whitespace characters.
    - Functions (only relevant for project 8):
      - call <function-name> <n-args>
      - function <function-name> <n-vars>
      - return
    """

    def __init__(self, input_file: typing.TextIO) -> None:
        """Gets ready to parse the input file.

        Args:
            input_file (typing.TextIO): input file.
        """
        self.lines = []
        self.current = None
        self.index = -1

        for line in input_file:
            line = line.split("//", 1)[0]
            line = line.strip().lstrip("\ufeff")
            if line:
                self.lines.append(line)

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        return self.index + 1 < len(self.lines)

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current 
        command. Should be called only if has_more_commands() is true. Initially
        there is no current command.
        """
        if self.has_more_commands():
            self.index += 1
            self.current = self.lines[self.index]

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current VM command.
            "C_ARITHMETIC" is returned for all arithmetic commands.
            For other commands, can return:
            "C_PUSH", "C_POP", "C_LABEL", "C_GOTO", "C_IF", "C_FUNCTION",
            "C_RETURN", "C_CALL".
        """
        if self.current is None:
            raise ValueError("commandType() called before advance() or on empty input")
        parts = self.current.split()
        if not parts:
            raise ValueError(f"Empty line encountered at index {self.index}")
        first = parts[0]
        if first in ARITHMETIC:
            return "C_ARITHMETIC"
        elif first in COMMANDTYPE:
            return COMMANDTYPE[first]
        else:
            raise ValueError(f"Unknown command '{first}' at index {self.index}: {self.current}")

    def arg1(self) -> str:
        """
        Returns:
            str: the first argument of the current command. In case of 
            "C_ARITHMETIC", the command itself (add, sub, etc.) is returned. 
            Should not be called if the current command is "C_RETURN".
        """
        if self.current is None:
            raise ValueError("arg1() called before advance()")
        parts = self.current.split()
        ctype = self.command_type()

        if ctype == "C_RETURN":
            raise ValueError("arg1() should not be called if commandType is C_RETURN")
        elif ctype == "C_ARITHMETIC":
            return parts[0]  # add,sub,neg
        else:
            return parts[1]  # push , pop

    def arg2(self) -> int:
        """
        Returns:
            int: the second argument of the current command. Should be
            called only if the current command is "C_PUSH", "C_POP", 
            "C_FUNCTION" or "C_CALL".
        """
        parts = self.current.split()
        ctype = self.command_type()
        if ctype not in ("C_PUSH", "C_POP", "C_FUNCTION", "C_CALL"):
            raise ValueError(f"arg2() is not valid for command type {ctype}")
        return int(parts[2])  # "local", "argument" ....


