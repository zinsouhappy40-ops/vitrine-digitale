from django.db import models


class TenantScopedManager(models.Manager):
    def for_business(self, business):
        if business is None:
            return self.none()
        return self.get_queryset().filter(business=business)
