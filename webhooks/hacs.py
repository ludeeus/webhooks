"""Handle HACS automations."""
import aiohttp
from integrationhelper import WebClient

from aiogithubapi import AIOGitHub


class Hacs:
    """HACS Auotmations."""

    def __init__(self):
        """initialize."""
        self.hacs = None
        self.token = None
        self.aiogithub = None

    async def initilize_hacs(self):
        """Extra initialization."""
        self.aiogithub = AIOGitHub(self.token, aiohttp.ClientSession())
        self.hacs = await self.aiogithub.get_repo("custom-components/hacs")

    async def handle_greeting(self, issue_number, submitter):
        """Handle greetings."""
        greeting = f"Hi, @{submitter} 👋\n\n"
        greeting += "An automatic task is now running some initial checks before this can be merged.\n"
        greeting += (
            "When those are done, someone will manually ensure that that it's OK. 💃\n\n"
        )
        greeting += "While you wait, you can have a look at [this cute kitten 😺](https://www.youtube.com/watch?v=0Bmhjf0rKe8)"
        await self.hacs.comment_on_issue(issue_number, greeting)

    async def handle_new_repo_pr_data(self, issue_data):
        """Handle PR's to the data branch."""
        issue_number = issue_data["number"]
        submitter = issue_data["sender"]["login"]
        async with aiohttp.ClientSession() as session:
            lables = ["New default repository"]

            categiories, added, removed = await get_diff_data(
                aiohttp.ClientSession(), issue_number
            )
            for repo in removed:
                if repo in added:
                    added.remove(repo)

            for repo in added:
                if not "/" in repo:
                    added.remove(repo)

            if len(categiories) > 1:
                lables.append("Manual review required")

            comments = await self.hacs.list_issue_comments(issue_number)
            greeting_done = False
            for comment in comments:
                if f"Hi, @{submitter} 👋\n\n" in comment.body:
                    greeting_done = True
                    break
            if not greeting_done:
                await self.handle_greeting(issue_number, submitter)

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
                    repochecks["submitter is owner"] = repo.split("/")[0] == submitter
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

            comment_number = None
            for comment in comments:
                if "# Repository checks\n\n" in comment.body:
                    comment_number = comment.id
                    break

            await self.hacs.update_issue(
                issue_number, labels=lables, assignees=["ludeeus"]
            )
            if comment_number is None:
                pass
                await self.hacs.comment_on_issue(issue_number, issue_comment)
            else:
                pass
                await self.hacs.update_comment_on_issue(comment_number, issue_comment)


async def get_diff_data(session, issue_number):
    """Get the data in the diff"""
    webclient = WebClient(session)

    diff = await webclient.async_get_text(
        f"https://patch-diff.githubusercontent.com/raw/custom-components/hacs/pull/{issue_number}.diff",
        {},
    )

    categiories = []
    added = []
    removed = []
    for line in diff.split("\n"):
        if "+++" in line:
            categiories.append(line.split("/")[-1])
        elif "-  " in line:
            removed.append(line.split('"')[1])
        elif "+  " in line:
            added.append(line.split('"')[1])

    return categiories, added, removed
