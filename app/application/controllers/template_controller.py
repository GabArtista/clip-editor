from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.infrastructure.database.base import get_db
from app.infrastructure.repositories import TemplateRepository
from app.domain.entities.user import User
from app.application.auth import get_current_user
from app.application.dto.template_dto import (
    TemplateCreateDTO,
    TemplateUpdateDTO,
    TemplateResponseDTO
)

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])


@router.post("", response_model=TemplateResponseDTO, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: TemplateCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria um novo template"""
    try:
        from app.domain.entities.template import Template
        
        template_repo = TemplateRepository(db)
        
        template = Template(
            name=template_data.name,
            description=template_data.description,
            template_type=template_data.template_type,
            config=template_data.config,
            thumbnail_url=template_data.thumbnail_url,
            is_public=template_data.is_public,
            created_by=current_user.id
        )
        
        created = template_repo.create(template)
        
        return TemplateResponseDTO(
            id=created.id,
            name=created.name,
            description=created.description,
            template_type=created.template_type,
            config=created.config,
            thumbnail_url=created.thumbnail_url,
            is_public=created.is_public,
            created_by=created.created_by,
            usage_count=created.usage_count,
            created_at=created.created_at.isoformat() if created.created_at else None,
            updated_at=created.updated_at.isoformat() if created.updated_at else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar template: {str(e)}"
        )


@router.get("/public", response_model=List[TemplateResponseDTO])
def list_public_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista templates públicos"""
    try:
        template_repo = TemplateRepository(db)
        templates = template_repo.get_public_templates(skip=skip, limit=limit)
        
        return [
            TemplateResponseDTO(
                id=t.id,
                name=t.name,
                description=t.description,
                template_type=t.template_type,
                config=t.config,
                thumbnail_url=t.thumbnail_url,
                is_public=t.is_public,
                created_by=t.created_by,
                usage_count=t.usage_count,
                created_at=t.created_at.isoformat() if t.created_at else None,
                updated_at=t.updated_at.isoformat() if t.updated_at else None
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar templates: {str(e)}"
        )


@router.get("/my", response_model=List[TemplateResponseDTO])
def list_my_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista templates do usuário atual"""
    try:
        template_repo = TemplateRepository(db)
        templates = template_repo.get_user_templates(current_user.id, skip=skip, limit=limit)
        
        return [
            TemplateResponseDTO(
                id=t.id,
                name=t.name,
                description=t.description,
                template_type=t.template_type,
                config=t.config,
                thumbnail_url=t.thumbnail_url,
                is_public=t.is_public,
                created_by=t.created_by,
                usage_count=t.usage_count,
                created_at=t.created_at.isoformat() if t.created_at else None,
                updated_at=t.updated_at.isoformat() if t.updated_at else None
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=TemplateResponseDTO)
def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Obtém um template por ID"""
    try:
        template_repo = TemplateRepository(db)
        template = template_repo.get_by_id(template_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template não encontrado"
            )
        
        # Incrementa uso se for público
        if template.is_public:
            template_repo.increment_usage(template_id)
        
        return TemplateResponseDTO(
            id=template.id,
            name=template.name,
            description=template.description,
            template_type=template.template_type,
            config=template.config,
            thumbnail_url=template.thumbnail_url,
            is_public=template.is_public,
            created_by=template.created_by,
            usage_count=template.usage_count,
            created_at=template.created_at.isoformat() if template.created_at else None,
            updated_at=template.updated_at.isoformat() if template.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar template: {str(e)}"
        )


@router.put("/{template_id}", response_model=TemplateResponseDTO)
def update_template(
    template_id: int,
    template_data: TemplateUpdateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza um template"""
    try:
        template_repo = TemplateRepository(db)
        template = template_repo.get_by_id(template_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template não encontrado"
            )
        
        # Verifica se é o dono
        if template.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para editar este template"
            )
        
        # Atualiza campos
        update_data = template_data.dict(exclude_unset=True)
        if "name" in update_data:
            template.name = update_data["name"]
        if "description" in update_data:
            template.description = update_data["description"]
        if "template_type" in update_data:
            template.template_type = update_data["template_type"]
        if "config" in update_data:
            template.config = update_data["config"]
        if "thumbnail_url" in update_data:
            template.thumbnail_url = update_data["thumbnail_url"]
        if "is_public" in update_data:
            template.is_public = update_data["is_public"]
        
        updated = template_repo.update(template)
        
        return TemplateResponseDTO(
            id=updated.id,
            name=updated.name,
            description=updated.description,
            template_type=updated.template_type,
            config=updated.config,
            thumbnail_url=updated.thumbnail_url,
            is_public=updated.is_public,
            created_by=updated.created_by,
            usage_count=updated.usage_count,
            created_at=updated.created_at.isoformat() if updated.created_at else None,
            updated_at=updated.updated_at.isoformat() if updated.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar template: {str(e)}"
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deleta um template"""
    try:
        template_repo = TemplateRepository(db)
        template = template_repo.get_by_id(template_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template não encontrado"
            )
        
        # Verifica se é o dono
        if template.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para deletar este template"
            )
        
        success = template_repo.delete(template_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template não encontrado"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar template: {str(e)}"
        )

