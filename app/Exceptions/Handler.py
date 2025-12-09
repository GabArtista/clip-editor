from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para erros de validação"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Erro de validação",
            "errors": errors
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handler para erros do SQLAlchemy"""
    logger.error(f"Erro do banco de dados: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Erro interno do banco de dados",
            "detail": "Ocorreu um erro ao processar a requisição. Tente novamente mais tarde."
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handler para erros gerais"""
    logger.error(f"Erro inesperado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Erro interno do servidor",
            "detail": "Ocorreu um erro inesperado. Tente novamente mais tarde."
        }
    )


def setup_exception_handlers(app):
    """Configura handlers de exceção"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

