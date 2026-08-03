from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from app.models import Appointment, DoctorProfile, DoctorWorkingHours, User
from notifications.notification_services import NotificationService


class DoctorWorkingHoursInline(admin.TabularInline):
    model = DoctorWorkingHours
    extra = 0


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
    inlines = [DoctorProfileInline, DoctorWorkingHoursInline]


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
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    actions = [approve_doctors]


@admin.register(DoctorWorkingHours)
class DoctorWorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day', 'start_time', 'end_time', 'is_available')
    list_filter = ('day', 'is_available')
    search_fields = ('doctor__email', 'doctor__first_name', 'doctor__last_name')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'specialty', 'requested_date', 'confirmed_date', 'status', 'created_at')
    list_filter = ('status', 'specialty')
    search_fields = ('patient__email', 'doctor__email', 'reason')
    readonly_fields = ('created_at',)
