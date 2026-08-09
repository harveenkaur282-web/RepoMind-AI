from pydantic import BaseModel, ConfigDict


class GitHubOwner(BaseModel):
    login: str


class GitHubRepository(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    full_name: str
    owner: GitHubOwner
    html_url: str
    default_branch: str
    description: str | None = None
