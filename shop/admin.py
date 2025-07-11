from django.contrib import admin
from .models import products , Order
# Register your models here.


class ManageProducts(admin.ModelAdmin):

    def change_discount_price(self, request, queryset):
        queryset.update(discount_price=0)
    change_discount_price.short_description = 'No discount'
    actions = ['change_discount_price']

    list_display = ('id', 'title', 'price', 'discount_price', 'category', 'description')
    search_fields = ('title', 'category')
    list_filter = ('category',)
    list_per_page = 10

    list_editable = ('price', 'discount_price', 'category')

admin.site.register(products, ManageProducts)
admin.site.register(Order)
