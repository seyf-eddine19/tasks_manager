from django.urls import reverse_lazy, reverse
from django.forms import HiddenInput, inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Case, When, IntegerField, F, Q

from django.views.generic import TemplateView, RedirectView, ListView, FormView, DetailView, DeleteView

from .models import Project, Task, UserProfile
from .forms import (
    UserForm, ProfileForm , ProjectForm, TaskForm, TaskFilterForm
)

def custom_403(request, exception):
    return render(request, '403.html', {}, status=403)

def custom_404(request, exception):
    return render(request, '404.html', {}, status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

class IndexView(LoginRequiredMixin, TemplateView):
    """عرض الصفحة الرئيسية"""
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # البيانات العامة
        context["total_projects"] = Project.objects.count()
        context["total_tasks"] = Task.objects.count()
        context["completed_tasks"] = Task.objects.filter(status="مكتمل").count()
        in_progress_tasks = Task.objects.filter(status="قيد التنفيذ").count()
        pending_tasks = Task.objects.filter(status="معلق").count()
        context["total_users"] = User.objects.count()

        # حساب نسبة المهام المكتملة لكل مستخدم
        context["user_task_stats"] = User.objects.annotate(
            total_tasks=Count(Case(When(Q(task__status="قيد التنفيذ") | Q(task__status="مكتمل") | Q(task__status="معلق") | Q(task__status="لم يبدأ بعد"), then=1), output_field=IntegerField())),
            notstart_tasks=Count(Case(When(task__status="لم يبدأ بعد", then=1), output_field=IntegerField())),
            inprogress_tasks=Count(Case(When(task__status="قيد التنفيذ", then=1), output_field=IntegerField())),
            hold_tasks=Count(Case(When(task__status="معلق", then=1), output_field=IntegerField())),
            completed_tasks=Count(Case(When(task__status="مكتمل", then=1), output_field=IntegerField()))
        ).annotate(
            completion_rate=Case(
                When(total_tasks__gt=0, then=F('completed_tasks') * 100.0 / F('total_tasks')),
                default=Value(0),
                output_field=FloatField()
            )
        ).order_by('-completion_rate')

        context["projects"] = Project.objects.all()
        context["user"] = user

        return context

class LogoutView(LoginRequiredMixin, RedirectView):
    """تسجيل الخروج وإعادة التوجيه لصفحة تسجيل الدخول"""
    pattern_name = 'login'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)

class ProfileView(LoginRequiredMixin, FormView):
    """عرض وتحديث الملف الشخصي للمستخدم"""
    model = User
    form_class = ProfileForm
    success_url = reverse_lazy('profile')
    template_name = 'users/profile.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["password_form"] = PasswordChangeForm(self.request.user)
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'تم تحديث الملف الشخصي بنجاح!')
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        """التعامل مع تحديث الملف الشخصي وكلمة المرور"""
        form = self.get_form()
        password_form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            return self.form_valid(form)

        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'تم تحديث كلمة المرور بنجاح!')
            return self.form_valid(form)

        return self.form_invalid(form)


# Form Views Mixin
class FormViewMixin(FormView):
    def get_object(self):
        """Retrieve object if updating, or return None for creation."""
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(self.model, pk=pk)
        return None

    def get_form_kwargs(self):
        """Pass instance to form if updating"""
        kwargs = super().get_form_kwargs()
        obj = self.get_object()
        if obj:
            kwargs["instance"] = obj
        return kwargs

    def get_initial(self):
        """Prefill form with existing data if updating."""
        obj = self.get_object()
        if obj:
            return {field.name: getattr(obj, field.name) for field in obj._meta.fields}
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def get_success_url(self):
        """إعادة التوجيه إلى الصفحة السابقة إذا كانت موجودة"""
        return self.request.GET.get("next", self.success_url)

    def form_valid(self, form):
        """Validate form and handle saving"""
        obj = form.save(commit=False) 
        is_update = self.get_object() is not None 

        obj.save()
        self.object = obj 
        form.save_m2m()

        if is_update:
            messages.success(self.request, "تم تحديث البيانات بنجاح!")
        else:
            messages.success(self.request, "تم إضافة البيانات بنجاح!")

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        messages.error(self.request, "حدث خطأ أثناء حفظ البيانات. يرجى التحقق من المدخلات.")
        return super().form_invalid(form)


