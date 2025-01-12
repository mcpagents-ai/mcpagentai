import os
import json
import subprocess
from typing import Any, Dict, Union


def _run_node_script(script_content: str) -> Union[Dict[str, Any], str]:
    """
    Runs a Node.js script via a temporary file, captures stdout/stderr,
    and returns JSON (if possible) or raw text.
    """
    script_filename = "temp_twitter_script.js"
    with open(script_filename, "w", encoding="utf-8") as f:
        f.write(script_content)

    process = subprocess.Popen(
        ["node", script_filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ},  # Pass environment variables if needed
    )
    stdout, stderr = process.communicate()
    retcode = process.returncode

    # Cleanup
    try:
        os.remove(script_filename)
    except OSError:
        pass

    if retcode != 0:
        err_msg = stderr.decode(errors="replace")
        raise RuntimeError(f"Node script error: {err_msg}")

    output_str = stdout.decode(errors="replace")
    try:
        return json.loads(output_str)
    except json.JSONDecodeError:
        return output_str


def send_tweet(tweet_text: str) -> Dict[str, Any]:
    """
    Sends a tweet using your Node.js agent-twitter-client approach.
    Returns the raw response as a dictionary (success, error, etc.).
    """
    # Basic example: you can expand or adjust as needed to handle cookies, login, etc.
    script = f"""
    const {{ Scraper }} = require('agent-twitter-client');
    const {{ Cookie }} = require('tough-cookie');

    (async function() {{
      try {{
        const scraper = new Scraper();
        // Load cookies from cookies.json, if you do that
        let cookiesData = [];
        try {{
          cookiesData = require('./cookies.json');
        }} catch (err) {{
          // no cookies
        }}

        const cookies = cookiesData.map(c => new Cookie({{
          key: c.key, value: c.value, domain: c.domain,
          path: c.path, secure: c.secure, httpOnly: c.httpOnly
        }}).toString());
        await scraper.setCookies(cookies);

        // Post tweet
        const resp = await scraper.sendTweet("{tweet_text.replace('"', '\\"')}");

        console.log(JSON.stringify({{
          success: true,
          message: "Tweet posted!",
          tweet_url: resp.url ? resp.url : null
        }}));
      }} catch (error) {{
        console.log(JSON.stringify({{
          success: false,
          error: error.message
        }}));
      }}
    }})();
    """

    return _dictify(_run_node_script(script))


def reply_tweet(reply_text: str, tweet_url: str) -> Dict[str, Any]:
    """
    Replies to a tweet given its URL or ID.
    In your Node.js, you might do `scraper.replyTweet(id, text)`.
    """
    # If you need just the tweet ID, extract it from the URL
    tweet_id = extract_tweet_id(tweet_url)

    script = f"""
    const {{ Scraper }} = require('agent-twitter-client');
    const {{ Cookie }} = require('tough-cookie');

    (async function() {{
      try {{
        const scraper = new Scraper();
        // Load cookies from cookies.json
        let cookiesData = [];
        try {{
          cookiesData = require('./cookies.json');
        }} catch (err) {{}}

        const cookies = cookiesData.map(c => new Cookie({{
          key: c.key, value: c.value, domain: c.domain,
          path: c.path, secure: c.secure, httpOnly: c.httpOnly
        }}).toString());
        await scraper.setCookies(cookies);

        // Post reply
        const resp = await scraper.replyTweet("{tweet_id}", "{reply_text.replace('"', '\\"')}");

        console.log(JSON.stringify({{
          success: true,
          message: "Reply posted!",
          tweet_url: resp.url ? resp.url : null
        }}));
      }} catch (error) {{
        console.log(JSON.stringify({{
          success: false,
          error: error.message
        }}));
      }}
    }})();
    """

    return _dictify(_run_node_script(script))


def extract_tweet_id(url: str) -> str:
    """
    Extract numeric tweet ID from a typical link:
    https://twitter.com/username/status/1234567890123456789
    """
    if "/status/" in url:
        return url.rsplit("/status/", 1)[-1].split("?")[0]
    return url  # fallback if already an ID or unknown format


def _dictify(result: Any) -> Dict[str, Any]:
    """Ensure we return a dictionary even if the Node script yields raw text."""
    if isinstance(result, dict):
        return result
    return {"success": False, "error": f"Unexpected output: {result}"}
