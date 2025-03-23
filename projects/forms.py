from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group, Permission
from .models import Project, Task, UserProfile


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="كلمة المرور:"
    )

    whatsapp_number = forms.CharField(
        max_length=15,
        required=False,
        label="رقم الواتساب:",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = [
            'username', 'password', 'first_name', 'last_name', 'email', 'whatsapp_number', 
            'is_superuser', 'is_active'
        ]
        labels = {
            'is_superuser': 'صلاحيات المدير:',
        }
        help_texts = {
            'username': '',
        }
        widgets = {
            'is_superuser': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['whatsapp_number'].initial = self.instance.profile.whatsapp_number
       

class ProfileForm(forms.ModelForm):
    whatsapp_number = forms.CharField(
        max_length=20,
        required=True,
        label="رقم الواتساب:",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['whatsapp_number'].initial = self.instance.profile.whatsapp_number

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            self.save_m2m()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.whatsapp_number = self.cleaned_data.get('whatsapp_number')
            profile.save()

        return user

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description'] 
        
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'
        can_delete=False
        widgets = {
            'id': forms.HiddenInput(),
            'task_name': forms.HiddenInput(),
            'status': forms.HiddenInput(),
            'start_date': forms.HiddenInput(),
            'end_date': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if field_name != 'assigned_to':
                field.widget.attrs['readonly'] = True
            else:
                field.widget.attrs['class'] = 'form-control'

class TaskFilterForm(forms.Form):
    status = forms.MultipleChoiceField(
        choices= Task.STATUS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "custom-checkbox"})
    )
