from django.db import models
from polymorphic_tree.models import PolymorphicMPTTModel, PolymorphicTreeForeignKey, PolymorphicMPTTModelManager
from .node import Node


class NodeChild2(Node):
    """
    Нода дерева
    """
    pass

    class Meta(PolymorphicMPTTModel.Meta):
        verbose_name = 'Нода дерева child 2'
        verbose_name_plural = 'Ноды дерева child 2'
        ordering = ('created_at', 'title',)

    def __str__(self):
        return self.title
