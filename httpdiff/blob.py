from rapidfuzz.distance.Levenshtein import opcodes
from threading import Lock
import re
import statistics


class Diff:
    """
    Diff is a class used to store one diff between two responses.
    This is used to make it easy to determine if two diffs are different or the same.
    The Item is added for later for verifying if the same items are used within two diffs
    The opcode is added to determine that the same operation was made on the same Item.
    """

    def __init__(self, opcode, item, message):
        self.opcode = opcode
        self.message = message
        self.item = item

    def __eq__(self, diff):
        """
        If the Diff originates from the same item, then it is very likely the same difference occuring in two responses
        """
        return self.opcode == diff.opcode and self.item == diff.item

    def __repr__(self):
        return f"{self.message}"


class Item:
    """
    Item is responsible for storing the normal behavior of a small part of the response and to check if there are any differences.
    """

    Static = 1
    Length = 2
    Anything = 3
    Integer = 4
    Range = 5

    def __init__(self, line=None):
        """
        analyze_methods is a set of properties that does not change for an item.
        lines contains all the bytes/strings seen in the same location of the Blob
        """
        self.std_dev = 0
        self.analyze_methods = set()
        self.lines = set()
        self.range = []
        self.lock = Lock()
        if line is None:
            return
        self.lines.add(line)

    def custom_add(self, line):
        # TODO: make it easier to create custom functions
        """
        used for specifying custom properties to an item during calibration. E.g.:

        class CustomItem(Item):
            def custom_add(self,line):
                if "42" in line:
                    self.analyze_methods.add(100)

            def custom_is_diff(self,opcode,line):
                out=[]
                if 5 not in self.analyze_methods:
                    return out
                if "42" not in line:
                    out.append(Diff(opcode,self,f"New line does not include 42! {line}"))
                return out
        """
        return

    def add_line(self, line):
        """
        adds line to self.lines and checks the unchanged properties of all lines.
        """
        self.lock.acquire()
        self.custom_add(line)
        self.lines.add(line)
        if Item.Range in self.analyze_methods:
            # Only expecting response time here for now
            try:
                lines = [int(i.strip()) for i in self.lines]
                self.std_dev = statistics.stdev(lines)
            except Exception:
                pass
            self.lock.release()
            return
        analyze_methods = set()
        if len(self.lines) == 1:
            analyze_methods.add(Item.Static)
        elif all(len(i) == len(next(iter(self.lines))) for i in self.lines):
            analyze_methods.add(Item.Length)
        elif all(len(i) > 0 for i in self.lines):
            analyze_methods.add(Item.Anything)
        if all(i.strip().isdigit() is True for i in self.lines):
            analyze_methods.add(Item.Integer)

        self.analyze_methods = analyze_methods
        self.lock.release()

    def custom_is_diff(self, opcode, line):
        # TODO: make it easier to create custom functions
        """
        used for creating a custom diff function. E.g.:

        class CustomItem(Item):
            def custom_add(self,line):
                if "42" in line:
                    self.analyze_methods.add(5)

            def custom_is_diff(self,opcode,line):
                out=[]
                if 5 not in self.analyze_methods:
                    return out
                if "42" not in line:
                    out.append(Diff(opcode,self,f"New line does not include 42! {line}"))
                return out
        """

        return []

    def is_diff(self, opcode, line):
        """
        checks if new line behaves different from calibrated behavior
        """
        out = self.custom_is_diff(opcode, line)
        if len(self.analyze_methods) == 0:
            return out
        if len(self.lines) == 0:
            out.append(Diff(opcode, self, f'Item different: None != "{line}"'))
        if Item.Static in self.analyze_methods and line != next(iter(self.lines)):
            out.append(Diff(opcode, self, f'Item different: "{next(iter(self.lines))}" != "{line}"'))
        if Item.Length in self.analyze_methods and len(line) != len(next(iter(self.lines))):
            out.append(Diff(opcode, self, f'Item length different: len("{next(iter(self.lines))}") != len("{line}")'))
        if Item.Anything in self.analyze_methods and not line:
            out.append(Diff(opcode, self, f"Item is suddenly empty: {next(iter(self.lines))} - {line}"))
        if Item.Integer in self.analyze_methods and line.strip().isdigit() is False:
            out.append(Diff(opcode, self, f"Item is suddenly not an integer: {line}"))
        if Item.Range in self.analyze_methods:
            if line.strip().isdigit() is False:
                return out
            try:
                lines = [int(i.strip()) for i in self.lines]
                lower = min(lines) - 7 * self.std_dev
                upper = max(lines) + 7 * self.std_dev
                integer_line = int(line.strip())
            except Exception:
                lines = [0]
                lower = 0
                upper = 0
                integer_line = 0
            if integer_line < lower:
                out.append(Diff(opcode, self, f"Item is suddenly lower than usual: {integer_line} < {min(lines)}"))
            if integer_line > upper:
                # opcode + "2" is to differentiate lower to higher
                out.append(Diff(opcode + "2", self, f"Item is suddenly higher than usual: {integer_line} > {max(lines)}"))

        return out

    def __len__(self):
        return len(self.lines)


