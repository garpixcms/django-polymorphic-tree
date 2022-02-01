from django.db import models
from polymorphic_tree.models import PolymorphicMPTTModel, PolymorphicTreeForeignKey, PolymorphicMPTTModelManager


class Node(PolymorphicMPTTModel):
    """
    Нода дерева
    """
    title = models.CharField(max_length=255, verbose_name='Название')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    parent = PolymorphicTreeForeignKey('self', null=True, blank=True, related_name='children',
                                       db_index=True, verbose_name='Родительская страница', on_delete=models.SET_NULL,
                                       limit_choices_to={})

    objects = PolymorphicMPTTModelManager()

    class Meta(PolymorphicMPTTModel.Meta):
        verbose_name = 'Нода дерева'
        verbose_name_plural = 'Ноды дерева'
        ordering = ('created_at', 'title',)

    def __str__(self):
        return self.title
