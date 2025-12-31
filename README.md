
# Hack VM Translator

A Python implementation of a **VM-to-Hack assembly translator** for the Hack platform. This project translates high-level Virtual Machine intermediate code into Hack Assembly language, supporting stack arithmetic, memory access, program flow, and full function calling conventions.

> **Coursework Project** > **Course:** Computer Cons. Workshop: From Nand to Tetris

> **Institution:** The Hebrew University of Jerusalem  
> **Authors:** Amit Tzur & Zohar Mattatia  

---

## 🚀 Features & Supported Commands

The translator fully supports the VM specification defined in the Nand2Tetris course (Projects 7 & 8).

### 1. Arithmetic / Logical
Handles stack-based arithmetic and logical operations:
* `add`, `sub`, `neg`
* `eq`, `gt`, `lt`
* `and`, `or`, `not`

### 2. Memory Access
Implements `push` and `pop` operations for the following memory segments:
* `constant`
* `local`, `argument`, `this`, `that`
* `temp`, `pointer`, `static`

### 3. Program Flow Control
* `label`: Label declaration.
* `goto`: Unconditional branching.
* `if-goto`: Conditional branching (based on stack top).

### 4. Function Calling Convention
* `function`: Function declaration.
* `call`: Function invocation (saves caller frame).
* `return`: Return to caller.

---

## 🛠️ Implementation Details

* **Bootstrap Code:** When required (parsing a directory), the translator emits bootstrap initialization code that sets `SP=256` and calls `Sys.init`.
* **Static Variables:** Static variables are mapped strictly as `FileName.index` to ensure file-level scoping.
* **Label Scoping:** Labels inside functions are generated with unique identifiers to prevent collisions between functions.
* **Standard Convention:** The implementation follows the standard Hack platform calling convention (saving `LCL`, `ARG`, `THIS`, `THAT` to the stack).

---

## 💻 How to Run

Ensure you have **Python 3** installed.

### 1. Translate a Single File
To translate a specific `.vm` file into a `.asm` file:
```bash
python3 Main.py path/to/File.vm
1. Translate a Single File
python3 Main.py path/to/File.vm
```
2. Translate a Directory
To translate all .vm files in a directory (and add bootstrap code):

```Bash
python3 Main.py path/to/Directory/
```
Output: The translator creates a single .asm file named after the input file or directory (e.g., Directory.asm) in the same location.

## 📂 Project Structure
```Plaintext
.
├── Makefile            # Execution script (if applicable)
├── Main.py             # Entry point / Driver code
├── Parser.py           # Handles file reading and command parsing
├── CodeWriter.py       # Generates Hack Assembly code
├── VMtranslator/       # Wrapper (optional)
└── README.md           # Project documentation
```

## 📄 License
MIT License
