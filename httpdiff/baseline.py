from .blob import Blob, ResponseTimeBlob
import urllib.parse


class Baseline:
    """
    Baseline is the main class for this library.
    """

    def __init__(self):
        """
        A Blob object is created for each area of bytes.

        """
        self.error_items = Blob()
        self.response_time_item = ResponseTimeBlob()
        self.status_code_item = Blob()
        self.reason_items = Blob()
        self.header_items = Blob()
        self.sorted_header_items = Blob()
        self.body_items = Blob()
        self.body_length_item = Blob()

        self.redir_status_code_item = Blob()
        self.redir_reason_items = Blob()
        self.redir_header_items = Blob()
        self.redir_body_items = Blob()
        self.redir_body_length_item = Blob()

    def add_response(self, response, response_time=0, error=b"", payload=None):
        """
        add_response adds another response to the baseline while calibrating.
        each Blob object gets more data appended to it.
        """
        if response == None:
            self.error_items.add_line(error)
            self.response_time_item.add_line(response_time)
            return
        if len(response.history) > 0:
            self.redir_status_code_item.add_line(str(response.history[0].status_code).encode(),payload)
            self.redir_reason_items.add_line(response.history[0].reason,payload)
            self.redir_header_items.add_line(response.history[0].headers,payload)
            self.redir_body_items.add_line(response.history[0].content,payoad)
            self.redir_body_length_item.add_line(str(len(response.history[0].content)).encode(),payload)
        else:
            self.redir_status_code_item.add_line(b"-1")
            self.redir_reason_items.add_line(b"")
            self.redir_header_items.add_line(b"")
            self.redir_body_items.add_line(b"")
            self.redir_body_length_item.add_line(b"-1")

        self.status_code_item.add_line(str(response.status_code).encode(),payload)
        self.reason_items.add_line(response.reason,payload)
        self.header_items.add_line(response.headers,payload)
        self.sorted_header_items.add_line(response.sorted_headers,payload)
        self.body_items.add_line(response.content,payload)
        self.body_length_item.add_line(str(len(response.content)).encode(),payload)
        self.response_time_item.add_line(response_time)
        self.error_items.add_line(error,payload)

    def find_diffs(self, response, response_time=0, error=b""):
        """
        find_diffs checks if there's a difference between the baseline and the new response

        All sections of the response is checked for differences and yielded as found

        """
        if response == None:
            if out := self.error_items.find_diffs(error):
                yield {"section": "error", "diffs":out}
            if out := self.response_time_item.find_diffs(response_time):
                yield {"section":"error","diffs":out}
            return
        if len(response.history) > 0:
            if out := self.redir_status_code_item.find_diffs(str(response.history[0].status_code).encode()):
                yield {"section":"status_code","diffs":out}
            if out := self.redir_reason_items.find_diffs(response.history[0].reason):
                yield {"section":"reason","diffs":out}
            if out := self.redir_body_items.find_diffs(response.history[0].content):
                yield {"section":"body","diffs":out}
            else:
                if out := self.redir_body_length_item.find_diffs(str(len(response.history[0].content)).encode()):
                    yield {"section":"body","diffs":out}
            if out := self.redir_header_items.find_diffs(response.history[0].headers):
                yield {"section":"headers","diffs":out}
        else:
            if out := self.redir_status_code_item.find_diffs(b"-1"):
                yield {"section":"status_code","diffs":out}
            if out := self.redir_reason_items.find_diffs(b""):
                yield {"section":"reason","diffs":out}
            if out := self.redir_body_items.find_diffs(b""):
                yield {"section":"body","diffs":out}
            if out := self.redir_body_length_item.find_diffs(b"-1"):
                yield {"section":"body","diffs":out}
            if out := self.redir_header_items.find_diffs(b""):
                yield {"section":"headers","diffs":out}
        if out := self.status_code_item.find_diffs(str(response.status_code).encode()):
            yield {"section":"status_code","diffs":out}
        if out := self.reason_items.find_diffs(response.reason):
            yield {"section":"reason","diffs":out}
        if out := self.body_items.find_diffs(response.content):
            yield {"section":"body","diffs":out}
        if out := self.header_items.find_diffs(response.headers):
            yield {"section":"headers","diffs":out}
        if out := self.sorted_header_items.find_diffs(response.sorted_headers):
            yield {"section":"sorted_headers","diffs":out}
        if out := self.response_time_item.find_diffs(response_time):
            yield {"section":"response_time","diffs":out}
        if out := self.error_items.find_diffs(error):
            yield {"section":"error","diffs":out}
        return
