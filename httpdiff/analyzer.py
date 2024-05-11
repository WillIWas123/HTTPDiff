from .blob import Blob, Item, ResponseTimeBlob

import urllib.parse
import datetime


class Analyzer:
    """
    Analyzer is the main class for this library.
    """

    def __init__(self):
        """
        A Blob object is created for each area of bytes/strings.

        """
        self.analyze_all = False
        self.verbose = False
        self.error_items = Blob()
        self.response_time_item = ResponseTimeBlob()
        self.body_length_only = False
        self.status_code_item = Blob()
        self.reason_items = Blob()
        self.header_items = Blob()
        self.body_items = Blob()
        self.body_length_item = Blob()

        self.redir_body_length_only = False
        self.redir_status_code_item = Blob()
        self.redir_reason_items = Blob()
        self.redir_header_items = Blob()
        self.redir_body_items = Blob()
        self.redir_body_length_item = Blob()

    # TODO: implement later
    def set_response(self, response, response_time, error, payload):
        """
        To be used for setting a new first response. Can be useful if you'd like to reset the calibration, etc.
        """
        pass

    def custom_add_response(self, response, response_time, error, payload):
        """
        custom_add_response is made for being overwritten by a custom Analyzer object.
        If you want to create your own checks while calibrating, change this function in a custom object. E.g.:

        class CustomAnalyzer(Analyzer):
            def __init__(self):
                super().__init__()
                self.my_items = Blob()

            def custom_add_response(self,response,response_time,error,payload):
                if response_time > 10:
                    self.my_items.add_line("slow")
                else:
                    self.my_items.add_line("fast")

            def custom_is_diff(self,response,response_time,error,payload):
                diffs = []
                if response_time > 10:
                    yield self.my_items.is_diff("slow")
                else:
                    yield self.my_items.is_diff("fast")
        """
        return

    def add_response(self, response, response_time="0", error="", payload=""):
        """
        add_response adds another response to the baseline while calibrating.
        each Blob object gets more data appended to it.
        """
        self.custom_add_response(response, response_time, error, payload)
        if response == None:
            self.error_items.add_line(error)
            self.response_time_item.add_line(str(response_time))
            return
        if len(response.history) > 0:
            self.redir_status_code_item.add_line(str(response.history[0].status_code))
            self.redir_reason_items.add_line(response.history[0].reason)
            self.redir_header_items.add_line(response.history[0].headers)
            self.redir_body_items.add_line(response.history[0].content)
            self.redir_body_length_item.add_line(str(len(response.history[0].content)))
        else:
            self.redir_status_code_item.add_line("-1")
            self.redir_reason_items.add_line("")
            self.redir_header_items.add_line("")
            self.redir_body_items.add_line(b"")
            self.redir_body_length_item.add_line("-1")

        self.status_code_item.add_line(str(response.status_code))
        self.reason_items.add_line(response.reason)
        self.header_items.add_line(response.headers)
        self.body_items.add_line(response.content)
        self.body_length_item.add_line(str(len(response.content)))
        self.response_time_item.add_line(str(response_time))
        self.error_items.add_line(error)

    def custom_is_diff(self, response, response_time, error, payload):
        """
        custom_is_diff is made for being overwritten by a custom Analyzer object.
        If you want to create your diff checks, change this function in a custom object. E.g.:

        class CustomAnalyzer(Analyzer):
            def __init__(self):
                super().__init__()
                self.my_items = Blob()

            def custom_add_response(self,response,response_time,error,payload):
                if response_time > 10:
                    self.my_items.add_line("slow")
                else:
                    self.my_items.add_line("fast")


            custom_is_diff(self,response,response_time,error,payload):
                if response_time > 10:
                    yield self.my_items.is_diff("slow")
                else:
                    yield self.my_items.is_diff("fast")
        """
        pass

    def is_diff(self, response, response_time="0", error="", payload=""):
        """
        is_diff checks if there's a difference between the baseline and the new response

        All parts of the response is checked for differences and yielded as found

        Note: payload is inputted as part of the arguments mainly to be used in custom_is_diff, in case you'd like to look out of reflection etc.
        """
        try:
            yield from self.custom_is_diff(response, response_time, error, payload)
        except Exception:
            pass
        if response == None:
            if out := self.error_items.is_diff(error):
                yield out
            if out := self.response_time_item.is_diff(str(response_time)):
                yield out
            return
        if len(response.history) > 0:
            if out := self.redir_status_code_item.is_diff(str(response.history[0].status_code)):
                yield out
            if out := self.redir_reason_items.is_diff(response.history[0].reason):
                yield out
            if (
                self.analyze_all is False
                and len(self.redir_body_length_item.item.lines) == 1
                and next(iter(self.redir_body_length_item.item.lines)) > 2000
            ):
                if self.redir_body_length_only is False:
                    if self.verbose is True:
                        print("[INFO] Only analyzing redirection body length")
                    self.redir_body_length_only = True
            elif self.redir_body_length_only is True:
                if self.verbose is True:
                    print("[INFO] Reverting to analyzing full redirection body!")
                self.redir_body_length_only = False
            if self.redir_body_length_only is False:
                if out := self.redir_body_items.is_diff(response.history[0].content):
                    yield out
            else:
                if out := self.redir_body_length_item.is_diff(str(len(response.history[0].content))):
                    yield out
            if out := self.redir_header_items.is_diff(response.history[0].headers):
                yield out
        else:
            if out := self.redir_status_code_item.is_diff("-1"):
                yield out
            if out := self.redir_reason_items.is_diff(""):
                yield out
            if out := self.redir_body_items.is_diff(b""):
                yield out
            if out := self.redir_body_length_item.is_diff("-1"):
                yield out
            if out := self.redir_header_items.is_diff(""):
                yield out
        if out := self.status_code_item.is_diff(str(response.status_code)):
            yield out
        if out := self.reason_items.is_diff(response.reason):
            yield out
        if (
            self.analyze_all is False
            and len(self.body_length_item.item.lines) == 1
            and next(iter(self.body_length_item.item.lines)) > 2000
        ):
            if self.body_length_only is False:
                if self.verbose is True:
                    print("[INFO] Only analyzing body length")
                self.body_length_only = True
        elif self.body_length_only is True:
            if self.verbose is True:
                print("[INFO] Reverting to analyzing full body!")
            self.body_length_only = False
        if self.body_length_only is False:
            if out := self.body_items.is_diff(response.content):
                yield out
        else:
            if out := self.body_length_item.is_diff(str(len(response.content))):
                yield out
        if out := self.header_items.is_diff(response.headers):
            yield out
        if out := self.response_time_item.is_diff(str(response_time)):
            yield out
        if out := self.error_items.is_diff(error):
            yield out
        return
