import os, re, json, subprocess, pathlib, time, random, urllib.parse, hmac, hashlib, base64
return tweet[:MAX_TWEET_LEN]


def oauth1_headers(status: str):
oauth_params = {
'oauth_consumer_key': X_API_KEY,
'oauth_nonce': ''.join(random.choice('0123456789ABCDEF') for _ in range(32)),
'oauth_signature_method': 'HMAC-SHA1',
'oauth_timestamp': str(int(time.time())),
'oauth_token': X_ACCESS_TOKEN,
'oauth_version': '1.0',
}
url = 'https://api.twitter.com/1.1/statuses/update.json'
params = { 'status': status }
all_params = {**oauth_params, **params}
param_str = '&'.join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(all_params[k], safe='')}" for k in sorted(all_params))
base_elems = ['POST', urllib.parse.quote(url, safe=''), urllib.parse.quote(param_str, safe='')]
base_str = '&'.join(base_elems)
signing_key = f"{urllib.parse.quote(X_API_SECRET, safe='')}&{urllib.parse.quote(X_ACCESS_SECRET, safe='')}"
sig = hmac.new(signing_key.encode(), base_str.encode(), hashlib.sha1).digest()
oauth_params['oauth_signature'] = base64.b64encode(sig).decode()
auth_header = 'OAuth ' + ', '.join([f'{k}="{urllib.parse.quote(v)}"' for k,v in oauth_params.items()])
return {'Authorization': auth_header, 'Content-Type': 'application/x-www-form-urlencoded'}


def post_tweet(status: str):
if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
print("[dry-run]", status)
return False
headers = oauth1_headers(status)
r = requests.post('https://api.twitter.com/1.1/statuses/update.json', headers=headers, data={'status': status})
print(r.status_code, r.text)
return r.ok


def main():
state = load_state()
seen = set(state.get("seen_post_ids", []))
counts = state.get("mention_counts", {})
prev_top = state.get("top10", [])
posts = parse_posts_html()
new_posts = [p for p in posts if p["id"] not in seen]
if not new_posts:
print("No new posts.")
return 0
for p in new_posts:
title = p["id"]
post_url = f"{SITE_BASE}/blog/#{urllib.parse.quote(p['id'])}"
handles = extract_handles(p.get("text"), p.get("html"))
first_time = [h for h in handles if h not in counts]
for h in set(handles):
counts[h] = counts.get(h, 0) + 1
cur_top = rank_top10(counts)
tweet = compose_tweet(title, post_url, first_time, prev_top, cur_top)
post_tweet(tweet)
prev_top = cur_top
seen.add(p["id"])
state["seen_post_ids"] = list(seen)
state["mention_counts"] = counts
state["top10"] = prev_top
save_state(state)
try:
sh("git", "config", "user.name", GIT_USER_NAME)
sh("git", "config", "user.email", GIT_USER_EMAIL)
sh("git", "add", str(STATE_PATH.relative_to(REPO_ROOT)))
sh("git", "commit", "-m", "update state [skip ci]", check=False)
sh("git", "push", "origin", DEFAULT_BRANCH)
except Exception as e:
print("[warn] push failed", e)
return 0


if __name__ == "__main__":
raise SystemExit(main())
