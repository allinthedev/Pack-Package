from django.contrib import admin

from .models import Item, MoneyInstance

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    autocomplete_fields = ("special",)
    save_on_top = True
    fieldsets = [
        (None, {"fields": ["name", "description", "prize"]}),
        ("Configure Reward", {"fields": ["minimum_rarity", "maximum_rarity", "special"]})
    ]
    list_display = ("name", "prize", "minimum_rarity", "maximum_rarity")
    list_editable = ("prize", "minimum_rarity", "maximum_rarity")
    list_filter = ("created_at", "special")
    ordering = ["-created_at"]

    search_fields = ("name",)

@admin.register(MoneyInstance)
class MoneyInstanceAdmin(admin.ModelAdmin):
    ...