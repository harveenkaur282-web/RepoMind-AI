class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""


class GitHubNotFoundError(GitHubAPIError):
    """Raised when a GitHub resource does not exist."""


class GitHubRateLimitError(GitHubAPIError):
    """Raised when the GitHub API rate limit is exceeded."""
