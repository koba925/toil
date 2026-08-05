import os
import re

dirs = [
    "0302_compiler", "0303_ici", "0304_pseudo_func", "0305_seq",
    "0306_var", "0307_assignment_scope", "0308_if", "0309_while",
    "0310_builtin_functions", "0311_user_functions", "0312_examples",
    "0401_ident"
]

pattern = re.compile(
r"""    def tokenize\(self\):
        while True:
            while self._current_char\(\)\.isspace\(\): self._advance\(\)

            if self._current_char\(\) == "#":
                while self._current_char\(\) not in \("\\n", "\$EOF"\):
                    self._advance\(\)
                continue

            self._start_pos = self._current_pos
            match self._current_char\(\):
                case "\$EOF":
                    self._tokens\.append\((?:Ident\("\$EOF"\)|"\$EOF")\)
                    break
                case c if c\.isdecimal\(\): self._number\(\)
                case c if is_ident_first\(c\): self._ident\(\)
                case c if c in "=:":
                    self._advance\(\)
                    if self._current_char\(\) == "=": self._advance\(\)
                    self._tokens\.append\(self._lexeme\(\)\)
                case c if c in "\+\-\*/%\(\)<>,;":
                    self._tokens\.append\(c\); self._advance\(\)
                case invalid:
                    assert False, f"Invalid character @ tokenize\(\): \{invalid\}"

        return self._tokens
"""
)

for d in dirs:
    path = f"book/{d}/toil.py"
    if not os.path.exists(path): continue
    content = open(path).read()
    if pattern.search(content):
        print(f"Match found in {d}")
    else:
        print(f"No match in {d}")
