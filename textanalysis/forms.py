
from django.utils.translation import gettext_lazy as _
from django import forms

TA_FUNCTION_CHOICES = (
    ('context', _('Keywords In Context')),
    ('wordlists', _('Word Lists by POS')),
    ('nounchunks', _('Noun chunks')),
    ('readability', _('Text Readability')),
    ('summarization', _('Text Summarization')),
    ('dashboard', _('Text Analysis Dashboard')),
)

class TextAnalysisInputForm(forms.Form):
    text = forms.CharField(required=True, label=_('text to analyze'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 10, 'cols': 120,}), help_text=_('short text of a few paragraphs, or url of a web page'))
    function = forms.ChoiceField(required=True, choices=TA_FUNCTION_CHOICES, label=_('text-analysis function'), widget=forms.Select(attrs={'class':'form-control',}))
