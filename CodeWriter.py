"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import os
import typing

binary = {
    "add": "M=M+D",
    "sub": "M=M-D",
    "and": "M=M&D",
    "or": "M=M|D",

}
unary = {
    "not": "M=!M",
    "neg": "M=-M",
    "shiftleft": "M=M<<",
    "shiftright": "M=M>>"
}
comparisons = {"eq": "JEQ", "gt": "JGT", "lt": "JLT", "ge": "JGE"}

PUSH = ["@SP", "A=M", "M=D", "@SP", "M=M+1"]


class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Initializes the CodeWriter.

        Args:
            output_stream (typing.TextIO): output stream.
        """

        self.file = output_stream
        self.filename = None
        self.label_counter = 0
        self.cur_function = None

    def set_file_name(self, filename: str) -> None:
        """Informs the code writer that the translation of a new VM file is 
        started.

        Args:
            filename (str): The name of the VM file.
        """
        # Your code goes here!
        # This function is useful when translating code that handles the
        # static segment. For example, in order to prevent collisions between two
        # .vm files which push/pop to the static segment, one can use the current
        # file's name in the assembly variable's name and thus differentiate between
        # static variables belonging to different files.
        # To avoid problems with Linux/Windows/MacOS differences with regards
        # to filenames and paths, you are advised to parse the filename in
        # the function "translate_file" in Main.py using python's os library,
        # For example, using code similar to:
        # input_filename, input_extension = os.path.splitext(os.path.basename(input_file.name))
        base_name = os.path.basename(filename)
        name_without_extension = os.path.splitext(base_name)[0]
        self.filename = name_without_extension

    def write_line(self, lines):
        if isinstance(lines, str):
            # single line
            self.file.write(lines + "\n")
        else:
            for line in lines:
                self.file.write(line + "\n")

    def write_arithmetic(self, command: str) -> None:
        """Writes assembly code that is the translation of the given 
        arithmetic command. For the commands eq, lt, gt, you should correctly
        compare between all numbers our computer supports, and we define the
        value "true" to be -1, and "false" to be 0.

        Args:
            command (str): an arithmetic command.
        """
        if command in binary:
            self.write_line([
                f"// binary operation: {command}",
                # pop y into D
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                # pop x and apply operation with D
                "@SP",
                "M=M-1",
                "A=M",
                binary[command],  # M=M+D, M=M-D, M=M&D, M=M|D
                # push result (increment SP)
                "@SP",
                "M=M+1"])
        elif command in unary:
            self.write_line([
                f"// unary operation: {command}",
                # access top of stack (SP-1)
                "@SP",
                "A=M-1",
                # apply the operator in-place
                unary[command]])  # M=-M or M=!M


        elif command == "eq":
            # Handle equality comparison: true if x == y, false otherwise
            label_id = self.label_counter
            self.label_counter += 1
            true_label = f"EQ_{label_id}_TRUE"
            end_label = f"EQ_{label_id}_END"

            self.write_line([
                "// comparison: eq",
                # Pop y into D
                "@SP", "M=M-1", "A=M", "D=M",
                # Pop x and compute x - y
                "@SP", "M=M-1", "A=M", "D=M-D",
                # If result is zero -> x == y
                f"@{true_label}", "D;JEQ",
                # False case: write 0
                "@SP", "A=M", "M=0",
                f"@{end_label}", "0;JMP",
                # True case: write -1
                f"({true_label})",
                "@SP", "A=M", "M=-1",
                # Finish: increment SP
                f"({end_label})",
                "@SP", "M=M+1"
            ])

        elif command in ("gt", "lt"):
            # Handle signed greater-than / less-than in a way that avoids overflow
            label_id = self.label_counter
            self.label_counter += 1

            prefix = f"{command.upper()}_{label_id}_"
            x_neg = f"{prefix}X_NEG"
            same_sign = f"{prefix}SAME_SIGN"
            x_pos_y_neg = f"{prefix}X_POS_Y_NEG"
            x_neg_y_non_neg = f"{prefix}X_NEG_Y_NON_NEG"
            true_label = f"{prefix}TRUE"
            end_label = f"{prefix}END"

            code = [
                f"// comparison: {command}",
                # Pop y into R13
                "@SP", "M=M-1", "A=M", "D=M",
                "@R13", "M=D",
                # Pop x into R14
                "@SP", "M=M-1", "A=M", "D=M",
                "@R14", "M=D",

                # Check sign of x
                "@R14", "D=M",
                f"@{x_neg}", "D;JLT",  # If x < 0 -> go to X_NEG

                # Here x >= 0, now check sign of y
                "@R13", "D=M",
                f"@{x_pos_y_neg}", "D;JLT",  # If y < 0 -> x>=0,y<0
                f"@{same_sign}", "0;JMP",  # Otherwise: same sign

                # X_NEG: x < 0, now check sign of y
                f"({x_neg})",
                "@R13", "D=M",
                f"@{x_neg_y_non_neg}", "D;JGE",  # If y >= 0 -> x<0,y>=0
                f"@{same_sign}", "0;JMP",  # Otherwise: both negative -> same sign

                # Case: x>=0, y<0 (different signs)
                f"({x_pos_y_neg})",
            ]

            if command == "gt":
                # For gt: x>=0,y<0 => always true
                code += ["@SP", "A=M", "M=-1", f"@{end_label}", "0;JMP"]
            else:
                # For lt: x>=0,y<0 => always false
                code += ["@SP", "A=M", "M=0", f"@{end_label}", "0;JMP"]

            # Case: x<0, y>=0 (different signs)
            code += [
                f"({x_neg_y_non_neg})",
            ]

            if command == "gt":
                # For gt: x<0,y>=0 => always false
                code += ["@SP", "A=M", "M=0", f"@{end_label}", "0;JMP"]
            else:
                # For lt: x<0,y>=0 => always true
                code += ["@SP", "A=M", "M=-1", f"@{end_label}", "0;JMP"]

            # Same-sign case: now it is safe to use x - y
            code += [
                f"({same_sign})",
                "@R14", "D=M",  # D = x
                "@R13", "D=D-M",  # D = x - y
                f"@{true_label}", "D;JGT" if command == "gt" else "D;JLT",
                # False case
                "@SP", "A=M", "M=0",
                f"@{end_label}", "0;JMP",
                # True case
                f"({true_label})",
                "@SP", "A=M", "M=-1",
                # Finish: increment SP
                f"({end_label})",
                "@SP", "M=M+1"
            ]
            self.write_line(code)
        else:
            raise ValueError(f"Unknown command: {command}")

    def write_push_pop(self, command: str, segment: str, index: int) -> None:
        """Writes assembly code that is the translation of the given 
        command, where command is either C_PUSH or C_POP.

        Args:
            command (str): "C_PUSH" or "C_POP".
            segment (str): the memory segment to operate on.
            index (int): the index in the memory segment.
        """
        # Your code goes here!
        # Note: each reference to "static i" appearing in the file Xxx.vm should
        # be translated to the assembly symbol "Xxx.i". In the subsequent
        # assembly process, the Hack assembler will allocate these symbolic
        # variables to the RAM, starting at address 16.
        if command == "C_PUSH":
            # 1. Get the value into D according to the segment and index
            code = self.getAddressCode(segment, index, for_pop=False)
            # 2. Push D onto the stack
            self.write_line(code + [
                "@SP",  # A = address of the stack pointer
                "A=M",  # A = top of the stack
                "M=D",  # *SP = D (store value on top of stack)
                "@SP",
                "M=M+1"  # SP++
            ])

        elif command == "C_POP":
            # 1. Compute the target address for the segment[index]
            code = self.getAddressCode(segment, index, for_pop=True)
            self.write_line(code + [
                "D=A",  # D = computed address
                "@R13",  # use R13 as a temporary register
                "M=D",  # R13 = target address

                # 2. Pop the top value from the stack into D
                "@SP",
                "M=M-1",  # SP--
                "A=M",  # A = new top of stack
                "D=M",  # D = *SP (popped value)

                # 3. Write D to the target address stored in R13
                "@R13",
                "A=M",  # A = target address
                "M=D"  # *addr = D
            ])

    def getAddressCode(self, segment, index, for_pop=False):
        base_segments = {
            "local": "LCL",
            "argument": "ARG",
            "this": "THIS",
            "that": "THAT"
        }

        # constant
        if segment == "constant":
            return [f"@{index}", "D=A"]

        # base segments
        elif segment in base_segments:
            code = [
                f"@{base_segments[segment]}",
                "D=M",
                f"@{index}",
                "A=D+A"
            ]
            if not for_pop:
                code.append("D=M")
            return code

        # temp
        elif segment == "temp":
            addr = 5 + int(index)
            code = [f"@{addr}"]
            if not for_pop:
                code.append("D=M")
            return code

        # pointer
        elif segment == "pointer":
            addr = 3 + int(index)
            code = [f"@{addr}"]
            if not for_pop:
                code.append("D=M")
            return code

        # static
        elif segment == "static":
            code = [f"@{self.filename}.{index}"]
            if not for_pop:
                code.append("D=M")
            return code

    def close(self):
        if self.file is not None:
            self.file.close()

    def write_init(self) -> None:
        # 1. SP = 256
        self.write_line(["@256", "D=A", "@SP", "M=D"])
        # 2. Call Sys.init
        self.write_call("Sys.init", 0)

    def write_label(self, label: str) -> None:
        """Writes assembly code that affects the label command. 
        Let "Xxx.foo" be a function within the file Xxx.vm. The handling of
        each "label bar" command within "Xxx.foo" generates and injects the symbol
        "Xxx.foo$bar" into the assembly code stream.
        When translating "goto bar" and "if-goto bar" commands within "foo",
        the label "Xxx.foo$bar" must be used instead of "bar".

        Args:
            label (str): the label to write.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!

        # if we are not in any function
        if not self.cur_function:
            self.write_line(f"({label})")
        else:  # if we are in a function we need to write its unique name
            self.write_line(f"({self.cur_function}${label})")

    def write_goto(self, label: str) -> None:
        """Writes assembly code that affects the goto command.

        Args:
            label (str): the label to go to.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        if not self.cur_function:
            self.write_line([f"@{label}", "0;JMP"])
        else:
            self.write_line([f"@{self.cur_function}${label}", "0;JMP"])

    def write_if(self, label: str) -> None:
        """Writes assembly code that affects the if-goto command. 

        Args:
            label (str): the label to go to.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!

        self.write_line(["@SP", "M=M-1", "A=M", "D=M"])
        # pop = now D holds zero or non-zero depends on the top value of the stack

        if not self.cur_function:
            self.write_line([f"@{label}", "D;JNE"])
        else:
            self.write_line([f"@{self.cur_function}${label}", "D;JNE"])

    def write_function(self, function_name: str, n_vars: int) -> None:
        """Writes assembly code that affects the function command. 
        The handling of each "function Xxx.foo" command within the file Xxx.vm
        generates and injects a symbol "Xxx.foo" into the assembly code stream,
        that labels the entry-point to the function's code.
        In the subsequent assembly process, the assembler translates this 
        symbol into the physical address where the function code starts.

        Args:
            function_name (str): the name of the function.
            n_vars (int): the number of local variables of the function.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!

        # Update current function name for future labels/goto commands
        self.cur_function = function_name

        # (function_name) = Write the function entry label
        self.write_line(f"({function_name})")

        # Initialize local variables to 0
        # repeat n_vars times (NUMBER OF LOCAL VARS):
        for i in range(n_vars):
            self.write_push_pop("C_PUSH", "constant", 0)

    def write_call(self, function_name: str, n_args: int) -> None:
        """Writes assembly code that affects the call command. 
        Let "Xxx.foo" be a function within the file Xxx.vm.
        The handling of each "call" command within Xxx.foo's code generates and
        injects a symbol "Xxx.foo$ret.i" into the assembly code stream, where
        "i" is a running integer (one such symbol is generated for each "call"
        command within "Xxx.foo").
        This symbol is used to mark the return address within the caller's 
        code. In the subsequent assembly process, the assembler translates this
        symbol into the physical memory address of the command immediately
        following the "call" command.

        Args:
            function_name (str): the name of the function to call.
            n_args (int): the number of arguments of the function.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!

        # The pseudo-code of "call function_name n_args" is:
        # push return_address   // generates a label and pushes it to the stack

        # 1. Push return address (Using D=A because it's a label/constant)
        return_label = f"{self.filename}$ret.{self.label_counter}"
        self.label_counter += 1

        self.write_line([
                            f"@{return_label}",
                            "D=A"] +  # Load the address number into D
                        PUSH  # Push D to stack
                        )

        # 2. Push LCL, ARG, THIS, THAT (Using D=M because we want the stored value)
        for segment in ["LCL", "ARG", "THIS", "THAT"]:
            self.write_line([
                                f"@{segment}",
                                "D=M"] +  # Load the value stored in the register into D
                            PUSH  # Push D to stack
                            )

        # ARG = SP-5-n_args     // repositions ARG
        self.write_line([f"@{n_args}", "D=A", "@5", "D=A+D", "@SP", "D=M-D", "@ARG", "M=D"])
        # LCL = SP              // repositions LCL
        self.write_line(["@SP", "D=M", "@LCL", "M=D"])

        # goto function_name    // transfers control to the callee
        self.write_line([f"@{function_name}", "0;JMP"])

        # (return_address)      // injects the return address label into the code
        self.write_line(f"({return_label})")

    def write_return(self) -> None:
        """Writes assembly code that affects the return command."""
        # This is irrelevant for project 7,
        # you will implement this in project 8!

        # frame = LCL                   // frame is a temporary variable
        self.write_line(["@LCL",
                         "D=M",
                         "@frame",
                         "M=D"])

        # return_address = *(frame-5)   // puts the return address in a temp var
        self.write_line(["@5", "D=A", "@frame", "A=M", "A=A-D", "D=M", "@return_address", "M=D"])

        # *ARG = pop()                  // repositions the return value for the caller
        self.write_line(["@SP", "M=M-1", "A=M", "D=M", "@ARG", "A=M", "M=D"])

        # SP = ARG + 1                  // repositions SP for the caller
        self.write_line(["@ARG", "D=M", "@SP", "M=D+1"])

        # # THAT = *(frame-1)             // restores THAT for the caller
        # # THIS = *(frame-2)             // restores THIS for the caller
        # # ARG = *(frame-3)              // restores ARG for the caller
        # # LCL = *(frame-4)              // restores LCL for the caller
        indexes = [1, 2, 3, 4]
        locations = ["THAT", "THIS", "ARG", "LCL"]
        for index, location in zip(indexes, locations):
            self.write_line(["@frame", "D=M", f"@{index}", "A=D-A", "D=M", f"@{location}", "M=D"])

        # goto return_address           // go to the return address
        self.write_line(["@return_address", "A=M", "0;JMP"])

        # # 1. FRAME = LCL (Save LCL to R13)
        # self.write_line(["@LCL", "D=M", "@R13", "M=D"])
        #
        # # 2. RET = *(FRAME - 5) (Save return address to R14)
        # self.write_line([
        #     "@R13",
        #     "D=M",  # D = FRAME
        #     "@5",
        #     "A=D-A",  # A = FRAME - 5
        #     "D=M",  # D = *(FRAME - 5)
        #     "@R14",
        #     "M=D"  # RET = D
        # ])
        #
        # # 3. *ARG = pop() (Reposition return value for the caller)
        # self.write_line(["@SP", "M=M-1", "A=M", "D=M", "@ARG", "A=M", "M=D"])
        #
        # # 4. SP = ARG + 1 (Reposition SP for the caller)
        # self.write_line(["@ARG", "D=M", "@SP", "M=D+1"])
        #
        # # 5. Restore THAT, THIS, ARG, LCL from FRAME
        # # We loop to restore segments: THAT=*(FRAME-1), THIS=*(FRAME-2), etc.
        # shifts = [1, 2, 3, 4]
        # segments = ["THAT", "THIS", "ARG", "LCL"]
        # for shift, segment in zip(shifts, segments):
        #     self.write_line([
        #         "@R13", "D=M",  # D = FRAME
        #         f"@{shift}", "A=D-A",  # A = FRAME - shift
        #         "D=M",  # D = value at (FRAME - shift)
        #         f"@{segment}", "M=D"  # Restore the segment pointer
        #     ])
        #
        # # 6. goto RET (Jump to the return address stored in R14)
        # self.write_line(["@R14", "A=M", "0;JMP"])
