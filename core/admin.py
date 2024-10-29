from django.contrib import admin

from core.models import PasswordSetupToken, User


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)


class PasswordSetupTokenAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "token")
    list_display = (
        "id",
        "user",
        "used",
    )


admin.site.register(PasswordSetupToken, PasswordSetupTokenAdmin)
