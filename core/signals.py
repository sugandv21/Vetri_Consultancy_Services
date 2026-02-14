from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Enrollment, TrainingModule, ModuleProgress, TrainingCompletion


# -------------------------------------------------------
# 1) When student enrolls → create module progress
# -------------------------------------------------------
@receiver(post_save, sender=Enrollment)
def create_training_progress(sender, instance, created, **kwargs):

    if not created:
        return

    training = instance.training
    modules = TrainingModule.objects.filter(training=training)

    progress_objects = []
    for module in modules:
        progress_objects.append(
            ModuleProgress(
                enrollment=instance,
                module=module
            )
        )

    # avoid duplicate errors
    if progress_objects:
        ModuleProgress.objects.bulk_create(progress_objects, ignore_conflicts=True)

    # create completion tracker
    TrainingCompletion.objects.get_or_create(enrollment=instance)


# -------------------------------------------------------
# 2) When new module is added → create progress for old students
# -------------------------------------------------------
@receiver(post_save, sender=TrainingModule)
def create_progress_for_existing_students(sender, instance, created, **kwargs):

    if not created:
        return

    enrollments = Enrollment.objects.filter(training=instance.training)

    progress_objects = []
    for enrollment in enrollments:
        progress_objects.append(
            ModuleProgress(
                enrollment=enrollment,
                module=instance
            )
        )

    if progress_objects:
        ModuleProgress.objects.bulk_create(progress_objects, ignore_conflicts=True)
