from backend.app.services.github.client import GitHubClient


class RepositoryIngestor:
    def __init__(self, github_client: GitHubClient | None = None) -> None:
        self.github_client = github_client or GitHubClient()

    async def ingest_repository(
        self,
        owner: str,
        repo: str,
    ) -> None:
        repository = await self.github_client.get_repository(
            owner=owner,
            repo=repo,
        )

        await self.github_client.get_repository_tree(
            owner=owner,
            repo=repo,
            tree_sha=repository.default_branch,
            recursive=True,
        )

        # file processing will be added next.
