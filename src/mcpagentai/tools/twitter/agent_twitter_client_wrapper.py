import os
import json
import subprocess
from typing import Any, Dict, Union

class AgentTwitterClientWrapper:
    
    def __init__(self, username: str, 
                 password: str, 
                 cookies_path: str = "./cookies.json",
                 email: str | None = None, 
                 twitter_api_key: str | None = None,
                 twitter_api_secret_key: str | None = None,
                 twitter_access_token: str | None = None,
                 twitter_access_secret_token: str | None = None):
        self.username = username
        self.password = password
        self.email = email
        self.api_creds = None
        if twitter_api_key and twitter_api_secret_key and twitter_access_token and twitter_access_secret_token:
            self.api_creds = {}
            self.api_creds["twitter_api_key"] = twitter_api_key
            self.api_creds["twitter_api_secret_key"] = twitter_api_secret_key
            self.api_creds["twitter_access_token"] = twitter_access_token
            self.api_creds["twitter_access_secret_token"] = twitter_access_secret_token
        self.cookies_path = cookies_path
        #self.save_cookies()

    def _dictify(self, result: Any) -> Dict[str, Any]:
        """Ensure we return a dictionary even if the Node script yields raw text."""
        if isinstance(result, dict):
            return result
        return {"success": False, "error": f"Unexpected output: {result}"}

    def _run_node_script(self, script_content: str) -> Union[Dict[str, Any], str]:
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
        
    def send_tweet(self, tweet_text: str) -> Dict[str, Any]:
        """
        Sends a tweet using your Node.js agent-twitter-client approach.
        Returns the raw response as a dictionary (success, error, etc.).
        """
        script = f"""
        const {{ Scraper }} = require('agent-twitter-client');
        const {{ Cookie }} = require('tough-cookie');

        (async function() {{
        try {{
            const scraper = new Scraper();
            // Load cookies from cookies.json, if you do that
            await scraper.login('{self.username}', '{self.password}');

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
        return self._dictify(self._run_node_script(script_content=script))
    
    def reply_tweet(self, reply_text: str, tweet_url: str) -> Dict[str, Any]:
        """
        Replies to a tweet given its URL or ID.
        In your Node.js, you might do `scraper.replyTweet(id, text)`.
        """
        # If you need just the tweet ID, extract it from the URL
        tweet_id = self.extract_tweet_id(tweet_url)

        script = f"""
        const {{ Scraper }} = require('agent-twitter-client');
        const {{ Cookie }} = require('tough-cookie');

        (async function() {{
        try {{
            const scraper = new Scraper();
            // Load cookies from cookies.json
            await scraper.login('{self.username}', '{self.password}');

            // Post reply
            const resp = await scraper.sendTweet("{reply_text.replace('"', '\\"')}", "{tweet_id}");

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

        return self._dictify(self._run_node_script(script))
    

    def extract_tweet_id(self, url: str) -> str:
        """
        Extract numeric tweet ID from a typical link:
        https://twitter.com/username/status/1234567890123456789
        """
        if "/status/" in url:
            return url.rsplit("/status/", 1)[-1].split("?")[0]
        return url  # fallback if already an ID or unknown format

    def save_cookies(self):
        cookies = self.get_cookies()
        if not cookies['success']:
            raise 
        with open(self.cookies_path, "w") as file:
            file.write(cookies['cookieData'])

    def get_cookies(self):
        """
        Retrieve a cookies after login.
        """
        if self.api_creds is None:
            login_line =f"""
                        await scraper.login('{self.username}', '{self.password}');

                        """
        else:
            login_line = f"""
                        await scraper.login({self.username},
                                            {self.password},
                                            {self.email},
                                            {self.api_creds['twitter_api_key']},
                                            {self.api_creds['twitter_api_secret_key']},
                                            {self.api_creds['twitter_access_token']},
                                            {self.api_creds['twitter_access_secret_token']})
                        """
        script =f"""
        const {{ Scraper }} = require('agent-twitter-client');
        const {{ Cookie }} = require('tough-cookie');
        (async function(){{
        try{{
            const scraper = new Scraper();

            {login_line}
            const is_logged_in = await scraper.isLoggedIn(); 
            if(is_logged_in)
            {{
                const cookies = await scraper.getCookies();
                console.log(JSON.stringify({{
                success: true,
                cookieData: JSON.stringify(cookies)
                }}
                ));
                scraper.logout();
            }}
            else
            {{
                console.log(JSON.stringify({{
                success: false,
                error: error.message
                }}
                ));
            }}

        }}catch(error) {{
            console.log(JSON.stringify({{
            success: false,
            error: error.message
            }}));
        }}
        }})();
        """
        return self._dictify(self._run_node_script(script))

if __name__ == '__main__':
    twitter_wrapper = AgentTwitterClientWrapper("alexandrai20420", "Test1234")
    twitter_wrapper.send_tweet("Hi! I am new to twitter")