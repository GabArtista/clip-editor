from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.domain.entities.template import Template
from app.domain.repositories.template_repository import ITemplateRepository
from app.Models.template_model import Template


class TemplateRepository(ITemplateRepository):
    """Implementação do repositório de templates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, template: Template) -> Template:
        """Cria um novo template"""
        db_template = Template(
            name=template.name,
            description=template.description,
            template_type=template.template_type,
            config=template.config,
            thumbnail_url=template.thumbnail_url,
            is_public=template.is_public,
            created_by=template.created_by,
            usage_count=0
        )
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template.to_domain()
    
    def get_by_id(self, template_id: int) -> Optional[Template]:
        """Busca template por ID"""
        db_template = self.db.query(Template).filter(
            Template.id == template_id
        ).first()
        return db_template.to_domain() if db_template else None
    
    def get_public_templates(self, skip: int = 0, limit: int = 100) -> List[Template]:
        """Lista templates públicos"""
        db_templates = self.db.query(Template).filter(
            Template.is_public == True
        ).offset(skip).limit(limit).order_by(Template.usage_count.desc()).all()
        return [t.to_domain() for t in db_templates]
    
    def get_user_templates(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Template]:
        """Lista templates de um usuário"""
        db_templates = self.db.query(Template).filter(
            Template.created_by == user_id
        ).offset(skip).limit(limit).order_by(Template.created_at.desc()).all()
        return [t.to_domain() for t in db_templates]
    
    def update(self, template: Template) -> Template:
        """Atualiza um template"""
        db_template = self.db.query(Template).filter(
            Template.id == template.id
        ).first()
        if not db_template:
            raise ValueError(f"Template com ID {template.id} não encontrado")
        
        db_template.name = template.name
        db_template.description = template.description
        db_template.template_type = template.template_type
        db_template.config = template.config
        db_template.thumbnail_url = template.thumbnail_url
        db_template.is_public = template.is_public
        
        self.db.commit()
        self.db.refresh(db_template)
        return db_template.to_domain()
    
    def delete(self, template_id: int) -> bool:
        """Deleta um template"""
        db_template = self.db.query(Template).filter(
            Template.id == template_id
        ).first()
        if not db_template:
            return False
        
        self.db.delete(db_template)
        self.db.commit()
        return True
    
    def increment_usage(self, template_id: int) -> bool:
        """Incrementa contador de uso"""
        db_template = self.db.query(Template).filter(
            Template.id == template_id
        ).first()
        if not db_template:
            return False
        
        db_template.usage_count += 1
        self.db.commit()
        return True

