# logic/recursion_handler.py

class RecursionHandler:
    def __init__(self, max_depth=3):
        self.max_depth = max_depth

    def recurse_followers(self, scraper, username, depth=0, visited=None):
        if visited is None:
            visited = set()
        if depth >= self.max_depth or username in visited:
            return []
        visited.add(username)
        followers = scraper.get_followers(username)
        all_profiles = []
        for follower in followers:
            all_profiles.append(follower)
            all_profiles.extend(self.recurse_followers(scraper, follower, depth + 1, visited))
        return all_profiles
