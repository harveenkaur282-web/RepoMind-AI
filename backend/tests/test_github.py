import pytest

from backend.app.services.github.client import GitHubClient


@pytest.mark.asyncio
async def test_get_repository() -> None:
    client = GitHubClient()

    try:
        repository = await client.get_repository(
            "octocat",
            "Hello-World",
        )

        assert repository.name == "Hello-World"
        assert repository.owner.login == "octocat"
        assert repository.html_url.startswith("https://github.com/")
        assert repository.default_branch

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_authenticated_user() -> None:
    client = GitHubClient()

    try:
        user = await client.get_authenticated_user()

        assert user["login"]
        assert user["id"]

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_repository_tree() -> None:
    client = GitHubClient()

    try:
        repository = await client.get_repository(
            owner="harveenkaur282-web",
            repo="RepoMind-AI",
        )

        tree = await client.get_repository_tree(
            owner="harveenkaur282-web",
            repo="RepoMind-AI",
            tree_sha=repository.default_branch,
        )

        assert "tree" in tree
        assert "truncated" in tree
        assert isinstance(tree["tree"], list)

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_file_content() -> None:
    client = GitHubClient()

    try:
        repository = await client.get_repository(
            owner="harveenkaur282-web",
            repo="RepoMind-AI",
        )

        content = await client.get_file_content(
            owner="harveenkaur282-web",
            repo="RepoMind-AI",
            path="README.md",
            ref=repository.default_branch,
        )

        assert "RepoMind" in content
        assert "AI" in content

    finally:
        await client.close()


def test_github_client_token_header() -> None:
    from unittest.mock import MagicMock, patch

    with patch("backend.app.services.github.client.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.github_token = "my_secret_token"
        mock_get_settings.return_value = mock_settings

        client = GitHubClient()
        assert client.client.headers["authorization"] == "token my_secret_token"
