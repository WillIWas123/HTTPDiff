# This file is not in use, this is simply a few examples of how it is possible to create custom diffs

from httpdiff import Diff, Item
class CustomBaseline:
    def __init__(self):
        self.number_count = set()

    def add_response(self, response, response_time=0, error=b"", payload=""):
        self.number_count.add(response.content.count(b"9801"))

    def find_diffs(self, response, response_time, error, payload):
        out = []
        if len(self.number_count) != 1:
            return
        number_count = response.content.count(b"9801")
        if number_count != list(self.number_count)[0]:
            out.append(Diff("", None, f"Number count changed {list(self.number_count)[0]} - {number_count}"))
            yield {"section": "custom_count", "diffs":out}

class CustomBlob:
    def __init__(self):
        self.item = Item()

    def add_line(self,line,payload=None):
        # line = full section of HTTP response
        self.item.add_line(str(line.count(b"9801")))

    def find_diffs(self,line):
        return self.item.find_diffs("",str(line.count(b"9801")))


class CustomItem:
    def __init__(self):
        self.lines = set()

    def add_line(self, line):
        # line = small part of section of HTTP response
        # Only non-static and non-reflected strings get here
        if b"9801" in line:
            self.lines.add(line)

    def find_diffs(self, opcode, line):
        out = []
        if len(self.lines) > 0 and b"9801" not in line:
            out.append(Diff(opcode, self, '9801 is missing!'))
        elif len(self.lines) == 0 and b"9801" in line:
            out.append(Diff(opcode, self, '9801 is suddenly present!'))
        return out
