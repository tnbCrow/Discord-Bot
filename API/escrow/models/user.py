from uuid import uuid4

from django.db import models


class User(models.Model):

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)

    discord_id = models.IntegerField(unique=True)
    balance = models.IntegerField(default=0)
    locked = models.IntegerField(default=0)
    memo = models.CharField(max_length=255, unique=True)
    withdrawl_address = models.CharField(max_length=64, blank=True, null=True)

    def get_available_balance(self):
        return self.balance - self.locked

    def __str__(self):
        return f"User: {self.discord_id}; Balance: {self.balance}; Available: {self.get_available_balance()}"


# generate a random memo and check if its already taken.
# If taken, generate another memo again until we find a valid memo
def generate_memo(instance):

    while True:

        memo = f'CrowBot{uuid4().hex}'

        if not User.objects.filter(memo=memo).exists():
            return memo


def pre_save_post_receiver(sender, instance, *args, **kwargs):

    if not instance.memo:
        instance.memo = generate_memo(instance)


# save the memo before the User model is saved with the unique memo
models.signals.pre_save.connect(pre_save_post_receiver, sender=User)
