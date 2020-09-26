from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.utils.text import slugify
from storio.utils import unique_slug_generator, unique_slug_generator_for_entry

class Story(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100)
    private = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    choices = [
    ('General', 'General'),
    ('Adventure', 'Adventure'),
    ('Crime', 'Crime'),
    ('Fantasy', 'Fantasy'),
    ('Horror', 'Horror'),
    ('Humor', 'Humor'),
    ('Romance', 'Romance'),
    ('Sci-fi', 'Sci-fi'),]
    genre = models.CharField(max_length=20, choices=choices, default='General')
    story_img = models.ImageField(default="story_imgs/default_story_preview.png", upload_to='story_imgs')
    story_description = models.TextField(max_length=200, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    view_count = models.PositiveIntegerField(default=0)
    slug = models.SlugField(unique=True)
    permitted_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name= 'permitted_users', blank=True)

    def create(self):
        self.created_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title

class Entry(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    text = models.TextField(max_length=500)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    published_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(max_length=150,blank=True)
    slug = models.SlugField(unique=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.text



def pre_save_receiver(sender, instance, *args, **kwargs): 
    if not instance.slug:
        if sender == Story:
            instance.slug = unique_slug_generator(instance)
        elif sender == Entry:
            instance.slug = unique_slug_generator_for_entry(instance)
  
  
pre_save.connect(pre_save_receiver, sender = Story)
pre_save.connect(pre_save_receiver, sender = Entry) 
