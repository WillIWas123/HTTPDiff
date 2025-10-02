from rapidfuzz.distance.Indel import opcodes
from threading import Lock
import re
import statistics


DISABLED = -2
UNINITIALIZED = -1


class Diff:
    """
    Diff is a class used to store one diff between two responses.
    This is used to make it easy to determine if two diffs are different or the same.
    The Item is added for later for verifying if the same items are used within two diffs
    """

    def __init__(self, item,message):
        self.item=item
        self.message = message

    def __eq__(self, diff):
        """
        If the Diff originates from the same item, then it is very likely the same difference occurring in two responses
        """
        return self.item == diff.item

    def __repr__(self):
        return self.message


class Item:
    """
    Items store the index to the static string within original_line
    """

    def __init__(self, l1,l2, initialized=True):
        self.original_l1 = l1
        self.l1 = l1
        self.original_l2 = l2
        self.l2 = l2
        self.initialized = initialized
        self.length = UNINITIALIZED

    def __repr__(self):
        return f"({self.l1}, {self.l2})"


class Blob:
    """
    Blob is a collection of Items, one Blob object is typically used for one area of bytes, such as a response body or response headers.
    """

    def __init__(self, line=None):
        self.lock = Lock()
        self.equal_items = []
        self.original_line = line
        self.insert_items = {}

    def add_line(self, line, payload=None):
        """
        Takes a new line, updates indexes for Items, and removes strings that turned out to be dynamic after all
        """
        self.lock.acquire()
        if not self.original_line:
            if payload:
                line = line.replace(payload.encode(),b"") # Removing reflection during calibration to make stuff simpler
            self.original_line = line
            self.lock.release()
            return

        diff = opcodes(self.original_line, line)
        equal_items_exists = True if self.equal_items else False
        equal_found = []
        insert_found = []
        new_equal_items = []
        item_l1, item_l2, item_r1, item_r2= None, None, None, None
        for opcode, l1,l2,r1,r2 in diff:

            item_found = False

            if opcode == "equal":
                if not equal_items_exists: # self.equal_items is not populated in advance
                    self.equal_items.append(Item(l1,l2))
                    continue
                remove = []
                for item in self.equal_items:
                    item.initialized=True

                    if item.l1 == item.l2: # If l1 and l2 are equal it means the string is empty
                        remove.append(item)
                        continue

                    if l1 > item.l2 or l2 < item.l1:
                        continue

                    if l1 < item.l2 and l2 > item.l1:
                        item_found = True
                        equal_found.append(item)

                    if l2 < item.l2 and l2 > item.l1:
                        new_item = Item(l2+1,item.l2,initialized=False)
                        new_equal_items.append(new_item)
                        item.l2 = l2
                    if l1 > item.l1 and l1 < item.l2: 
                        item.l1 = l1
                for item in remove:
                    self.equal_items.remove(item)

            # Code below should find the dynamic strings between the static items
            if item_found is False:
                if item_l1 is None:
                    item_l1 = l1
                    item_r1 = r1
                item_l2 = l2
                item_r2 = r2
            elif item_found is True and item_l1 is not None:
                equal_item = equal_found[-1]
                if self.insert_items.get(equal_item) is None:
                    self.insert_items[equal_item] = Item(item_l1,item_l2)
                insert_item = self.insert_items[equal_item]
                if insert_item.length != DISABLED and item_l1 != insert_item.l1: 
                    insert_item.length = UNINITIALIZED
                elif insert_item.length > 0 and item_r2-item_r1 != insert_item.length:
                    insert_item.length = DISABLED # Disabling length checks
                elif insert_item.length == UNINITIALIZED:
                    insert_item.length = item_r2-item_r1

                insert_item.l1 = item_l1
                insert_item.l2 = item_l2
                insert_found.append(insert_item)

                item_l1, item_l2, item_r1, item_r2 = None, None, None, None


        if equal_items_exists:
            remove = []
            for item in self.equal_items:
                if item not in equal_found:
                    remove.append(item)
            for item in remove:
                self.equal_items.remove(item)
            for item in reversed(insert_found):
                # Removing all dynamic text from self.original_line
                if item.l1 == item.l2:
                    continue
                self.original_line = self.original_line[:item.l1] + self.original_line[item.l2:]
                    
                    
        for item in new_equal_items:
            self.equal_items.append(item)

        self.lock.release()

    def is_equal_after_all(self, line, r1, r2, item):
        text = self.original_line[item.l1:item.l2]
        text2 = line[r1:r2]
        index = 0
        while True:
            index = text.find(text2,index)
            if index < 0:
                return False
            lower = r1-index
            upper = lower+(item.l2-item.l1)
            if text in line[lower:upper]:
                return True
            index+=1
        return False



    def find_diffs(self, line):
        """
        Takes in bytes, checks if the index of known static strings have changed.
        Also checks whether insertions of static lengths change.
        """
        out = []
        diff = opcodes(self.original_line, line)
        equal_found = []
        item_l1, item_l2, item_r1, item_r2 = None, None, None, None
        for opcode, l1,l2,r1,r2 in diff:
            item_found = False
            if opcode == "equal":
                for item in self.equal_items:
                    if item.initialized is False:
                        continue
                    if item in equal_found:
                        continue
                    if l2 < item.l1 or l1 > item.l2: # Not even close
                        continue

                    if l1 <= item.l1 and l2 >= item.l2:
                        equal_found.append(item)
                        item_found = True

                    # Code below exists because of payload reflection
                    if l1 >= item.l1 and l2 <= item.l2:
                        """
                        The Indel algorithm may mess up whenever the payload reflection contains an equal part of a static string in close proximity.
                        """
                        if self.is_equal_after_all(line, r1, r2, item):
                            equal_found.append(item)
                            item_found = True
                            
            if item_found is False:
                if item_l1 is None:
                    item_l1 = l1
                    item_r1 = r1
                item_l2 = l2
                item_r2 = r2
            elif item_found is True and item_l1 is not None:
                equal_item = equal_found[-1]
                if self.insert_items.get(equal_item) is None:
                    self.insert_items[equal_item] = Item(item_l1,item_l2)
                insert_item = self.insert_items[equal_item]

                if insert_item.l1 != item_l1:
                    out.append(Diff(item, f"Insertion occured at different location: {insert_item.l1} != {item_l1}"))
                if insert_item.length > 0 and insert_item.length != item_r2-item_r1:
                    out.append(Diff(item, f"Length of insertion changed: {insert_item.length} != {r2-r1}"))

                item_l1, item_l2, item_r1, item_r2 = None, None, None, None



        for item in self.equal_items:
            if item.initialized is False: # Item discovered at last calibration response. Ignoring for now
                continue
            if item not in equal_found:
                out.append(Diff(item, f"Line is no longer present: {self.original_line[item.l1:item.l2]}")) 

        return out



class ResponseTimeBlob(Blob):
    """
    Custom Blob class for analyzing response times.
    """

    def __init__(self, line=None):
        super().__init__(line=line)
        self.std_dev = 0
        self.response_times = []

    def add_line(self, line):
        """
        add another response time.
        """
        self.lock.acquire()
        self.response_times.append(line)
        if len(self.response_times) > 1:
            self.std_dev = statistics.stdev(self.response_times)
        self.lock.release()

    def find_diffs(self, line):
        """
        checks whether the new response time is significantly higher or lower than the normal
        """
        out = []
        if len(self.response_times) == 0:
            return out
        lower = min(self.response_times) - 7 * self.std_dev
        upper = max(self.response_times) + 7 * self.std_dev
        if line < lower:
            out.append(Diff(1,f"Item is suddenly lower than usual: {line} < {min(self.response_times)}"))
        if line > upper:
            out.append(Diff(2,f"Item is suddenly higher than usual: {line} > {max(self.response_times)}"))
        return out
