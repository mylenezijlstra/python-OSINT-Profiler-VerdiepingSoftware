import httpx
import asyncio
from typing import List, Dict

class OSINTProfiler:
    def __init__(self):
        # Platform templates: {name: (url_template, success_indicator_type, success_value)}
        # success_indicator_type: 'status' (http code) or 'text' (search for text in body)
        self.platforms = {
            "GitHub": ("https://github.com/{}", "status", 200),
            "Twitter (X)": ("https://twitter.com/{}", "status", 200),
            "Instagram": ("https://www.instagram.com/{}/", "status", 200),
            "Reddit": ("https://www.reddit.com/user/{}", "status", 200),
            "Pinterest": ("https://www.pinterest.com/{}/", "status", 200),
            "LinkedIn": ("https://www.linkedin.com/in/{}", "status", 200),
            "TikTok": ("https://www.tiktok.com/@{}", "status", 200),
            "Snapchat": ("https://www.snapchat.com/add/{}", "status", 200),
            "Steam": ("https://steamcommunity.com/id/{}", "status", 200),
            "SoundCloud": ("https://soundcloud.com/{}", "status", 200),
            "Medium": ("https://medium.com/@{}", "status", 200),
            "Vimeo": ("https://vimeo.com/{}", "status", 200),
        }
        
    def generate_usernames(self, first: str, last: str) -> List[str]:
        """Generate common username variations from first and last name."""
        first = first.lower().strip()
        last = last.lower().strip()
        
        variations = [
            f"{first}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first[0]}{last}",
            f"{first}{last[0]}",
            f"{last}{first}",
            f"{last}.{first}"
        ]
        return list(set(variations))

    async def check_platform(self, client: httpx.AsyncClient, name: str, username: str, template: str, indicator: str, value: int) -> Dict:
        url = template.format(username)
        try:
            # We use a common User-Agent to avoid some basic blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=10.0)
            
            is_found = False
            if indicator == "status":
                is_found = response.status_code == value
            
            # Special case for platforms that return 200 but 404 text (like some social sites)
            # This is a simplified version; real OSINT tools use more complex checks
            if is_found and "page not found" in response.text.lower():
                is_found = False
            if is_found and "404" in response.text and response.status_code != 200:
                is_found = False

            return {
                "platform": name,
                "username": username,
                "url": url,
                "status": "Found" if is_found else "Not Found"
            }
        except Exception as e:
            return {
                "platform": name,
                "username": username,
                "url": url,
                "status": "Error"
            }

    async def scan(self, first: str = None, last: str = None, username: str = None):
        if username:
            usernames = [username.strip()]
        elif first and last:
            usernames = self.generate_usernames(first, last)
        else:
            return []
            
        results = []
        
        async with httpx.AsyncClient() as client:
            tasks = []
            for name, (template, indicator, value) in self.platforms.items():
                for u in usernames:
                    tasks.append(self.check_platform(client, name, u, template, indicator, value))
            
            all_results = await asyncio.gather(*tasks)
            
            # Filter to only keep found profiles (or errors)
            # grouped by platform to avoid showing multiple results for the same site if multiple username variations match
            summary = {}
            for res in all_results:
                plat = res["platform"]
                if plat not in summary or res["status"] == "Found":
                    if plat not in summary or summary[plat]["status"] != "Found":
                        summary[plat] = res
            
            return list(summary.values())
