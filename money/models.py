from django.db import models
from django.db.models import Q


class Chitti(models.Model):
    name = models.CharField(max_length=100)

    number_of_persons = models.PositiveIntegerField()

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    monthly_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    amount_after_taking_chitti = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    duration_months = models.PositiveIntegerField()

    start_date = models.DateField()

    starting_chitti_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    amount_to_be_added = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return self.name

    def get_end_date(self):
        total_months = self.duration_months - 1

        year = self.start_date.year + (
            self.start_date.month - 1 + total_months
        ) // 12

        month = (
            self.start_date.month - 1 + total_months
        ) % 12 + 1

        import calendar
        from datetime import date

        last_day = calendar.monthrange(year, month)[1]

        return date(year, month, last_day)


class ChittiMonth(models.Model):
    chitti = models.ForeignKey(
        Chitti,
        on_delete=models.CASCADE,
        related_name="months"
    )

    month = models.DateField()

    chitti_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    is_completed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chitti", "month"],
                name="unique_chitti_month"
            )
        ]

    def __str__(self):
        return f"{self.chitti.name} - {self.month}"


class Participant(models.Model):
    chitti = models.ForeignKey(
        Chitti,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    name = models.CharField(max_length=100)

    is_me = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ChittiTake(models.Model):
    chitti = models.ForeignKey(
        Chitti,
        on_delete=models.CASCADE,
        related_name="chitti_takes"
    )

    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="chitti_takes"
    )

    month = models.ForeignKey(
        ChittiMonth,
        on_delete=models.CASCADE,
        related_name="chitti_takes"
    )

    taken_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chitti", "participant"],
                name="one_take_per_person_per_chitti"
            ),
            models.UniqueConstraint(
                fields=["chitti", "month"],
                name="one_take_per_month_per_chitti"
            ),
        ]

    def __str__(self):
        return (
            f"{self.participant.name} - "
            f"{self.month.month}"
        )


class MonthlyObligation(models.Model):
    chitti = models.ForeignKey(
        Chitti,
        on_delete=models.CASCADE,
        related_name="obligations"
    )

    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="obligations"
    )

    month = models.ForeignKey(
        ChittiMonth,
        on_delete=models.CASCADE,
        related_name="obligations"
    )

    amount_due = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status_confirmed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chitti", "participant", "month"],
                name="unique_monthly_obligation"
            )
        ]

    def __str__(self):
        return (
            f"{self.participant.name} - "
            f"{self.month.month} - "
            f"{self.amount_due}"
        )


class PaymentTransaction(models.Model):
    chitti = models.ForeignKey(
        Chitti,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    payment_month = models.DateField()

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.participant.name} - "
            f"{self.payment_month} - "
            f"{self.amount}"
        )


class PaymentAllocation(models.Model):
    payment = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name="allocations"
    )

    obligation = models.ForeignKey(
        MonthlyObligation,
        on_delete=models.CASCADE,
        related_name="allocations"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.payment} → {self.obligation}"