class Response:
    # TODO: consider adding support for other libraries than requests
    """
    An object to make processing of responses a bit easier.
    Takes in a Response object from the requests library and stores the wanted values in a easy to use manner.
    """

    def __init__(self, response):
        self.none = False
        if response is None:
            self.none = True
            return
        self.history = []
        if len(response.history) > 0:
            self.history = [Response(response.history[0])]
        self.status_code = response.status_code
        self.reason = response.reason.encode()
        self.content = response.content
        self.headers = ""
        self.sorted_headers = ""
        self.request=response.request
        for i in response.headers:
            self.headers += f"{i}: {response.headers[i]}\n"
        self.headers=self.headers.encode()

        for k in sorted(response.headers.keys()): # Sorted headers can be useful when headers keep changing locations
            self.sorted_headers += f"{k}: {response.headers[k]}\n"
        self.sorted_headers=self.sorted_headers.encode()

    def __eq__(self, item):
        if self.none is True and item is None:
            return True
        return False
