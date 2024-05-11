import re
from rapidfuzz.distance.Levenshtein import opcodes


"""
reflection.py is made for removing reflections in responses
"""


def find_common_string_start(string1, string2):
    """
    Finds first common string before the payload in the text.
    only index2 and index4 are really used, which represents the end of the string at each text.
    """
    codes = list(opcodes(string1, string2))
    index1, index2, index3, index4 = -1, -1, -1, -1
    if len(codes) == 0:
        return index1, index2, index3, index4
    length = -1
    for i in range(len(codes), -1, -1):
        opcode, l1, l2, r1, r2 = codes[i - 1]
        if opcode == "equal":
            new_length = l2 - l1
            # TODO: stupid hardcoded number, find something better...
            if new_length > 15:
                return l1, l2, r1, r2
            if new_length > length:
                length = new_length
                index1, index2, index3, index4 = l1, l2, r1, r2
    return index1, index2, index3, index4


def find_common_string_end(string1, string2):
    """
    Finds first common string after the payload in the text.
    only index1 and index3 are really used, which represents the start of the string at each text.
    """
    codes = opcodes(string1, string2)
    index1, index2, index3, index4 = -1, -1, -1, -1
    length = -1
    for opcode, l1, l2, r1, r2 in codes:
        if opcode == "equal":
            new_length = l2 - l1
            # TODO stupid hardcoded number, find something better...
            if new_length > 15:
                return l1, l2, r1, r2
            if new_length > length:
                length = new_length
                index1, index2, index3, index4 = l1, l2, r1, r2
    return index1, index2, index3, index4


def find_common_indexes(text1, start1, end1, text2, start2, end2):
    """
    Finds common string before and after a reflection
    """
    offset = 200
    first1 = start1 - offset
    if first1 < 0:
        first1 = 0
    first2 = start2 - offset
    if first2 < 0:
        first2 = 0
    string1 = text1[first1:start1]
    string2 = text1[first2:start2]
    _, l1, _, r1 = find_common_string_start(string1, string2)
    l1 += first1
    r1 += first2

    last1 = end1 + offset
    if last1 >= len(text1):
        last1 = len(text1) - 1

    last2 = end2 + offset
    if last2 >= len(text2):
        last2 = len(text2) - 1

    string1 = text1[end1:last1]
    string2 = text2[end2:last2]
    l2, _, r2, _ = find_common_string_end(string1, string2)
    l2 += end1
    r2 += end2
    return l1, l2, r1, r2


def remove_reflections_string(text1, text2, payload1, payload2):
    """
    Finds and replaces all reflections in text1 and text2 with "r-e-f-l-e-c-t-i-o-n"
    """
    if isinstance(payload1, str) is False or isinstance(payload2, str) is False:
        return text1, text2
    payload1_strings = re.findall("[A-Za-z0-9]{4,}", payload1)
    payload2_strings = re.findall("[A-Za-z0-9]{4,}", payload2)
    replace = "r-e-f-l-e-c-t-i-o-n"
    if isinstance(text1, bytes):
        payload1_strings = [i.encode() for i in payload1_strings]
        payload2_strings = [i.encode() for i in payload2_strings]
        replace = replace.encode()

    c = 0
    while True:
        if c > 1000:
            break
        start1, end1 = find_index(text1, payload1_strings)
        start2, end2 = find_index(text2, payload2_strings)
        if start1 == -1 or start2 == -1 or end1 == -1 or end2 == -1:
            break
        l1, l2, r1, r2 = find_common_indexes(text1, start1, end1, text2, start2, end2)
        if l1 == -1 or r1 == -1 or l2 == -1 or r2 == -1:
            break
        text1 = text1[:l1] + replace + text1[l2:]
        text2 = text2[:r1] + replace + text2[r2:]
        c += 1

    return text1, text2


def find_index(text, payload_strings):
    """
    Finds parts of the payload in the text. These indexes are further processed to find an exact location.
    """
    c, c2, index, index2, start, end = 0, 0, 0, 0, -1, 0
    while True:
        c2 += 1
        if c2 > 1000:
            start = -1
            end = -1
            break

        if c >= len(payload_strings):
            return start, index2

        string = payload_strings[c]
        new_index = text.find(string, index)
        if c == 1 and payload_strings[0] in text[index + len(payload_strings[0]) : new_index]:
            start = -1
            c = 0
            continue

        elif c > 1 and payload_strings[0] in text[index + len(payload_strings[c - 1]) : new_index]:
            end = index + len(payload_strings[c - 1])
            break
        index = new_index
        index2 = index + len(string)
        if index == -1 or index2 == -1:
            break
        if start == -1:
            start = index
            if start != 0:
                start -= 1
        index += len(string)
        c += 1
    return start, end


def remove_reflection(response1, response2, payload1, payload2):
    """
    Removes all reflections from two responses, note that two responses and two payloads are needed to make this work.
    If you'd like to remove reflection from a single respones, use a dummy payload or a response from the calibration phase as a second one.
    """
    if response1 == None or response2 == None:
        return response1, response2
    headers1, headers2 = remove_reflections_string(response1.headers, response2.headers, payload1, payload2)
    response1.headers = headers1
    response2.headers = headers2

    content1, content2 = remove_reflections_string(response1.content, response2.content, payload1, payload2)
    response1.content = content1
    response2.content = content2

    reason1, reason2 = remove_reflections_string(response1.reason, response2.reason, payload1, payload2)
    response1.reason = reason1
    response2.reason = reason2
    return response1, response2
