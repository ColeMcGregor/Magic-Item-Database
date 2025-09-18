import sys
import requests

'''
This program prints the payload of a reddit post.
It takes in a reddit post url and prints the payload of the post.
its used for testing reddit json calls, and to see what info is available. when we are scraping reddit.

author: Cole McGregor
date: 2025-09-18
version: 0.1.0
'''

def main():
    if len(sys.argv) < 2:
        print("Usage: python print_reddit_payload.py <reddit_post_url>")
        sys.exit(1)

    url = sys.argv[1].rstrip("/")
    if not url.endswith(".json"):
        url = url + "/.json"

    headers = {"User-Agent": "liamindex-scraper/0.1"}
    params = {"sort": "top", "limit": 500, "depth": 1}

    resp = requests.get(url, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    comments = data[1]["data"]["children"]
    for c in comments:
        if c["kind"] != "t1":
            continue
        author = c["data"].get("author")
        body = c["data"].get("body")
        print(f"Author: {author}\n{body}\n{'-'*40}")

if __name__ == "__main__":
    main()
