from django.contrib import admin
from .base_node import BaseNodeAdmin
from ..models.node_child2 import NodeChild2


@admin.register(NodeChild2)
class NodeChild2Admin(BaseNodeAdmin):
    pass
