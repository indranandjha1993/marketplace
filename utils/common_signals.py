from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import FileField, ImageField


@receiver(post_delete)
def delete_files_on_model_delete(sender, instance, **kwargs):
    for field in instance._meta.fields:
        if isinstance(field, (FileField, ImageField)):
            file_field = getattr(instance, field.name)
            if file_field:
                file_field.delete(save=False)
