from menu import Menu, MenuItem
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
from django.conf import settings

def about_children(request):
    children = []
    children.append (MenuItem(
        capfirst(_("the Text Analysis project")),
        url='/info/about/',
        ))
    return children

def analysis_children(request):
    children = []
    children.append (MenuItem(
        capfirst(_("interactive text analyzer")),
        url='/ta_input/',
        ))
    if request.user.is_authenticated:
        children.append (MenuItem(
            capfirst(_("corpora")),
            url='/my_contents/',
            ))
    return children

def help_children(request):
    children = []
    children.append (MenuItem(
        capfirst(_("text analysis functions")),
        url='/help/text-analysis/',
        ))
    children.append (MenuItem(
        capfirst(_("working with corpora")),
        url='/help/corpora/',
        ))
    return children

Menu.items = {}
Menu.sorted = {}

# Add a few items to our main menu
Menu.add_item("main", MenuItem(capfirst(_("about")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=about_children,
                               separator=True))
Menu.add_item("main", MenuItem(capfirst(_("my spaces")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=analysis_children,
                               separator=True))
Menu.add_item("main", MenuItem(capfirst(_("help")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=help_children,
                               separator=True))
