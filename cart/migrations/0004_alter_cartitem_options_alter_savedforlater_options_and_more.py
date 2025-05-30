# Generated by Django 5.1.7 on 2025-05-03 09:32

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_remove_cart_cart_cart_user_id_b645f9_idx_and_more'),
        ('products', '0003_remove_category_meta_description_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cartitem',
            options={'ordering': ['-added_at']},
        ),
        migrations.AlterModelOptions(
            name='savedforlater',
            options={'ordering': ['-added_at']},
        ),
        migrations.AddField(
            model_name='cart',
            name='last_activity',
            field=models.DateTimeField(auto_now=True, help_text='Last time the cart was modified'),
        ),
        migrations.AddField(
            model_name='cart',
            name='notes',
            field=models.TextField(blank=True, help_text='Customer notes for the order', null=True),
        ),
        migrations.AddField(
            model_name='cart',
            name='shipping_cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='cart',
            name='shipping_method',
            field=models.CharField(blank=True, help_text='Selected shipping method', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='gift_message',
            field=models.TextField(blank=True, help_text='Gift message if this item is a gift', null=True),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='is_gift',
            field=models.BooleanField(default=False, help_text='Whether this item is a gift'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='item_note',
            field=models.CharField(blank=True, help_text='Customer note for this item', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='price_at_addition',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Price when item was added to cart', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='savedforlater',
            name='note',
            field=models.CharField(blank=True, help_text='Note for this saved item', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='savedforlater',
            name='price_at_save',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Price when item was saved for later', max_digits=10, null=True),
        ),
        migrations.AddIndex(
            model_name='cart',
            index=models.Index(fields=['user'], name='cart_cart_user_id_b645f9_idx'),
        ),
        migrations.AddIndex(
            model_name='cart',
            index=models.Index(fields=['session_id'], name='cart_cart_session_f55f25_idx'),
        ),
        migrations.AddIndex(
            model_name='cart',
            index=models.Index(fields=['last_activity'], name='cart_cart_last_ac_251660_idx'),
        ),
        migrations.AddIndex(
            model_name='cartitem',
            index=models.Index(fields=['cart', 'product'], name='cart_cartit_cart_id_4bd8c3_idx'),
        ),
        migrations.AddIndex(
            model_name='cartitem',
            index=models.Index(fields=['added_at'], name='cart_cartit_added_a_c3b0c9_idx'),
        ),
        migrations.AddIndex(
            model_name='savedforlater',
            index=models.Index(fields=['user'], name='cart_savedf_user_id_eb343c_idx'),
        ),
        migrations.AddIndex(
            model_name='savedforlater',
            index=models.Index(fields=['added_at'], name='cart_savedf_added_a_aa717d_idx'),
        ),
    ]
