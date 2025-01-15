import os
import json
import subprocess
from typing import Any, Dict, Union
from pathlib import Path

# Get current working directory (where start.sh is run from)
WORKING_DIR = Path.cwd()
COOKIES_PATH = WORKING_DIR / 'cookies.json'


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
    escaped_text = tweet_text.replace('"', '\\"')

    script = f"""
    const {{ Scraper }} = require('agent-twitter-client');
    const {{ Cookie }} = require('tough-cookie');

    (async function() {{
      try {{
        const scraper = new Scraper();
        // Load cookies if they exist
        let cookiesData = [];
        try {{
          cookiesData = require('{COOKIES_PATH}');
        }} catch (err) {{
          // no cookies - will trigger fresh login
        }}

        const cookies = cookiesData.map(c => new Cookie({{
          key: c.key, value: c.value, domain: c.domain,
          path: c.path, secure: c.secure, httpOnly: c.httpOnly
        }}).toString());
        await scraper.setCookies(cookies);

        // Post tweet
        const resp = await scraper.sendTweet("{escaped_text}");

        // Save cookies after successful operation
        const newCookies = await scraper.getCookies();
        require('fs').writeFileSync('{COOKIES_PATH}', JSON.stringify(newCookies, null, 2));

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
    escaped_text = reply_text.replace('"', '\\"')

    script = f"""
    const {{ Scraper }} = require('agent-twitter-client');
    const {{ Cookie }} = require('tough-cookie');

    (async function() {{
      try {{
        const scraper = new Scraper();
        // Load cookies from cookies.json
        let cookiesData = [];
        try {{
          cookiesData = require('{COOKIES_PATH}');
        }} catch (err) {{}}

        const cookies = cookiesData.map(c => new Cookie({{
          key: c.key, value: c.value, domain: c.domain,
          path: c.path, secure: c.secure, httpOnly: c.httpOnly
        }}).toString());
        await scraper.setCookies(cookies);

        // Post reply
        const resp = await scraper.replyTweet("{tweet_id}", "{escaped_text}");

        // Save cookies after successful operation
        const newCookies = await scraper.getCookies();
        require('fs').writeFileSync('{COOKIES_PATH}', JSON.stringify(newCookies, null, 2));

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


def get_mentions() -> list:
    """
    Fetches recent mentions using searchTweets.
    Returns a list of mention objects with id, username, text, and conversation context.
    """
    print("\n🔍 Checking for new mentions...")

    script = f"""
    const {{ Scraper }} = require('agent-twitter-client');
    const {{ Cookie }} = require('tough-cookie');

    (async function() {{
      try {{
        const scraper = new Scraper();
        console.log("📝 Loading cookies...");
        // Load cookies if they exist
        let cookiesData = [];
        try {{
          cookiesData = require('{COOKIES_PATH}');
          console.log("✅ Cookies loaded successfully");
        }} catch (err) {{
          console.log("⚠️ No existing cookies found");
        }}

        const cookies = cookiesData.map(c => new Cookie({{
          key: c.key, value: c.value, domain: c.domain,
          path: c.path, secure: c.secure, httpOnly: c.httpOnly
        }}).toString());
        await scraper.setCookies(cookies);

        console.log(`🔎 Searching for tweets mentioning @${{process.env.TWITTER_USERNAME}}...`);
        const mentions = [];
        for await (const mention of scraper.searchTweets(
            `@${{process.env.TWITTER_USERNAME}}`,
            100,
            1
        )) {{
            if (mention.username === process.env.TWITTER_USERNAME) {{
                console.log(`⏩ Skipping own tweet: ${mention.text}`);
                continue;
            }}
            console.log(`✨ Found mention from @${mention.username}: ${mention.text}`);
            mentions.push(mention);
        }}

        const newCookies = await scraper.getCookies();
        require('fs').writeFileSync('{COOKIES_PATH}', JSON.stringify(newCookies, null, 2));
        console.log(`✅ Found ${mentions.length} total mentions`);
        return mentions;
      }} catch (error) {{
        console.log(`❌ Error checking mentions: ${error.message}`);
        return [];
      }}
    }})();
    """

    try:
        result = _run_node_script(script)
        if isinstance(result, list):
            print(f"✅ Successfully fetched {len(result)} mentions")
            return result
        elif isinstance(result, dict) and 'mentions' in result:
            mentions = result['mentions']
            print(f"✅ Successfully fetched {len(mentions)} mentions")
            return mentions
        else:
            print(f"❌ Unexpected response format: {result}")
            return []
    except Exception as e:
        print(f"❌ Error parsing mentions response: {e}")
        return []
