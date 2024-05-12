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

A lot of web pentesting tools suck, using regexes or hardcoded values to determine whether something is different. These methods will produce false-positives no matter how much you tweak those values. [HTTPDiff](https://github.com/WillIWas123/HTTPDiff) attempts to use a more dynamic way of differentiation responses, attempting to reduce the false-positives produced during a scan.

By sending multiple requests with a known outcome, it is possible to calibrate a baseline of how the application normally behaves. [HTTPDiff](https://github.com/WillIWas123/HTTPDiff) can then be used to find deviations from the default behavior. [HTTPDiff](https://github.com/WillIWas123/HTTPDiff) will analyze every part of the response; the status code, reason, headers, body, response time, and even errors.


## Usecases

- Most (not all) content discovery tools rely solely on status codes for verifying if the endpoint exists (Good luck finding files and directories purposely hidden by returning a 404!). This is my attempt to create a flexible library designed to make it easy to create awesome scanners, finding all kinds of vulnerabilities!

- If you want to brute-force endpoints and directories on a web application, you can start by sending a series of requests to known invalid endpoints. The baseline can now be used to determine if any other endpoints behave in a similar way, or are somehow different. Go to [WebCD](https://github.com/WillIWas123/WebCD) for a good example on how to utilize this library.

- Want to check if an endpoint changes over time? Create a small script to determine the normal behavior and check in later! (Note that certain content may change over time such as the Date header, calibrate over time for optimal results).


## Installation


```python3 -m pip install httpdiff```

## How it all works

Here comes some details of how the library is built, feel free to skip this section if you're not interested:


### Here's the process for calibrating:

1. The Analyzer object takes a response object as a parameter (among others), multiple Blobs are created, one for headers, reason (status code + message), response time, body etc.
2. The input strings/bytes are split on multiple characters `,.; and whitespaces`. A list of these bytes/strings are stored as the original lines.
3. A new response is inputted, the strings are similarly split on the same characters.
4. Levenshtein's algorithm (similar to `git diff`) is used to generate opcodes describing how to transform the original lines to the new lines.
5. Using these opcodes it is possible to relatively accurately determine the location of each Item, track replacements, insertions, deletions etc.
6. A check for multiple properties are done, if all the lines in an Item have the same property it's stored as a method to analyze the lines in the future. A property in this case is a way to compare or measure a line.
7. If there are no properties that can be used, the Item is going to be ignored in any future diffing.
8. Repeat from step 3.


### Here's the process for diffing:

1. A new response is inputted, the strings are similarly split on the same characters as before.
2. Opcodes are generated in a similar manner as before.
3. Each line is compared against its respective Item, verifying the new line has the same properties as all the previous lines in the Item.
4. If the line does not contain one of the stored properties, a Diff is created.
5. (Optional) Find differences in two responses with expected different outcomes and compare the diffs.

## Example usage

Go visit [WebCD](https://github.com/WillIWas123/WebCD) to see an awesome content discovery tool utilizing [HTTPDiff](https://github.com/WillIWas123/HTTPDiff).

Here's a small example script showing how [HTTPDiff](https://github.com/WillIWas123/HTTPDiff) can be used:

```python
import requests
from httpdiff import Response, Analyzer, remove_reflection
import string
import random

def calibrate_baseline(analyzer):
    value = "".join(random.choice(string.ascii_letters) for _ in range(random.randint(3,15)))
    for _ in range(10):
        resp = requests.get(f"https://someurl/endpoint?param={value}")
        httpdiff_resp = Response(resp)
        analyzer.add_response(httpdiff_resp)

def scan(analyzer):
    # 10 1's and 10 2's are used for easier identifying the reflection in the response
    payload1 = "' or '1111111111'='1111111111"
    resp = requests.get(f"https://someurl/endpoint?param={payload1}")
    httpdiff_resp1 = Response(resp)
    # Using lists instead of generator output because the diffs are going to be compared


    # payload2 in this example is supposed to contain a similar payload, but a different result if vulnerable. Kind of an opposite payload.
    payload2 = "' or '1111111111'='2222222222"
    resp = requests.get(f"https://someurl/endpoint?param={payload2}")
    httpdiff_resp2 = Response(resp)

    # Attempts to remove the reflection of the payloads
    remove_reflection(httpdiff_resp1,httpdiff_resp2,payload1,payload2)

    diffs = list(analyzer.is_diff(httpdiff_resp1))
    diffs2 = list(analyzer.is_diff(httpdiff_resp2))
    if diffs != diffs2:
      print(f"Vulnerable to SQL Injection!") 

def main():
    analyzer = Analyzer()
    calibrate_baseline(analyzer)
    scan(analyzer)

if __name__ == "__main__": 
  main()
```


## Todo

- Implement more property checks for Items
- Improve method for diffing integer ranges
- Properly handle errors
- Make it easier to "overwrite" functions in order to create custom calibration and diffing methods.
- Do a lot more testing with this tool, bugs may still be present.
- Multiple TODO's are scattered around the code, these will be addressed some time in the future.

## Tips

Some tips for successfully creating your own scanner of some sort:

- Use random values of random length when calibrating a baseline
- Use cachebusters
- Repeat one set of values during calibration (to ensure potential cache hits are included in the baseline)
- Use relatively long values for values that are arbitrary (for removing reflection with better accuracy)
- Verify the baseline upon a positive result
- Verify the same payload a couple of times upon a positive result to verify it's not a fluke
- Create an issue if you catch any mistakes in the library
- Tell others about [HTTPDiff](https://github.com/WillIWas123/HTTPDiff)