class Blob:
    """
    Blob is a collection of Items, one Blob object is typically used for one area of bytes/strings, such as a response body or response headers.
    """

    def __init__(self, line=None):
        """
        items is a dict of all split strings from the given line.
        appended_items are strings that has been inserted after the first response was submitted.
        previous_static_items is starting empty and will be populated if previous static items suddenly change in is_diff.
        """
        self.lock = Lock()
        self.items = {}
        self.compile = r",|\.|\s|;"
        self.appended_items = {}
        self.previous_static_items = {}
        self.original_lines = []
        self.compiled = re.compile(self.compile)
        if line is None:
            self.item = Item()
            return

        self.original_lines = re.split(self.compiled, line)

    def custom_add(self, line):
        # TODO: make it easier to create custom functions
        """
        Used for creating a custom add function for a given line.
        """
        return

    def add_line(self, line):
        """
        Takes bytes or a string as input and splits it up in to multiple Items.
        """
        self.lock.acquire()
        self.custom_add(line)
        if len(self.original_lines) == 0:
            if isinstance(line, bytes) is True:
                self.compile = self.compile.encode()
            self.compiled = re.compile(self.compile)
            self.original_lines = re.split(self.compiled, line)
            self.lock.release()
            return

        lines = re.split(self.compiled, line)

        diff = opcodes(self.original_lines, lines)

        for opcode, l1, l2, r1, r2 in diff:
            if opcode == "insert":
                for j in range(r1, r2):
                    if self.appended_items.get(l1) is None:
                        self.appended_items[l1] = Item(lines[j])
                    self.appended_items[l1].add_line(lines[j])

            elif opcode == "delete":
                for j in range(l1, l2):
                    if self.items.get(j) is None:
                        self.items[j] = Item(self.original_lines[j])
                    self.items[j].add_line("")

            elif opcode == "replace":
                for l, r in zip(range(l1, l2), range(r1, r2)):
                    if self.items.get(l) is None:
                        self.items[l] = Item(self.original_lines[l])
                    self.items[l].add_line(lines[r])
        self.lock.release()

    def custom_is_diff(self, line):
        # TODO: make it easier to create custom functions
        """
        used for creating a custom is_diff function.
        """
        return []

    def is_diff(self, line):
        """
        Takes in bytes or a string, checks if any Item has changed behavior.
        """
        out = self.custom_is_diff(line)

        lines = re.split(self.compiled, line)
        diff = opcodes(self.original_lines, lines)

        for opcode, l1, l2, r1, r2 in diff:
            if opcode == "delete":
                for j in range(l1, l2):
                    if self.items.get(j) is None:
                        self.lock.acquire()
                        if self.previous_static_items.get(j) is None:
                            self.previous_static_items[j] = Item()

                        # opcode+"2" = delete2, used for differentiating the two different cases where a line was deleted
                        out.append(Diff(opcode + "2", self.previous_static_items[j], f'"{self.original_lines[j]}" - ""'))
                        self.lock.release()
                        continue

                    out.extend(self.items[j].is_diff(opcode, ""))

            elif opcode == "insert":
                for j in range(r1, r2):
                    if self.appended_items.get(l1) is None:
                        self.lock.acquire()
                        if self.previous_static_items.get(l1) is None:
                            self.previous_static_items[l1] = Item()

                        # opcode+"2" = insert2, used for differentiating the two different cases where a line was inserted
                        out.append(Diff(opcode + "2", self.previous_static_items[l1], f'"" - "{lines[j]}"'))
                        self.lock.release()
                        continue

                    out.extend(self.appended_items[l1].is_diff(opcode, lines[j]))

            elif opcode == "replace":
                for l, r in zip(range(l1, l2), range(r1, r2)):
                    if self.items.get(l) is None:
                        self.lock.acquire()
                        if self.previous_static_items.get(l) is None:
                            self.previous_static_items[l] = Item()

                        # opcode+"2" = replace2, used for differentiating the two different cases where a line was replaced
                        out.append(
                            Diff(opcode + "2", self.previous_static_items[l], f'"{self.original_lines[l]}" - "{lines[r]}"')
                        )
                        self.lock.release()
                        continue

                    out.extend(self.items[l].is_diff(opcode, lines[r]))
        return out


class ResponseTimeBlob(Blob):
    """
    Custom Blob class for analyzing response times.
    """

    def __init__(self, line=None):
        super().__init__(line=line)
        self.item = Item()
        self.std_dev = 0

    def add_line(self, line):
        """
        adds line to self.item.lines.
        """
        self.lock.acquire()
        self.item.lines.add(line)
        try:
            lines = [int(i.strip()) for i in self.item.lines]
            self.std_dev = statistics.stdev(lines)
        except Exception:
            pass
        self.lock.release()

    def is_diff(self, line):
        """
        checks if new line behaves different from calibrated behavior
        """
        out = []
        if line.strip().isdigit() is False:
            out.append(Diff(0, self, f"Response time is expected to be an integer: {line}"))
            return out
        try:
            lines = [int(i.strip()) for i in self.item.lines]
            lower = min(lines) - 7 * self.std_dev
            upper = max(lines) + 7 * self.std_dev
            integer_line = int(line.strip())
        except Exception:
            return out
        if integer_line < lower:
            out.append(Diff(1, self, f"Item is suddenly lower than usual: {integer_line} < {min(lines)}"))
        if integer_line > upper:
            out.append(Diff(2, self, f"Item is suddenly higher than usual: {integer_line} > {max(lines)}"))
        return out
