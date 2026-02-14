from django.contrib import admin
from .models import Training, Enrollment, TrainingEnquiry, EnquiryMessage, Payment


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ("title", "duration", "fee", "is_active")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "training", "enrolled_at")


@admin.register(TrainingEnquiry)
class TrainingEnquiryAdmin(admin.ModelAdmin):
    list_display = ("user", "training", "created_at")


@admin.register(EnquiryMessage)
class EnquiryMessageAdmin(admin.ModelAdmin):
    list_display = ("enquiry", "sender", "created_at")
    
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at")

    def has_add_permission(self, request):
        return False  # admin cannot manually create


from .models import HomeHero

@admin.register(HomeHero)
class HomeHeroAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "updated_at")
    list_editable = ("is_active",)

from .models import FeatureSection, HomeFeature


@admin.register(FeatureSection)
class FeatureSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active")


@admin.register(HomeFeature)
class HomeFeatureAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "link_type", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("section", "is_active")



from .models import SiteStatistic

@admin.register(SiteStatistic)
class SiteStatisticAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "suffix", "order", "is_active")
    list_editable = ("order", "is_active")
    
from .models import FAQ
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("question", "answer")

from .models import Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "is_active", "created_at")
    list_filter = ("is_active", "company")
    search_fields = ("name", "company", "message")

from .models import HomeCTA

@admin.register(HomeCTA)
class HomeCTAAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active")
    list_editable = ("is_active",)

from .models import AboutPage

@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active")
    list_editable = ("is_active",)


from .models import ServicePage, ServiceItem

class ServiceItemInline(admin.TabularInline):
    model = ServiceItem
    extra = 1

@admin.register(ServicePage)
class ServicePageAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active"]
    inlines = [ServiceItemInline]

from .models import PricingPage, PricingPlan, PricingFeature

class PricingFeatureInline(admin.TabularInline):
    model = PricingFeature
    extra = 1

class PricingPlanInline(admin.StackedInline):
    model = PricingPlan
    extra = 1

@admin.register(PricingPage)
class PricingPageAdmin(admin.ModelAdmin):
    inlines = [PricingPlanInline]

@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    inlines = [PricingFeatureInline]


from .models import CertificateDesign

@admin.register(CertificateDesign)
class CertificateDesignAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not CertificateDesign.objects.exists()  # only one allowed


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "payment_type", "amount", "status", "created_at")
    list_filter = ("payment_type", "status")
    search_fields = ("user__email",)
    ordering = ("-created_at",)


from .models import SubscriptionPricing

@admin.register(SubscriptionPricing)
class SubscriptionPricingAdmin(admin.ModelAdmin):
    list_display = ("plan", "price")