# User Views
class UserListView(PermissionRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'

class UserDetailView(PermissionRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    permission_required = 'auth.view_user'

class UserDeleteView(PermissionRequiredMixin, DeleteView):
    model = User
    template_name = 'users/user_delete.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'auth.delete_user'

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'تم حذف البيانات بنجاح.')
        return response

class UserFormView(PermissionRequiredMixin, FormViewMixin):
    model = User
    form_class = UserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')
    permission_required = ['auth.add_user', 'auth.change_user']


# Project Views
class ProjectListView(ListView):
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    # permission_required = 'projects.view_project'

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/detail.html'
    # permission_required = 'projects.view_project'

class ProjectDeleteView(PermissionRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/delete.html'
    success_url = reverse_lazy('project_list')
    permission_required = 'projects.delete_project'

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'تم حذف البيانات بنجاح.')
        return response

TaskFormSet = inlineformset_factory(Project, Task, form=TaskForm, can_delete=False, extra=0)

class ProjectFormView(PermissionRequiredMixin, FormViewMixin):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    success_url = reverse_lazy('project_update')
    permission_required = ['projects.add_project', 'projects.change_project']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()  # معرفة هل المشروع جديد أم تعديل

        if obj:  # عرض نموذج المهام فقط إذا كان المشروع يتم تعديله
            if self.request.POST:
                context['task_formset'] = TaskFormSet(self.request.POST, instance=obj)
            else:
                context['task_formset'] = TaskFormSet(instance=obj)
        else:
            context['task_formset'] = None  # عند الإنشاء، لا نظهر نموذج المهام

        return context

    def form_valid(self, form):
        """حفظ المشروع ثم حفظ المهام المرتبطة به إن وجدت"""
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        is_update = self.get_object() is not None  # معرفة هل هو تحديث أم إضافة جديدة
    
        obj.save()
        self.object = obj  
    
        # حفظ المهام إذا كان هناك تعديل
        if is_update:
            context = self.get_context_data()
            task_formset = context.get('task_formset')
    
            if task_formset.is_valid():
                # التحقق من تعيين المسؤول عن كل مهمة
                for form in task_formset:
                    if not form.cleaned_data.get('assigned_to'):
                        messages.error(self.request, "يجب تعيين مسؤول لكل مهمة.")
                        return redirect(reverse('project_update', kwargs={'pk': obj.pk}))
                task_formset.save()
    
                # بدء أول مهمة تلقائيًا إن لم تكن هناك مهام قيد التنفيذ
                tasks = obj.tasks.all()
                if tasks.exists() and all(task.status == 'لم يبدأ بعد' for task in tasks):
                    first_task = tasks.order_by('id').first()
                    if first_task:
                        first_task.status = 'قيد التنفيذ'
                        first_task.save(update_fields=['status', 'start_date'])
    
            else:
                messages.error(self.request, "حدث خطأ أثناء حفظ المهام.")
                return redirect(reverse('project_update', kwargs={'pk': obj.pk}))
    
        messages.success(self.request, "تم تحديث المشروع بنجاح!" if is_update else "تم إضافة المشروع بنجاح!")
        return redirect(reverse('project_update', kwargs={'pk': obj.pk}))


# Task Views
from urllib.parse import quote

def send_whatsapp(request, phone_number, message):
    """
    إعادة توجيه المستخدم إلى واتساب لفتح المحادثة مباشرة.
    """
    encoded_message = quote(message)  # تحويل النص إلى صيغة URL
    whatsapp_url = f"https://wa.me/{phone_number}/?text={encoded_message}"
    return redirect(whatsapp_url)


from urllib.parse import quote

def send_whatsapp(request, phone_number, message):
    """
    عرض صفحة تحتوي على أزرار لفتح WhatsApp أو العودة إلى قائمة المهام.
    """
    # ترميز الرسالة لتكون متوافقة مع URL
    encoded_message = quote(message)
    whatsapp_url = f"https://wa.me/{phone_number}/?text={encoded_message}"

    context = {
        'whatsapp_url': whatsapp_url,
        'task_list_url': reverse('task_list')  # رابط العودة إلى صفحة المهام
    }
    
    return render(request, 'tasks/send_whatsapp.html', context)


class TaskListView(ListView):
    model = Task
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'
    permission_required = 'projects.view_task'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        
        # 🔹 تقسيم المهام حسب المشروع ثم الحالة
        grouped_tasks = {}
        for task in self.get_queryset():
            project_title = task.project.title
            status = task.status
            
            if project_title not in grouped_tasks:
                grouped_tasks[project_title] = {}

            if status not in grouped_tasks[project_title]:
                grouped_tasks[project_title][status] = []

            grouped_tasks[project_title][status].append(task)

        context["grouped_tasks"] = grouped_tasks
        return context
    
    def get_queryset(self):
        queryset = Task.objects.select_related('project').filter(assigned_to=self.request.user)

        self.filter_form = TaskFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            status_filter = self.filter_form.cleaned_data.get("status")
            queryset = queryset.filter(status__in=status_filter) if status_filter else queryset

        return queryset.order_by('-start_date', '-id')

    def post(self, request, *args, **kwargs):
        """Handles task status update from buttons"""
        task_id = request.POST.get("task_id")
        action = request.POST.get("action")

        if task_id and action:
            task = get_object_or_404(Task, pk=task_id, assigned_to=request.user)
            if task:
                project = task.project
                if action == "complete" and task.status in ["قيد التنفيذ", "معلق"]:
                    total_tasks = project.tasks.count()
                    completed_tasks = project.tasks.filter(status="مكتمل").count() + 1  # Include the current task update                    

                    task.status = "مكتمل"
                    task.save()
                    messages.success(request, "تم إكمال المهمة!")
                    if completed_tasks == total_tasks:
                        project.status = "مكتمل"
                        project.save()
                        messages.success(request, f"تم إكمال جميع مهام المشروع {project}!")
                    else:
                        project.status = "قيد التنفيذ"
                        project.save()
                           
                elif action == "hold" and task.status == "قيد التنفيذ":
                    task.status = "معلق"
                    project.status = "معلق"
                    task.save()
                    project.save()
                    messages.warning(request, f"بعض المهام معلقة، تم تعليق المشروع {project}!")

        return redirect("task_list")
    def post(self, request, *args, **kwargs):
        task_id = request.POST.get("task_id")
        action = request.POST.get("action")
    
        if task_id and action:
            task = get_object_or_404(Task, pk=task_id, assigned_to=request.user)
            if task:
                project = task.project
                if action == "complete" and task.status in ["قيد التنفيذ", "معلق"]:
                    total_tasks = project.tasks.count()
                    completed_tasks = project.tasks.filter(status="مكتمل").count() + 1  
    
                    task.status = "مكتمل"
                    task.save()
                    messages.success(request, "تم إكمال المهمة!")
    
                    if completed_tasks == total_tasks:
                        project.status = "مكتمل"
                        project.save()
                        messages.success(request, f"تم إكمال جميع مهام المشروع {project}!")
                    else:
                        project.status = "قيد التنفيذ"
                        project.save()
                    
                    # 🔹 إرسال إشعار عبر واتساب إذا كانت هناك مهمة جديدة
                    next_task = project.tasks.filter(status="قيد التنفيذ").order_by('id').first()
                    if next_task and next_task.assigned_to:
                        phone_number = next_task.assigned_to.profile.whatsapp_number
                        message_body = f"لديك مهمة جديدة: {next_task.task_name} في مشروع {next_task.project.title}."
                        return redirect(reverse('send_whatsapp', args=[phone_number, message_body]))
    
                elif action == "hold" and task.status == "قيد التنفيذ":
                    task.status = "معلق"
                    project.status = "معلق"
                    task.save()
                    project.save()
                    messages.warning(request, f"بعض المهام معلقة، تم تعليق المشروع {project}!")
    
        return redirect("task_list")
    
