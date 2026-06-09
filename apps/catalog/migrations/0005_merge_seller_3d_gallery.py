"""Reconcilia os dois ramos de migração do catálogo após o merge.

Une o ramo de modelos 3D (model_3d/model_stl) com o ramo de
vendedor + galeria + avaliações, mantendo as duas features.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_merge_20260607_1521"),
        ("catalog", "0004_productimage_review_product_is_on_promotion_and_more"),
    ]

    operations = []
