
from django.utils.translation import gettext_lazy as _
from django import forms
from dal import autocomplete

from django.conf import settings
if 'commons' in settings.INSTALLED_APPS:
    from commons.models import OER
    from commons.models import Language

from textanalysis.babelnet import bn_domains
FIELD_CHOICES = (('subjects', 'subjects'), ('definition', 'definition'), ('def_source', 'definition source'), ('POS', 'part of speech'), ('type', 'term type'), ('status', 'term status'), ('term_source', 'term source'), ('rel.', 'term reliability'),)
INITIAL_LANGUAGES_SELECTION = ('en',)
INITIAL_FIELDS_SELECTION = ('subjects', 'definition', 'POS', 'type',)

TA_FUNCTION_CHOICES = (
    # ('context', _('Keywords In Context')),
    ('wordlists', _('Words by POS and frequency, with contexts')),
    ('annotations', _('Annotated text')),
    ('nounchunks', _('Entities and terms')),
    ('readability', _('Text Readability')),
    ('cohesion', _('Text Cohesion')),
    ('dependency', _('Dependency parse')),
    # ('summarization', _('Text Summarization')),
    # ('dashboard', _('Text Analysis Dashboard')),
)

class TextAnalysisInputForm(forms.Form):
    text = forms.CharField(required=True, label=_('text to analyze'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 10, 'cols': 120,}), help_text=_('short text of a few paragraphs, or url of a web page'))
    function = forms.ChoiceField(required=True, choices=TA_FUNCTION_CHOICES, label=_('text-analysis function'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('select one'))
    if 'commons' in settings.INSTALLED_APPS:
        glossary = forms.ModelChoiceField(required=False, label=_('glossary'), queryset=OER.objects.all().order_by('title'), widget=autocomplete.ModelSelect2(url='/textanalysis/glossary-autocomplete/', attrs={'style': 'width: 100%;'}), help_text=_('auto-complete search; the selected glossary, if any, is used only by a few functions'))
    # domains = forms.MultipleChoiceField(required=True, choices=WIKIPEDIA_DOMAINS, label=_('Wikipedia/Babelnet domains'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('used only by a few functions; currently applies only to English texts'))

class GlossaryUploadForm(forms.Form):
    glossary = forms.FileField(required=True,
        label=_('select a file'),
        widget=forms.FileInput(attrs={'class': 'btn btn-default', 'data-buttonText':_("choose file"), 'accept': '.tbx,.csv'}), help_text=_("select a .tbx file in TBX-IATE format; a TAB-separated .csv file can also work for simple cases"))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 3,}), help_text=_('select/deselect languages: needed only for new languages when editing the glossary'))
    domains = forms.MultipleChoiceField(required=False, choices=bn_domains, label=_('Wikipedia/Babelnet domains'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 4,}), help_text=_('select/deselect domains: needed only for new domains when editing the glossary'))

class GlossaryCreateForm(forms.Form):
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'form-control', 'style':'width: 50ch;',}), help_text=_("glossary title"),)
    source = forms.CharField(required=False, label=_('source'), widget=forms.TextInput(attrs={'class':'form-control', 'style':'width: 50ch;',}), help_text=_("overall glossary source: organization and/or author(s)"),)
    languages = forms.ModelMultipleChoiceField(required=True, label=_('languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 3,}), help_text=_('select/deselect used languages: choose one at least'))
    domains = forms.MultipleChoiceField(required=False, choices=bn_domains, label=_('Wikipedia/Babelnet domains'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 4,}), help_text=_('select/deselect domains available to classify concepts'))
    optional_fields = forms.MultipleChoiceField(required=False, choices=FIELD_CHOICES, label=_('optional fields'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}), help_text=_('select/deselect used fields (columns) related to concepts and terms'))
