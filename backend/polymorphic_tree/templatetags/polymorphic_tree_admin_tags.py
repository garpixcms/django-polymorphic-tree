from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node, TemplateSyntaxError, Variable
from django.utils.safestring import mark_safe
from future.builtins import next
from mptt.templatetags.mptt_tags import cache_tree_children
from polymorphic_tree.templatetags.stylable_admin_list import stylable_column_repr
from django.utils.translation import gettext as _

register = Library()


@register.filter
def real_model_name(node):
    # Allow upcasted model to work.
    # node.get_real_instance_class().__name__ would also work
    return ContentType.objects.get_for_id(node.polymorphic_ctype_id).model


@register.filter
def mptt_breadcrumb(node):
    """
    Return a breadcrumb of nodes, for the admin breadcrumb
    """
    if node is None:
        return []
    else:
        return list(node.get_ancestors())


class AdminListRecurseTreeNode(Node):

    def __init__(self, template_nodes, cl_var):
        self.template_nodes = template_nodes
        self.cl_var = cl_var

    @classmethod
    def parse(cls, parser, token):
        bits = token.contents.split()
        if len(bits) != 2:
            raise TemplateSyntaxError('%s tag requires an admin ChangeList' % bits[0])

        cl_var = Variable(bits[1])

        template_nodes = parser.parse(('endadminlist_recursetree',))
        parser.delete_first_token()
        return cls(template_nodes, cl_var)

    def _render_node(self, context, cl, node, level=0):
        bits = []
        context.push()

        # Render children to add to parent later
        for child in node.get_children():
            bits.append(self._render_node(context, cl, child, level=level+1))

        columns = self._get_column_repr(cl, node)  # list(tuple(name, html), ..)
        first_real_column = next(col for col in columns if col[0] != 'action_checkbox')

        context['columns'] = columns
        context['other_columns'] = [col for col in columns if col[0] not in ('action_checkbox', first_real_column[0])]
        context['first_column'] = first_real_column[1]
        context['named_columns'] = dict(columns)
        context['node'] = node
        context['change_url'] = cl.url_for_result(node)
        context['children'] = mark_safe(u''.join(bits))
        context['level'] = level
        context['margin_left'] = -level * 12

        # Render
        rendered = self.template_nodes.render(context)
        context.pop()
        return rendered

    def render(self, context):
        cl = self.cl_var.resolve(context)
        assert isinstance(cl, ChangeList), "cl variable should be an admin ChangeList"  # Also assists PyCharm
        roots = cache_tree_children(cl.result_list)
        bits = [self._render_node(context, cl, node) for node in roots]
        return ''.join(bits)

    def _get_column_repr(self, cl, node):
        columns = []
        for field_name in cl.list_display:
            html, row_class_ = stylable_column_repr(cl, node, field_name)
            columns.append((field_name, html))
        return columns


def add_node(obj, current_path, top_nodes, parent_attr, root_level, is_filtered, queryset):
    # Get the current mptt node level
    node_level = obj.get_level()

    parent = obj.parent

    if parent is not None and len(top_nodes) == 0:
        root_level = parent.get_level()
        add_node(parent, current_path, top_nodes, parent_attr, root_level, is_filtered, queryset)

    if node_level < root_level:
        # ``queryset`` was a list or other iterable (unable to order),
        # and was provided in an order other than depth-first
        raise ValueError(
            _("Node %s not in depth-first order") % (type(queryset),)
        )

    # Set up the attribute on the node that will store cached children,
    # which is used by ``MPTTModel.get_children``
    obj._cached_children = []

    # Remove nodes not in the current branch
    while len(current_path) > node_level - root_level:
        current_path.pop(-1)

    if node_level == root_level:
        # Add the root to the list of top nodes, which will be returned
        top_nodes.append(obj)
    else:
        # Cache the parent on the current node, and attach the current
        # node to the parent's list of children
        _parent = current_path[-1]
        setattr(obj, parent_attr, _parent)
        _parent._cached_children.append(obj)

        if root_level == 0:
            # get_ancestors() can use .parent.parent.parent...
            setattr(obj, "_mptt_use_cached_ancestors", True)

    # Add the current node to end of the current path - the last node
    # in the current path is the parent for the next iteration, unless
    # the next iteration is higher up the tree (a new branch), in which
    # case the paths below it (e.g., this one) will be removed from the
    # current path during the next iteration
    current_path.append(obj)


def get_tree(queryset):

    current_path = []
    top_nodes = []

    if queryset:
        # Get the model's parent-attribute name
        parent_attr = queryset[0]._mptt_meta.parent_attr
        root_level = None
        is_filtered = hasattr(queryset, "query") and queryset.query.has_filters()
        for obj in queryset:
            node_level = obj.get_level()
            if node_level == 0:
                current_path.clear()
            if len(current_path) == 0:
                root_level = node_level
            else:
                root_level = current_path[0].get_level()
            add_node(obj, current_path, top_nodes, parent_attr, root_level, is_filtered, queryset)

    return top_nodes


@register.tag
def adminlist_recursetree(parser, token):
    """
    Very similar to the mptt recursetree, except that it also returns the styled admin code.
    """
    return AdminListRecurseTreeNode.parse(parser, token)
