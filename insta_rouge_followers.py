#!/usr/bin/env python3
"""
Compare Instagram followers and following exports.

Usage:
    python instagram_compare.py followers_1.json following.json
    python instagram_compare.py followers_1.json following.json --out results

Outputs:
    - A DataFrame with two columns: 'followers' and 'following'
    - The list of usernames present in following but NOT in followers
"""

import argparse
import json
from urllib.parse import urlparse

import pandas as pd


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def username_from_href(href):
    """Fallback: extract username from an Instagram profile URL."""
    if not href:
        return None
    parts = [p for p in urlparse(href).path.split("/") if p]
    # handles both /username and /_u/username
    return parts[-1] if parts else None


def extract_followers(data):
    """
    Followers file is usually a top-level list of records:
      {"title": "", "media_list_data": [], "string_list_data": [{"href", "value", "timestamp"}]}
    Username lives in string_list_data[0]["value"].
    """
    if isinstance(data, dict):
        # Some exports wrap the list in a key such as "relationships_followers"
        for value in data.values():
            if isinstance(value, list):
                data = value
                break

    usernames = []
    for record in data:
        for item in record.get("string_list_data", []):
            name = item.get("value") or username_from_href(item.get("href"))
            if name:
                usernames.append(name)
    return usernames


def extract_following(data):
    """
    Following file is a dict:
      {"relationships_following": [{"title": "<username>", "string_list_data": [...]}, ...]}
    Username lives in "title" (falls back to href if title is empty).
    """
    records = data.get("relationships_following", []) if isinstance(data, dict) else data

    usernames = []
    for record in records:
        name = record.get("title")
        if not name:
            items = record.get("string_list_data", [])
            if items:
                name = items[0].get("value") or username_from_href(items[0].get("href"))
        if name:
            usernames.append(name)
    return usernames


def build_dataframe(followers, following):
    """Two columns of (possibly) different lengths -> pad shorter with NaN."""
    return pd.DataFrame(
        {
            "followers": pd.Series(followers, dtype="object"),
            "following": pd.Series(following, dtype="object"),
        }
    )


def main():
    parser = argparse.ArgumentParser(description="Compare Instagram followers and following.")
    parser.add_argument("followers_file", help="C://Users/priyanshu/Documents/Projects/insta_followers_not_following_back/followers_1.json")
    parser.add_argument("following_file", help="C://Users/priyanshu/Documents/Projects/insta_followers_not_following_back/following.json")
    parser.add_argument("--out", help="Optional output prefix to save CSV files", default=None)
    args = parser.parse_args()

    followers = extract_followers(load_json(args.followers_file))
    following = extract_following(load_json(args.following_file))

    df = build_dataframe(followers, following)

    # In following but not in followers (people who don't follow you back)
    followers_set = set(followers)
    not_following_back = sorted(u for u in set(following) if u not in followers_set)
    not_following_back_df = pd.DataFrame({"not_following_you_back": not_following_back})

    print(f"Followers: {len(set(followers))} | Following: {len(set(following))}")
    print("\n=== DataFrame (followers vs following) ===")
    print(df.to_string())
    print(f"\n=== In following but NOT in followers ({len(not_following_back)}) ===")
    for name in not_following_back:
        print(name)

    df.to_csv(f"followers_following_usernames.csv", index=False)
    not_following_back_df.to_csv(f"not_following_back.csv", index=False)
    print(f"\nSaved followers_following_usernames.csv and not_following_back.csv")


if __name__ == "__main__":
    main()