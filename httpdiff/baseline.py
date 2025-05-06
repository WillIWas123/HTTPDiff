from .blob import Blob, Item, ResponseTimeBlob
import urllib.parse


class Baseline:
    """
    Baseline is the main class for this library.
    """

    def __init__(self,custom_baseline=None,custom_blob=None,custom_item=None):
        """
        A Blob object is created for each area of bytes.

        """
        self.custom_baseline = custom_baseline() if custom_baseline else None
        self.custom_blob = custom_blob
        self.custom_item = custom_item
        self.analyze_all = False
        self.body_length_only = False
        self.error_items = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.response_time_item = ResponseTimeBlob(custom_blob=custom_blob,custom_item=custom_item)
        self.status_code_item = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.reason_items = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.header_items = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.body_items = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.body_length_item = Blob(custom_blob=custom_blob,custom_item=custom_item)

        self.redir_body_length_only = False
        self.redir_status_code_item = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.redir_reason_items = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.redir_header_items = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.redir_body_items = Blob(custom_blob=custom_blob,custom_item=custom_item)
        self.redir_body_length_item = Blob(custom_blob=custom_blob,custom_item=custom_item)

    # TODO: implement later
    def set_response(self, response, response_time, error, payload):
        """
        To be used for setting a new first response. Can be useful if you'd like to reset the calibration, etc.
        """
        pass

    def add_response(self, response, response_time=0, error=b"", payload=None):
        """
        add_response adds another response to the baseline while calibrating.
        each Blob object gets more data appended to it.
        """
        if self.custom_baseline:
            self.custom_baseline.add_response(response, response_time, error, payload)
        if response == None:
            self.error_items.add_line(error)
            self.response_time_item.add_line(response_time)
            return
        if len(response.history) > 0:
            self.redir_status_code_item.add_line(str(response.history[0].status_code).encode())
            self.redir_reason_items.add_line(response.history[0].reason,payload)
            self.redir_header_items.add_line(response.history[0].headers,payload)
            self.redir_body_items.add_line(response.history[0].content,payload)
            self.redir_body_length_item.add_line(str(len(response.history[0].content)).encode())
        else:
            self.redir_status_code_item.add_line(b"-1")
            self.redir_reason_items.add_line(b"")
            self.redir_header_items.add_line(b"")
            self.redir_body_items.add_line(b"")
            self.redir_body_length_item.add_line(b"-1")

        self.status_code_item.add_line(str(response.status_code).encode())
        self.reason_items.add_line(response.reason,payload)
        self.header_items.add_line(response.headers,payload)
        self.body_items.add_line(response.content,payload)
        self.body_length_item.add_line(str(len(response.content)).encode())
        self.response_time_item.add_line(response_time)
        self.error_items.add_line(error,payload)


    def find_diffs(self, response, response_time=0, error=b"", payload=""):
        """
        find_diffs checks if there's a difference between the baseline and the new response

        All sections of the response is checked for differences and yielded as found

        Note: payload is inputted as part of the arguments mainly to be used in custom_baseline, in case you'd like to look out of reflection etc.
        """
        if self.custom_baseline:
            yield from self.custom_baseline.find_diffs(response, response_time, error, payload)
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
            if (
                self.analyze_all is False
                and len(self.redir_body_length_item.item.lines) == 1
                and next(iter(self.redir_body_length_item.item.lines)) > 2000
            ):
                if self.redir_body_length_only is False:
                    self.redir_body_length_only = True
            elif self.redir_body_length_only is True:
                self.redir_body_length_only = False
            if self.redir_body_length_only is False:
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
        if (
            self.analyze_all is False
            and len(self.body_length_item.item.lines) == 1
            and next(iter(self.body_length_item.item.lines)) > 2000
        ):
            if self.body_length_only is False:
                self.body_length_only = True
        elif self.body_length_only is True:
            self.body_length_only = False
        if self.body_length_only is False:
            if out := self.body_items.find_diffs(response.content):
                yield {"section":"body","diffs":out}
        else:
            if out := self.body_length_item.find_diffs(str(len(response.content)).encode()):
                yield {"section":"body","diffs":out}
        if out := self.header_items.find_diffs(response.headers):
            yield {"section":"headers","diffs":out}
        if out := self.response_time_item.find_diffs(response_time):
            yield {"section":"response_time","diffs":out}
        if out := self.error_items.find_diffs(error):
            yield {"section":"error","diffs":out}
        return
