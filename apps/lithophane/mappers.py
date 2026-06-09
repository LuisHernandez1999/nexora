"""Mapper Model->dict do rascunho de lithophane (para template e JSON do endpoint)."""
from __future__ import annotations

from typing import Any

from apps.core.layers import BaseMapper

from .models import LithophaneDraft


class LithophaneMapper(BaseMapper[LithophaneDraft]):
    @classmethod
    def to_dict(cls, instance: LithophaneDraft) -> dict[str, Any]:
        return {
            "draft_id": instance.pk,
            "format": instance.format,
            "format_label": instance.get_format_display(),
            "size": float(instance.size),
            "thickness": float(instance.thickness),
            "image_url": instance.image.url if instance.image else "",
            "glb_url": instance.model_glb.url if instance.model_glb else "",
            "stl_url": instance.model_stl.url if instance.model_stl else "",
        }
