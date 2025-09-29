from pydantic import BaseModel, Field


class Copyright(BaseModel):
    """
    A model representing the copyright information and assets.

    This class contains URLs to various logo formats and the copyright text.
    """
    logo_vy: str | None = Field(default=None, description="Вертикальный цветной баннер (Vertical color banner)")
    logo_hy: str | None = Field(default=None, description="Горизонтальный цветной баннер (Horizontal color banner)")
    logo_vm: str | None = Field(default=None, description="Вертикальный монохромный баннер (Vertical monochrome banner)")
    logo_hm: str | None = Field(default=None, description="Горизонтальный монохромный баннер (Horizontal monochrome banner)")
    logo_vd: str | None = Field(default=None, description="Вертикальный черно-белый баннер (Vertical black-and-white banner)")
    logo_hd: str | None = Field(default=None, description="Горизонтальный черно-белый баннер (Horizontal black-and-white banner)")
    url: str | None = Field(default=None, description="URL Яндекс Расписаний (Yandex Schedules URL)")
    text: str | None = Field(default=None, description="Уведомительный текст (Notification text)")


class CopyrightRequest(BaseModel):
    """
    This request takes no parameters.
    """
    pass


class CopyrightResponse(BaseModel):
    """
    The response model containing copyright information.
    """
    copyright: Copyright | None = Field(default=None, description="The copyright data object")
