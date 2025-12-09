from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.template import Template


class ITemplateRepository(ABC):
    """Interface do repositório de templates"""
    
    @abstractmethod
    def create(self, template: Template) -> Template:
        """Cria um novo template"""
        pass
    
    @abstractmethod
    def get_by_id(self, template_id: int) -> Optional[Template]:
        """Busca template por ID"""
        pass
    
    @abstractmethod
    def get_public_templates(self, skip: int = 0, limit: int = 100) -> List[Template]:
        """Lista templates públicos"""
        pass
    
    @abstractmethod
    def get_user_templates(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Template]:
        """Lista templates de um usuário"""
        pass
    
    @abstractmethod
    def update(self, template: Template) -> Template:
        """Atualiza um template"""
        pass
    
    @abstractmethod
    def delete(self, template_id: int) -> bool:
        """Deleta um template"""
        pass
    
    @abstractmethod
    def increment_usage(self, template_id: int) -> bool:
        """Incrementa contador de uso"""
        pass

