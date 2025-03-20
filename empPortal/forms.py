from django import forms
from .models import DocumentUpload

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = DocumentUpload
        fields = "__all__"
