from .models import Comment
from django import forms


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        # 아래는 스타일 지정을 위해 임의로 추가함
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,  # 몇 줄을 디폴트로 보이게 할 것인지
                'style': 'height:90px;',  # row보다 우선순위, 디폴트로 보이는 textarea의 높이는?
                'placeholder': 'Join the discussion and leave a comment!',
            }),
        }
