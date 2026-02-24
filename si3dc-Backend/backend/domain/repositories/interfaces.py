"""SI3DC — Repository Interfaces (Abstract).

DDD repository contracts for the domain layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository defining standard CRUD operations."""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        ...

    @abstractmethod
    async def list_all(self, offset: int = 0, limit: int = 50) -> list[T]:
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        ...

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        ...


class PatientRepository(BaseRepository["PatientORM"]):
    """Repository contract for Patient entity."""

    @abstractmethod
    async def get_by_cpf(self, cpf: str) -> Optional["PatientORM"]:
        ...

    @abstractmethod
    async def search(self, query: str, offset: int = 0, limit: int = 20) -> list["PatientORM"]:
        ...


class ProfessionalRepository(BaseRepository["HealthProfessionalORM"]):
    """Repository contract for HealthProfessional entity."""

    @abstractmethod
    async def get_by_registration(
        self, reg_type: str, reg_number: str
    ) -> Optional["HealthProfessionalORM"]:
        ...
