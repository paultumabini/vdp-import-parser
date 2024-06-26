from django import forms

from .models import FtpConfig


class FtpConfigForm(forms.ModelForm):
    class Meta:
        model = FtpConfig
        fields = '__all__'
        widgets = {
            'feed_ids': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
        }
