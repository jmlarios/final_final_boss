from django import forms

class MenuUploadForm(forms.Form):
    menu_pdf = forms.FileField(label="Menu PDF")  # Only keep the PDF field
