from menu import Menu, MenuItem
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
# from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.text import format_lazy
def string_concat(*strings):
    return format_lazy('{}' * len(strings), *strings)

def about_children(request):
    children = []
    if settings.SITE_ID == 5:
        children.append (MenuItem(
             capfirst(_("cover page")),
             url='/we-collab/cover/',
            ))
    if not settings.SITE_ID == 1:
        children.append (MenuItem(
             # capfirst(string_concat(_('the site'), ' ', settings.SITE_NAME)),
             capfirst(_("this site")),
             url='/'+settings.SITE_NAME.lower()+'/info/',
            ))
    children.append (MenuItem(
         capfirst(_("the CommonS project")),
         url='/info/about/',
        ))
    children.append (MenuItem(
         capfirst(_("the platform")),
         url='/info/platform/',
         ))
    if settings.SITE_ID == 1:
        children.append (MenuItem(
             capfirst(_("press releases")),
             url='/press_releases/',
            ))
    return children

def projects_children(request):
    children = []
    if settings.SITE_ID == 1:
        children.append (MenuItem(
         capfirst(_("all communities")),
         url='/cops/',
        ))
        children.append (MenuItem(
             capfirst(_("browse mentors")),
             url='/browse_mentors/',
        ))
    else:
        children.append (MenuItem(
         capfirst(_("projects tree")),
         url='/cops/',
        ))
    children.append (MenuItem(
         capfirst(_("search projects")),
         url='/projects/search',
        ))
    """
    children.append (MenuItem(
         capfirst(_("top contributors")),
         url='/resources/contributors/',
        ))
    """
    children.append (MenuItem(
         capfirst(_("forums")),
         url='/forum/',
        ))
    if request.user.is_authenticated:
        children.append (MenuItem(
             capfirst(_("browse people")),
             url='/browse_people/',
            ))
        children.append (MenuItem(
             capfirst(_("search people")),
             url='/people/search/',
            ))
    if settings.SITE_ID in [3, 4, 5]: # HEALTH, WE-COLLAB
        children.append (MenuItem(
         capfirst(_("seach documents")),
         url='/documents/search/',
        ))
    return children

def resources_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("learning paths")),
         url='/lps/search/',
        ))
    children.append (MenuItem(
         capfirst(_("open resources")),
         url='/oers/search/',
        ))
    if settings.SITE_ID == 1:
        children.append (MenuItem(
             capfirst(_("source repositories")),
             url='/repos/search/',
            ))
    children.append (MenuItem(
         capfirst(_("all resources")),
         # url='/repos/',
         url='/browse/',
        ))
    return children

def my_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("my dashboard")),
         url='/my_home/',
        ))
    children.append (MenuItem(
         capfirst(_("my projects")),
         url='/my_projects/',
        ))
    if request.user.is_staff: # CS, WE-COLLAB
        children.append (MenuItem(
             capfirst(_("my activity")),
             url='/my_activity/',
            ))
    # new, test only:
    children.append (MenuItem(
         capfirst(_("my contents")),
         url='/my_contents/',
        ))
    children.append (MenuItem(
         capfirst(_("text analysis")),
         url='/textanalysis/ta_input/',
        ))
    if settings.SITE_ID in [5]:
        children.append (MenuItem(
             capfirst(_("student feedback")),
             url='/feedback/attendee/',
            ))
    return children

def help_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("tutorials")),
         url='/help/tutorials/',
        ))
    children.append (MenuItem(
         capfirst(_("registration and authentication")),
         url='/help/register/',
        ))
    children.append (MenuItem(
         capfirst(_("user profile and user roles")),
         url='/help/profile/',
        ))
    children.append (MenuItem(
         capfirst(_("site navigation")),
         url='/help/navigation/',
        ))
    children.append (MenuItem(
         capfirst(_("communities and projects")),
         url='/help/community/',
        ))
    children.append (MenuItem(
         capfirst(_("searching the catalogued resources")),
         url='/help/search/',
        ))
    children.append (MenuItem(
         capfirst(_("open resources")),
         url='/help/oer/',
        ))
    children.append (MenuItem(
         capfirst(_("learning paths")),
         url='/help/lp/',
        ))
    children.append (MenuItem(
         capfirst(_("mentoring")),
         url='/help/mentoring/',
        ))
    children.append (MenuItem(
         capfirst(_("analytics")),
         url='/help/analytics/',
        ))
    children.append (MenuItem(
         capfirst(_("internationalization")),
         url='/info/i18n/',
        ))
    children.append (MenuItem(
         capfirst(_("translation")),
         url='/info/translation/',
        ))
    children.append (MenuItem(
         capfirst(_("content evaluation")),
         url='/help/evaluation/',
        ))
    children.append (MenuItem(
         capfirst(_("editorial tools")),
         url='/help/editorial/',
        ))
    return children

def admin_children(request):
    children = []
    user = request.user
    if user.is_superuser or (user.is_authenticated):
        children.append (MenuItem(
             capfirst(_("activity stream")),
             url='/analytics/activity_stream/',
            ))
        children.append (MenuItem(
             capfirst(_("forums")),
             url='/analytics/forums/',
            ))
        children.append (MenuItem(
             capfirst(_("messages")),
             url='/analytics/messages/',
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
Menu.add_item("main", MenuItem(capfirst(_("projects")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=projects_children,
                               separator=True))     
Menu.add_item("main", MenuItem(capfirst(_("resources")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=resources_children,
                               separator=True))
#if settings.SITE_ID in [1, 5,]:
Menu.add_item("main", MenuItem(capfirst(_("my spaces")),
                               url='/p',
                               weight=30,
                               check=lambda request: request.user.is_authenticated,
                               children=my_children,
                               separator=True))
Menu.add_item("main", MenuItem(capfirst(_("help")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=help_children,
                               separator=True))
