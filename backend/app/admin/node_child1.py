from django.contrib import admin
from .base_node import BaseNodeAdmin
from ..models.node_child1 import NodeChild1


@admin.register(NodeChild1)
class NodeChild1Admin(BaseNodeAdmin):
    pass
