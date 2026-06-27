from django import forms


class ChatQuestionForm(forms.Form):
    question = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)
