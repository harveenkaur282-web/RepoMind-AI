from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Interface for embedding providers."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        raise NotImplementedError

    @abstractmethod
    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Embed documents/chunks for retrieval."""
        raise NotImplementedError

    @abstractmethod
    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """Embed a search query."""
        raise NotImplementedError
