"""Handle HACS automations."""
import aiohttp
from integrationhelper import WebClient

from aiogithubapi import AIOGitHub


class Hacs:
    """HACS Auotmations."""

    def __init__(self, session):
        """initialize."""
        self.session = session
        self.hacs = None
        self.token = None
        self.aiogithub = None

    async def initilize_hacs(self):
        """Extra initialization."""
        print("Initializing HACS")
        self.aiogithub = AIOGitHub(self.token, self.session)
        self.hacs = await self.aiogithub.get_repo("custom-components/hacs")

    async def execute(self, event_data):
        """Run tasks based on the content in the event data."""
        if event_data.get("pull_request") is not None:
            print("We now know that this is a PR.")
            executer = PullRequest(event_data, self.hacs, self.aiogithub, self.session)
            executer.issue_number = event_data["number"]
            executer.action = event_data["action"]
            executer.submitter = event_data["pull_request"]["user"]["login"]
            await executer.handle_greeting()
            if event_data["pull_request"]["base"]["ref"] == "data":
                # This PR goes to the data branch, let's assume it's a new default repo.
                await executer.handle_new_repo_pr_data()

        if event_data.get("issue") is not None:
            print("We now know that this is a issue.")
            executer = Issue(event_data, self.hacs, self.aiogithub, self.session)
            executer.issue_number = event_data["issue"]["number"]
            executer.action = event_data["action"]
            executer.submitter = event_data["issue"]["user"]["login"]
            if event_data["issue"]["state"] == "open":
                print("The issue is open.")
                await executer.known_issue()

            elif event_data["issue"]["state"] == "closed":
                print("The issue is closed.")
                if executer.action == "created":
                    if event_data.get("comment") is not None:
                        print("Someone commented on a closed issue!")
                        await executer.comment_on_closed_issue()



class Common:
    def __init__(self, data, hacs_repository, aiogithub, session):
        self.data = data
        self.session = session
        self.issue_number = None
        self.submitter = None
        self.action = None
        self.hacs_repository = hacs_repository
        self.aiogithub = aiogithub

    async def handle_greeting(self):
        """Handle greetings."""
        if self.action == "opened":
            comments = await self.hacs_repository.list_issue_comments(self.issue_number)
            greeting_done = False
            for comment in comments:
                if f"Hi, @{self.submitter} 👋\n\n" in comment.body:
                    greeting_done = True
                    break
            if not greeting_done:
                greeting = f"Hi, @{self.submitter} 👋\n\n"
                greeting += "An automatic task is now running some initial checks before this can be merged.\n"
                greeting += "When those are done, someone will manually ensure that that it's OK. 💃\n\n"
                greeting += "While you wait, you can have a look at [this cute kitten 😺](https://www.youtube.com/watch?v=0Bmhjf0rKe8)"
                await self.create_comment(greeting)

    async def create_comment(self, message):
        """Comment on an issue/PR"""
        message += "\n\n\n_This message was automatically generated🚀_"
        print(f"Adding comment to issue {self.issue_number}")
        print(message)
        await self.hacs_repository.comment_on_issue(self.issue_number, message)

    async def update_comment(self, message, comment_number):
        """Update a comment on an issue/PR"""
        message += "\n\n\n_This message was automatically generated🚀_"
        print(f"Adding comment to issue {self.issue_number}")
        print(message)
        await self.hacs_repository.update_comment_on_issue(comment_number, message)


class Issue(Common):
    async def known_issue(self):
        """Post a comment if this is a known issue, then close the issue."""
        if self.action == "opened":
            print("Searching for known issues")
            from .const import KNOWN_ISSUES

            is_known = False
            message = None
            for issue in KNOWN_ISSUES:
                print(f"Searching for {issue}")
                if issue in self.data["issue"]["body"]:
                    is_known = True
                    message = KNOWN_ISSUES[issue]
                    break

            if is_known:
                await self.create_comment(message)
                await self.hacs_repository.update_issue(
                    self.issue_number, state="closed"
                )


    async def comment_on_closed_issue(self):
        """Comment on a closed issue."""
        if self.data["issue"]["author_association"] != "COLLABORATOR":
            from .const import CLOSED_ISSUE
            user = self.data["comment"]["user"]
            message = CLOSED_ISSUE.format(user)
            await self.create_comment(message)



class PullRequest(Common):
    async def get_diff_data(self):
        """Get the data in the diff"""
        files = []
        added = []
        removed = []
        webclient = WebClient(self.session)

        diff = await webclient.async_get_text(
            f"https://patch-diff.githubusercontent.com/raw/custom-components/hacs/pull/{self.issue_number}.diff",
            {},
        )

        for line in diff.split("\n"):
            if "+++" in line:
                files.append(line.split("/")[-1])
            elif "-  " in line:
                removed.append(line.split('"')[1])
            elif "+  " in line:
                added.append(line.split('"')[1])

        return files, added, removed

    async def handle_new_repo_pr_data(self):
        """Handle PR's to the data branch."""
        lables = ["New default repository"]

        files, added, removed = await self.get_diff_data()
        for repo in removed:
            if repo in added:
                added.remove(repo)

        for repo in added:
            if not "/" in repo:
                added.remove(repo)

        if len(files) > 1:
            lables.append("Manual review required")

        issue_comment = "# Repository checks\n\n"
        issue_comment += "These checks are automatic.\n\n"

        for repo in added:
            repochecks = {
                "repository exists": False,
                "submitter is owner": False,
                "not a fork": False,
            }
            try:
                repository = await self.aiogithub.get_repo(repo)
                repochecks["repository exists"] = True
                print(repository.fork)
                repochecks["not a fork"] = not repository.fork
                repochecks["submitter is owner"] = repo.split("/")[0] == self.submitter
            except Exception:
                if "Manual review required" not in lables:
                    lables.append("Manual review required")

            issue_comment += f"## Checks for `{repo}`\n\n"
            issue_comment += f"[Repository link](https://github.com/{repo})\n\n"
            issue_comment += "Status | Check\n-- | --\n"
            for check in repochecks:
                issue_comment += "✔️" if repochecks[check] else "❌"
                issue_comment += f" | {check.capitalize()}\n"
            issue_comment += "\n"

            all_checks_pased = True
            for check in repochecks:
                if not repochecks[check]:
                    all_checks_pased = False
                    break

            if all_checks_pased:
                issue_comment += "All automatic checks of the repository is ok, waiting for a manual review."
            else:
                issue_comment += "One (or more) automatic check(s) faile."
                if "Manual review required" not in lables:
                    lables.append("Manual review required")

        comments = await self.hacs_repository.list_issue_comments(self.issue_number)
        comment_number = None
        for comment in comments:
            if "# Repository checks\n\n" in comment.body:
                comment_number = comment.id
                break

        await self.hacs_repository.update_issue(
            self.issue_number, labels=lables, assignees=["ludeeus"]
        )
        if comment_number is None:
            await self.create_comment(issue_comment)
        else:
            await self.update_comment(issue_comment, comment_number)
