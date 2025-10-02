# HTTPDiff

A library written for finding differences between HTTP responses.

- [Disclaimer](https://github.com/WillIWas123/HTTPDiff#disclaimer)
- [About](https://github.com/WillIWas123/HTTPDiff#about)
- [Usecases](https://github.com/WillIWas123/HTTPDiff#usecases)
- [Installation](https://github.com/WillIWas123/HTTPDiff#installation)
- [How it all works](https://github.com/WillIWas123/HTTPDiff#how_it_all_works)
- [Example usage](https://github.com/WillIWas123/HTTPDiff#example-usage)
- [Todo](https://github.com/WillIWas123/HTTPDiff#todo)
- [Tips](https://github.com/WillIWas123/HTTPDiff#tips)

## Disclaimer

- This is considered to be a beta release, and may contain bugs and unintentional behavior. Consider yourself warned!

## About

[HTTPDiff](https://github.com/WillIWas123/HTTPDiff) is a library built for finding differences between responses.

A lot of web pentesting tools suck, using regexes or hardcoded values to determine whether something is different. These methods will produce false-negatives no matter how much you tweak those values. [HTTPDiff](https://github.com/WillIWas123/HTTPDiff) attempts to use a more dynamic way of differentiation responses, attempting to reduce the false-negatives produced during a scan.

By sending multiple requests with a known outcome, it is possible to calibrate a baseline of how the application normally behaves. [HTTPDiff](https://github.com/WillIWas123/HTTPDiff) can then be used to find deviations from the default behavior. [HTTPDiff](https://github.com/WillIWas123/HTTPDiff) will analyze every section of the response; the status code, reason, headers, body, response time, and even errors.


## Usecases

- Want to create a SQL injection scanner? Send a bunch of payloads with random strings for calibration, then send pairs of payloads (e.g. ' or '1'='1 and ' or '1'='2) and check for differences!

- If you want to brute-force endpoints and directories on a web application, you can start by sending a series of requests to known invalid endpoints. The baseline can now be used to determine if any other endpoints behave in a similar way, or are somehow different. Go to [Diffuzz](https://github.com/WillIWas123/Diffuzz) for a good example on how to utilize this library.


## Installation


```python3 -m pip install httpdiff```

## How it all works

Here comes some details of how the library is built, feel free to skip this section if you're not interested:


### Here's the process for calibrating:

1. The add_response function in the Baseline object accepts a Response object as a parameter (among others), multiple Blobs are created, one for headers, reason (status code + message), response time, body etc.
2. Each sections of the first response is stored as original_line.
3. A new response is inputted. 
4. Levenshtein's algorithm (similar to `git diff`) is used to generate opcodes describing how to transform the original lines to the new lines.
5. The opcodes can be used to determine where static strings are within the HTTP response, these indexes are stored as individual Item objects.
    5.1. The insertions are also tracked, often it is possible to see insertions of same length between static strings.
6. A new response is inputted.
7. The indexes for all the static Item's are updated, removing any dynamic strings that were accidentaly equal the last time around.
8. Repeat from step 6.


### Here's the process for diffing:

1. A new response is inputted.
2. Opcodes are generated in a similar manner as in the calibration phase.
3. Check if all known static strings are present, also check whether all known insertions occur at the expected index and are of expected length.
4. Return a Diff object for each anomaly.
5. (Optional) Find differences in two responses with expected different outcomes and compare the diffs.

## Example usage

Go visit [Diffuzz](https://github.com/WillIWas123/Diffuzz) to see an awesome fuzzer utilizing [HTTPDiff](https://github.com/WillIWas123/HTTPDiff).

Here's a small example script showing how [HTTPDiff](https://github.com/WillIWas123/HTTPDiff) can be used:

```python
from httpdiff import Response, Baseline
import string
import random
import requests

def calibrate_baseline(baseline):
    for _ in range(10):
        value = "".join(random.choice(string.ascii_letters) for _ in range(random.randint(3,50)))
        resp = requests.get(f"https://someurl/endpoint?parameter={value}")
        httpdiff_resp = Response(resp)
        baseline.add_response(httpdiff_resp,payload=value) # Adding value as a parameter for finding reflections

    # Often smart to repeat a single payload twice including a potentially cached response in the baseline
    resp = requests.get(f"https://someurl/endpoint?parameter={value}")
    httpdiff_resp = Response(resp)
    baseline.add_response(httpdiff_resp,payload=value)

def scan(baseline):
    payload1 = "' or '1'='1"
    resp = requests.get(f"https://someurl/endpoint?parameter={payload1}")
    httpdiff_resp1 = Response(resp) 

    # payload2 in this example is supposed to contain a similar payload, but a different result if vulnerable. Kind of an opposite payload. 
    payload2 = "' or '1'='2"
    resp = requests.get(f"https://someurl/endpoint?parameter={payload2}")
    httpdiff_resp2 = Response(resp)

    diffs = list(baseline.is_diff(httpdiff_resp1))
    diffs2 = list(baseline.is_diff(httpdiff_resp2))
    if diffs != diffs2:
        print("Vulnerable to SQL Injection!")
    else:
        print("Not vulnerable to SQL injection!")

def main():
    baseline = Baseline()
    calibrate_baseline(baseline)
    scan(baseline)

if __name__ == "__main__":
    main()
```


## Todo

- Work on possibilities of tracking insertions better, can we detect changes even within insertions?
- Improve method for diffing integer ranges
- Properly handle errors
- Do a lot more testing with this tool, bugs may still be present.

## Tips

Some tips for successfully creating your own scanner of some sort:

- Use random values of random length when calibrating a baseline
- Use cachebusters
- Repeat one set of values during calibration (to ensure potential cache hits are included in the baseline)
- Verify the baseline upon a positive result
- Verify the same payload a couple of times upon a positive result to verify it's not a fluke
- Create an issue if you catch any mistakes in the library
- Tell others about [HTTPDiff](https://github.com/WillIWas123/HTTPDiff)
