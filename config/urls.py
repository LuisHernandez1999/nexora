"""Roteamento raiz do Nexora."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
    path("", include("apps.core.urls")),
    path("conta/", include("apps.accounts.urls")),
    path("catalogo/", include("apps.catalog.urls")),
    path("promocoes/", include("apps.promotions.urls")),
    path("vendedor/", include("apps.seller.urls")),
    path("carrinho/", include("apps.cart.urls")),
    path("pedidos/", include("apps.orders.urls")),
    path("lithophane/", include("apps.lithophane.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
