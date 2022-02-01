from django.contrib import admin
from polymorphic_tree.admin import PolymorphicMPTTParentModelAdmin, PolymorphicMPTTChildModelAdmin
from django.conf import settings
from django.utils.translation import gettext as _
from polymorphic.admin import PolymorphicChildModelFilter
from ..models.node import Node
from ..models.node_child1 import NodeChild1
from ..models.node_child2 import NodeChild2


@admin.register(Node)
class NodeAdmin(PolymorphicMPTTParentModelAdmin):
    """
    Стандартные настройки для базовых страниц.
    """
    base_model = Node
    child_models = [NodeChild1, NodeChild2]
    list_per_page = 2

    empty_value_display = '- нет -'
    save_on_top = True
    view_on_site = True

    # date_hierarchy = 'created_at'
    # prepopulated_fields = {'slug': ('title',)}
    #
    # search_fields = ('title',)
    # list_filter = (PolymorphicChildModelFilter, 'is_active', 'created_at', 'updated_at', 'sites')
    # actions = ('clone_object', 'rebuild')
    #
    list_display = ('title', 'created_at', 'updated_at')
    # list_editable = ('is_active',)
    #
    # readonly_fields = ('created_at', 'updated_at', 'model_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'initial' in kwargs:
            self.fields['parent'].queryset = self.model.get_available_page_parents()
            self.fields['parent'].default = self.model.get_default_parent()

    def clone_object(self, request, queryset):
        """Копирование(клонирование) выбранных объектов - action"""
        for obj in queryset:
            prefix = '-CLONE'
            clone = obj
            clone.title += prefix
            clone.slug += prefix
            clone.id = None
            clone.is_active = False
            clone.save()

    clone_object.short_description = 'Клонировать объект'

    def _rebuild(self):
        try:
            self.model.objects.rebuild()
        except:  # noqa
            print('[ERROR]: Ошибка при перезагрузки древовидной структуры')

    def rebuild(self, request, queryset):
        """Пересорбать МПТТ модель. Иногда требуется для перезагрузки дерева."""
        self._rebuild()

    rebuild.short_description = 'Пересобрать пункты раздела'

    def save_model(self, request, obj, form, change):
        self._rebuild()
        super().save_model(request, obj, form, change)
