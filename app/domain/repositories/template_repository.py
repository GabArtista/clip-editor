from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.template import Template


class ITemplateRepository(ABC):
    """Contrato do repositório de templates."""

    @abstractmethod
    def create(self, template: Template) -> Template:
        ...

    @abstractmethod
    def get_by_id(self, template_id: int) -> Optional[Template]:
        ...

    @abstractmethod
    def get_public_templates(self, skip: int = 0, limit: int = 100) -> List[Template]:
        ...

    @abstractmethod
    def get_user_templates(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Template]:
        ...

    @abstractmethod
    def update(self, template: Template) -> Template:
        ...

    @abstractmethod
    def delete(self, template_id: int) -> bool:
        ...

    @abstractmethod
    def increment_usage(self, template_id: int) -> bool:
        ...


