from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from app.models import Appointment, DoctorProfile, User


from notifications.notification_services import NotificationService


class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    extra = 0
    readonly_fields = ('applied_at',)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Hospital Profile', {'fields': ('role', 'phone', 'address')}),
    )
    inlines = [DoctorProfileInline]


@admin.action(description="Approve selected doctor applications")
def approve_doctors(modeladmin, request, queryset):
    updated = 0
    for profile in queryset:
        if not profile.approved:
            profile.approved = True
            profile.save()
            updated += 1
            NotificationService.send_notification(
                recipient=profile.user,
                actor=request.user,
                title="Doctor Profile Approved 🎉",
                message="Congratulations! Your doctor profile has been verified and approved by hospital administration. You can now receive patient appointments.",
                target_obj=profile,
                category="approval",
                type="success"
            )
    modeladmin.message_user(request, f"Approved {updated} doctor application(s). Notifications sent.")


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'approved', 'applied_at')
    list_filter = ('approved', 'specialty')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    actions = [approve_doctors]

    def save_model(self, request, obj, form, change):
        if change:
            orig = DoctorProfile.objects.get(pk=obj.pk)
            if not orig.approved and obj.approved:
                NotificationService.send_notification(
                    recipient=obj.user,
                    actor=request.user,
                    title="Doctor Profile Approved 🎉",
                    message="Congratulations! Your doctor profile has been verified and approved by hospital administration. You can now receive patient appointments.",
                    target_obj=obj,
                    category="approval",
                    type="success"
                )
        elif obj.approved:
            NotificationService.send_notification(
                recipient=obj.user,
                actor=request.user,
                title="Doctor Profile Approved 🎉",
                message="Congratulations! Your doctor profile has been verified and approved by hospital administration. You can now receive patient appointments.",
                target_obj=obj,
                category="approval",
                type="success"
            )
        super().save_model(request, obj, form, change)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'specialty', 'requested_date', 'status', 'created_at')
    list_filter = ('status', 'specialty')
    search_fields = ('patient__username', 'doctor__username', 'reason')
    readonly_fields = ('created_at',)
