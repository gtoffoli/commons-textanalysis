
from django.utils.translation import gettext_lazy as _
from django import forms
from dal import autocomplete

from django.conf import settings
if 'commons' in settings.INSTALLED_APPS:
    from commons.models import OER

TA_FUNCTION_CHOICES = (
    ('dependency', _('Dependency parse')),
    ('context', _('Keywords In Context')),
    ('wordlists', _('Word Lists by POS')),
    ('annotations', _('Annotated text')),
    ('nounchunks', _('Entities and terms')),
    ('readability', _('Text Readability')),
    ('cohesion', _('Text Cohesion')),
    ('summarization', _('Text Summarization')),
    ('dashboard', _('Text Analysis Dashboard')),
)

class TextAnalysisInputForm(forms.Form):
    text = forms.CharField(required=True, label=_('text to analyze'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 10, 'cols': 120,}), help_text=_('short text of a few paragraphs, or url of a web page'))
    function = forms.ChoiceField(required=True, choices=TA_FUNCTION_CHOICES, label=_('text-analysis function'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('select one'))
    if 'commons' in settings.INSTALLED_APPS:
        glossary = forms.ModelChoiceField(required=False, label=_('glossary'), queryset=OER.objects.all().order_by('title'), widget=autocomplete.ModelSelect2(url='/textanalysis/glossary-autocomplete/', attrs={'style': 'width: 100%;'}), help_text=_('auto-complete search; the selected glossary, if any, is used only by a few functions'))
    # domains = forms.MultipleChoiceField(required=True, choices=WIKIPEDIA_DOMAINS, label=_('Wikipedia/Babelnet domains'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('used only by a few functions; currently applies only to English texts'))
