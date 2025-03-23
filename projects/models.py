from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from .utils import send_whatsapp_message


# Extending User Model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="WhatsApp Number")

    def __str__(self):
        return f"{self.user.username} - {self.whatsapp_number if self.whatsapp_number else 'No WhatsApp'}"


class Project(models.Model):
    STATUS_CHOICES = [
        ('لم يبدأ بعد', 'لم يبدأ بعد'),
        ('قيد التنفيذ', 'قيد التنفيذ'),
        ('مكتمل', 'مكتمل'),
        ('معلق', 'معلق'),
    ]

    title = models.CharField(max_length=255, verbose_name='اسم المشروع')
    description = models.TextField(blank=True, null=True, verbose_name='وصف المشروع')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='لم يبدأ بعد', verbose_name='حالة المشروع')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='تاريخ الإنشاء')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='منشئ المشروع')

    def current_task(self):
        """ إرجاع أول مهمة لم تكتمل بعد """
        current_task = self.tasks.filter(status__in=['قيد التنفيذ']).order_by('start_date').first()
        return current_task.task_name if current_task else "لا توجد مهام حالية"

    def create_default_tasks(self):
        tasks = [
            'اختيار الموضوع',
            'كتابة المحتوى',
            'التسجيل',
            'المونتاج',
            'الثامنايل',
            'الرفع'
        ]
        
        for task_name in tasks:
            Task.objects.create(
                project=self,
                task_name=task_name,
                status='لم يبدأ بعد'
            )

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # التحقق مما إذا كان المشروع جديدًا
        super().save(*args, **kwargs)  # حفظ المشروع أولًا

        if is_new:
            self.create_default_tasks()  # إنشاء المهام تلقائيًا عند إنشاء مشروع جديد
        else:
            # تحقق مما إذا كانت جميع المهام لم تبدأ بعد
            tasks = self.tasks.all()
            if tasks.exists() and all(task.status == 'لم يبدأ بعد' for task in tasks):
                first_task = tasks.order_by('id').first()
                if first_task:
                    first_task.status = 'قيد التنفيذ'
                    first_task.start_date = timezone.now().date()
                    first_task.save()

    def __str__(self):
        return self.title


class Task(models.Model):
    TASK_CHOICES = [
        ('اختيار الموضوع', 'اختيار الموضوع'),
        ('كتابة المحتوى', 'كتابة المحتوى'),
        ('التسجيل', 'التسجيل'),
        ('المونتاج', 'المونتاج'),
        ('الثامنايل', 'الثامنايل'),
        ('الرفع', 'الرفع'),
    ]

    STATUS_CHOICES = [
        ('لم يبدأ بعد', 'لم يبدأ بعد'),
        ('قيد التنفيذ', 'قيد التنفيذ'),
        ('مكتمل', 'مكتمل'),
        ('معلق', 'معلق'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    task_name = models.CharField(max_length=50, choices=TASK_CHOICES)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='قيد التنفيذ')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


    def save(self, *args, **kwargs):
        # تحديث تاريخ البدء عند تعيين المهمة "قيد التنفيذ"
        if self.status == "قيد التنفيذ":
            self.start_date = timezone.now().date()

        # عند اكتمال المهمة، حدد تاريخ الانتهاء وابحث عن المهمة التالية
        elif self.status == "مكتمل":
            self.end_date = timezone.now().date()

            # البحث عن المهمة التالية التي لم تبدأ بعد

            next_task = self.project.tasks.filter(status="لم يبدأ بعد").order_by('id').first()
            if next_task:
                next_task.status = "قيد التنفيذ"
                next_task.start_date = timezone.now().date()
                next_task.save()

                recipient_number = f"whatsapp:+{next_task.assigned_to.profile.whatsapp_number}"
                message_body = f"لديك مهمة {next_task}"
                print(recipient_number)
                send_whatsapp_message(recipient_number, message_body)
                     

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project.title} - {self.task_name} ({self.status})"
