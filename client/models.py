# importing the db database
# lot of features we are inheriting from models
# pre build features
from django.db import models
#We are using this to reference user to the chitFund# means chitfund are the users of the apps
from django.contrib.auth.models import AbstractUser#get_user_model
#User = get_user_model()
# post save is executed whenn the a save function is executed
from django.db.models.signals import post_save

"""
    .objects is caloling the model manager
    on the manager we get access to methods of the database
    we can user create , get, save methods. cerate cerates a new instance
    query set using manager, all() , filter(on something)
    filter(field__gt = xxx) greater than this number
    Quert set says it all the instances and  you can run a query
    An instance is nothing but the instace of the filtered object
    ORM concept is used to work on database without working on sequel query interaction by python
"""



# Creating my custom user model
class User(AbstractUser):
    is_chitfund_owner = models.BooleanField(default=False)
    is_chitfund_user = models.BooleanField(default=False)
    is_namegen_user = models.BooleanField(default=False)
    is_food_app_user = models.BooleanField(default=False)
    is_ocr_app_user = models.BooleanField(default=False)
    is_transcribe_app_user = models.BooleanField(default=False)
    is_chatbot_user = models.BooleanField(default=False)
    is_kuries_user = models.BooleanField(default=False)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.user.username



# chitfund model
class ChitFund(models.Model):
    # below commented field is already there
    # in the User part hence commented
    name = models.CharField(max_length = 200)
    about = models.TextField(null=True)
    address = models.TextField(max_length=400,blank=True,null=True)
    state = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    pin = models.IntegerField(blank=True, null=True)
    # we need to have one to one relation between
    # user and the agent which is the user itself

    #### Have to think on below line ############################################
    #user = models.OneToOneField(User, on_delete=models.CASCADE)
    #############################################################################

    # auto_now it will automatically store the updated value int his field
    #updated = models.DateTimeField(auto_now=True)
    # auto_now_add takes a snapshot of when it was first added the instance
    #created = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(UserProfile,
                              on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.name

# Create your models here. Table schema
class Client(models.Model):

    # Gender categories
    MALE = 1
    FEMALE = 2
    GENDER = (
        (MALE,"Male"),
        (FEMALE, "Female"),
    )

    # Marriage categories
    MARRIED = 1
    SINGLE = 2
    OTHERS = 3
    MARRIAGE = (
        (MARRIED,"Married"),
        (SINGLE, "Single"),
        (OTHERS,"Others")
    )

    # Education categories
    POSTGRADUATE=1
    GRADUATE=2
    HIGHSCHOOL=3
    SCHOOL=4
    OTHERS=5
    UNKNOWN=6

    EDU =(
        (POSTGRADUATE,"Postgraduate"),
        (GRADUATE,"Graduate"),
        (HIGHSCHOOL,"Highschool"),
        (SCHOOL,"School"),
        (OTHERS,"Others"),
        (UNKNOWN,"Unknown")
    )

    # Soucre choice
    SOURCE_CHOICES = (
        ('YT','Youtube'),
        ('Google','Google'),
        ('Linkedin','Linkedin')

    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    age = models.IntegerField(default=18)

    sex = models.IntegerField(
        choices=GENDER,
        default=MALE,
    )

    education= models.IntegerField(
        choices=EDU,
        default=UNKNOWN,
    )

    marriage = models.IntegerField(
        choices=MARRIAGE,
        default=SINGLE,
    )

    phoned = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=13)
    email = models.EmailField()
    company = models.CharField(max_length=150,blank=True,null=True)
    description = models.TextField()
    source = models.CharField(choices=SOURCE_CHOICES, max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)
    # Blank means you ar esubmitting emply string, null means not having value in the database
    #profile_picture = models.ImageField(blank=True, null=True,
    #default="eneru_logo.jpg")
    #special_file = models.FileField(blank=True,null=True)

    # Relationship field connection betn tables
    # how to handle when the related instance is delete to handle
    # models.CASCADE will delete the client when chitfund is deleted
    chitfundName = models.ForeignKey("ChitFund",
                                     related_name="users", 
                                     on_delete=models.SET_NULL,
                                     blank=True,
                                     null=True)

    owner = models.ForeignKey(UserProfile,
                              on_delete=models.SET_NULL, blank=True, null=True)


    category = models.ForeignKey("Category",
                                 related_name="clients",
                                 on_delete=models.SET_NULL,
                                 blank=True,
                                 null=True)
    # auto_now it will automatically store the updated value int his field
    #updated = models.DateTimeField(auto_now=True)
    # auto_now_add takes a snapshot of when it was first added the instance
    #created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name



class Category(models.Model):
    name = models.CharField(max_length=30) # New, Processing, Opened, Ongoing, Defaulted, Completed
    owner = models.ForeignKey(UserProfile,
                              on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.name


# very powerful signals when some events needs to happen after an event
def post_user_created_signal(sender, instance, created, **kwargs):
    #print(instance, created)
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(post_user_created_signal, sender=User)