# Django
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView

# Third Party
from rest_framework import routers

# Squarelet
from squarelet.organizations.viewsets import ChargeViewSet, OrganizationViewSet
from squarelet.users.viewsets import UrlAuthTokenViewSet, UserViewSet

router = routers.DefaultRouter()
router.register("users", UserViewSet)
router.register("url_auth_tokens", UrlAuthTokenViewSet, base_name="url_auth_token")
router.register("organizations", OrganizationViewSet)
router.register("charges", ChargeViewSet)

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "selectplan/",
        TemplateView.as_view(template_name="pages/selectplan.html"),
        name="select_plan",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("squarelet.users.urls", namespace="users")),
    path(
        "organizations/",
        include("squarelet.organizations.urls", namespace="organizations"),
    ),
    path("accounts/", include("allauth.urls")),
    path("api/", include(router.urls)),
    path("openid/", include("oidc_provider.urls", namespace="oidc_provider")),
    path("hijack/", include("hijack.urls", namespace="hijack")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
if "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
