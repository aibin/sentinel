from django.contrib import admin

from core.models import PasswordToken, User


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)


class PasswordTokenAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "token")
    list_display = (
        "id",
        "user",
        "used",
    )


admin.site.register(PasswordToken, PasswordTokenAdmin)
