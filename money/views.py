from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .models import (
    Chitti,
    ChittiMonth,
    Participant,
    ChittiTake,
    MonthlyObligation,
    PaymentTransaction,
    PaymentAllocation,
)


def add_months(start_date, months):
    month = start_date.month - 1 + months

    year = start_date.year + month // 12

    month = month % 12 + 1

    return date(year, month, 1)

@login_required
def home(request):
    chittis = Chitti.objects.all().order_by("id")

    return render(
        request,
        "money/home.html",
        {
            "chittis": chittis
        }
    )


def create_chitti(request):

    if request.method == "POST":

        name = request.POST.get(
            "chitti_name",
            ""
        ).strip()

        number_of_persons_text = request.POST.get(
            "number_of_persons",
            ""
        ).strip()

        total_amount_text = request.POST.get(
            "total_amount",
            ""
        ).strip()

        monthly_amount_text = request.POST.get(
            "monthly_amount",
            ""
        ).strip()

        amount_after_taking_text = request.POST.get(
            "amount_after_taking",
            ""
        ).strip()

        duration_months_text = request.POST.get(
            "duration_months",
            ""
        ).strip()

        start_date_text = request.POST.get(
            "start_date",
            ""
        ).strip()

        starting_chitti_amount_text = request.POST.get(
            "starting_chitti_amount",
            ""
        ).strip()

        amount_to_be_added_text = request.POST.get(
            "amount_to_be_added",
            ""
        ).strip()

        if not name:
            return render(
                request,
                "money/create_chitti.html",
                {"error": "Chitti Name is required."}
            )

        try:
            number_of_persons = int(number_of_persons_text)

            if number_of_persons <= 0:
                raise ValueError

        except (ValueError, TypeError):
            return render(
                request,
                "money/create_chitti.html",
                {"error": "Number of Persons must be greater than 0."}
            )

        try:
            total_amount = Decimal(total_amount_text)

            if total_amount < 0:
                raise ValueError

        except (InvalidOperation, ValueError):
            return render(
                request,
                "money/create_chitti.html",
                {"error": "Enter a valid Total Amount."}
            )

        try:
            monthly_amount = Decimal(monthly_amount_text)

            if monthly_amount < 0:
                raise ValueError

        except (InvalidOperation, ValueError):
            return render(
                request,
                "money/create_chitti.html",
                {"error": "Enter a valid Monthly Amount."}
            )

        try:
            amount_after_taking = Decimal(
                amount_after_taking_text
            )

            if amount_after_taking < 0:
                raise ValueError

        except (InvalidOperation, ValueError):
            return render(
                request,
                "money/create_chitti.html",
                {
                    "error":
                    "Enter a valid Amount After Taking Chitti."
                }
            )

        try:
            duration_months = int(duration_months_text)

            if duration_months <= 0:
                raise ValueError

        except (ValueError, TypeError):
            return render(
                request,
                "money/create_chitti.html",
                {"error": "Duration must be greater than 0."}
            )

        try:
            start_date = datetime.strptime(
                start_date_text,
                "%Y-%m-%d"
            ).date()

        except (ValueError, TypeError):
            return render(
                request,
                "money/create_chitti.html",
                {"error": "Enter a valid Start Date."}
            )

        try:
            starting_chitti_amount = Decimal(
                starting_chitti_amount_text
            )

            if starting_chitti_amount < 0:
                raise ValueError

        except (InvalidOperation, ValueError):
            return render(
                request,
                "money/create_chitti.html",
                {
                    "error":
                    "Enter a valid Starting Chitti Amount."
                }
            )

        try:
            amount_to_be_added = Decimal(
                amount_to_be_added_text
            )

            if amount_to_be_added < 0:
                raise ValueError

        except (InvalidOperation, ValueError):
            return render(
                request,
                "money/create_chitti.html",
                {
                    "error":
                    "Enter a valid Amount to be Added."
                }
            )

        participant_names = []

        for i in range(number_of_persons):

            participant_name = request.POST.get(
                f"participant_{i}",
                ""
            ).strip()

            if not participant_name:
                return render(
                    request,
                    "money/create_chitti.html",
                    {
                        "error":
                        f"Participant {i + 1} name is required."
                    }
                )

            participant_names.append(participant_name)

        with transaction.atomic():

            chitti = Chitti.objects.create(
                name=name,
                number_of_persons=number_of_persons,
                total_amount=total_amount,
                monthly_amount=monthly_amount,
                amount_after_taking_chitti=amount_after_taking,
                duration_months=duration_months,
                start_date=start_date,
                starting_chitti_amount=starting_chitti_amount,
                amount_to_be_added=amount_to_be_added,
            )

            months = []

            for i in range(duration_months):

                month_date = add_months(
                    start_date,
                    i
                )

                chitti_amount = (
                    starting_chitti_amount
                    + (amount_to_be_added * i)
                )

                month = ChittiMonth.objects.create(
                    chitti=chitti,
                    month=month_date,
                    chitti_amount=chitti_amount,
                    is_completed=False,
                )

                months.append(month)

            participants = []

            for participant_name in participant_names:

                participant = Participant.objects.create(
                    chitti=chitti,
                    name=participant_name,
                    is_me=False,
                )

                participants.append(participant)

            me = Participant.objects.create(
                chitti=chitti,
                name="ME",
                is_me=True,
            )

            # Create regular-member monthly obligations.
            for participant in participants:

                for month in months:

                    MonthlyObligation.objects.create(
                        chitti=chitti,
                        participant=participant,
                        month=month,
                        amount_due=monthly_amount,
                        status_confirmed=False,
                    )

        return redirect("home")

    return render(
        request,
        "money/create_chitti.html"
    )

def edit_chitti(request, chitti_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    participants = Participant.objects.filter(
        chitti=chitti,
        is_me=False
    ).order_by("id")

    if request.method == "POST":

        name = request.POST.get(
            "chitti_name",
            ""
        ).strip()

        number_of_persons_text = request.POST.get(
            "number_of_persons",
            ""
        ).strip()

        total_amount_text = request.POST.get(
            "total_amount",
            ""
        ).strip()

        monthly_amount_text = request.POST.get(
            "monthly_amount",
            ""
        ).strip()

        amount_after_taking_text = request.POST.get(
            "amount_after_taking",
            ""
        ).strip()

        duration_months_text = request.POST.get(
            "duration_months",
            ""
        ).strip()

        start_date_text = request.POST.get(
            "start_date",
            ""
        ).strip()

        starting_chitti_amount_text = request.POST.get(
            "starting_chitti_amount",
            ""
        ).strip()

        amount_to_be_added_text = request.POST.get(
            "amount_to_be_added",
            ""
        ).strip()

        # -----------------------------
        # Basic validation
        # -----------------------------

        if not name:
            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error": "Chitti Name is required."
                }
            )

        try:

            number_of_persons = int(
                number_of_persons_text
            )

            if number_of_persons <= 0:
                raise ValueError

        except (ValueError, TypeError):

            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error":
                    "Number of Persons must be greater than 0."
                }
            )

        try:

            total_amount = Decimal(
                total_amount_text
            )

            if total_amount < 0:
                raise ValueError

        except (InvalidOperation, ValueError):

            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error":
                    "Enter a valid Total Amount."
                }
            )

        try:

            monthly_amount = Decimal(
                monthly_amount_text
            )

            if monthly_amount < 0:
                raise ValueError

        except (InvalidOperation, ValueError):

            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error":
                    "Enter a valid Monthly Amount."
                }
            )

        try:

            amount_after_taking = Decimal(
                amount_after_taking_text
            )

            if amount_after_taking < 0:
                raise ValueError

        except (InvalidOperation, ValueError):

            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error":
                    "Enter a valid Amount After Taking Chitti."
                }
            )

        try:

            duration_months = int(
                duration_months_text
            )

            if duration_months <= 0:
                raise ValueError

        except (ValueError, TypeError):

            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error":
                    "Duration must be greater than 0."
                }
            )

        try:

            start_date = datetime.strptime(
                start_date_text,
                "%Y-%m-%d"
            ).date()

        except (ValueError, TypeError):

            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error":
                    "Enter a valid Start Date."
                }
            )

        try:

            starting_chitti_amount = Decimal(
                starting_chitti_amount_text
            )

            if starting_chitti_amount < 0:
                raise ValueError

        except (InvalidOperation, ValueError):

            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error":
                    "Enter a valid Starting Chitti Amount."
                }
            )

        try:

            amount_to_be_added = Decimal(
                amount_to_be_added_text
            )

            if amount_to_be_added < 0:
                raise ValueError

        except (InvalidOperation, ValueError):

            return render(
                request,
                "money/edit_chitti.html",
                {
                    "chitti": chitti,
                    "participants": participants,
                    "error":
                    "Enter a valid Amount to be Added."
                }
            )

        # -----------------------------
        # Participant names
        # -----------------------------

        participant_names = []

        for i in range(number_of_persons):

            participant_name = request.POST.get(
                f"participant_{i}",
                ""
            ).strip()

            if not participant_name:

                return render(
                    request,
                    "money/edit_chitti.html",
                    {
                        "chitti": chitti,
                        "participants": participants,
                        "error":
                        f"Participant {i + 1} name is required."
                    }
                )

            participant_names.append(
                participant_name
            )

        # -----------------------------
        # Check whether history exists
        # -----------------------------

        has_history = (
            PaymentTransaction.objects.filter(
                chitti=chitti
            ).exists()
            or
            ChittiTake.objects.filter(
                chitti=chitti
            ).exists()
        )

        # If history already exists, don't allow
        # structural changes that could break history.
        if has_history:

            if (
                number_of_persons
                != chitti.number_of_persons
            ):
                return render(
                    request,
                    "money/edit_chitti.html",
                    {
                        "chitti": chitti,
                        "participants": participants,
                        "error":
                        "Number of Persons cannot be changed "
                        "after payments or Chitti history exists."
                    }
                )

            if duration_months != chitti.duration_months:

                return render(
                    request,
                    "money/edit_chitti.html",
                    {
                        "chitti": chitti,
                        "participants": participants,
                        "error":
                        "Duration cannot be changed "
                        "after payments or Chitti history exists."
                    }
                )

            if start_date != chitti.start_date:

                return render(
                    request,
                    "money/edit_chitti.html",
                    {
                        "chitti": chitti,
                        "participants": participants,
                        "error":
                        "Start Date cannot be changed "
                        "after payments or Chitti history exists."
                    }
                )

        # -----------------------------
        # Save changes
        # -----------------------------

        with transaction.atomic():

            chitti.name = name
            chitti.number_of_persons = number_of_persons
            chitti.total_amount = total_amount
            chitti.monthly_amount = monthly_amount
            chitti.amount_after_taking_chitti = (
                amount_after_taking
            )
            chitti.duration_months = duration_months
            chitti.start_date = start_date
            chitti.starting_chitti_amount = (
                starting_chitti_amount
            )
            chitti.amount_to_be_added = (
                amount_to_be_added
            )

            chitti.save()

            # Update participant names.
            existing_participants = list(
                Participant.objects.filter(
                    chitti=chitti,
                    is_me=False
                ).order_by("id")
            )

            for i, participant_name in enumerate(
                participant_names
            ):

                if i < len(existing_participants):

                    existing_participants[i].name = (
                        participant_name
                    )

                    existing_participants[i].save()

                else:

                    Participant.objects.create(
                        chitti=chitti,
                        name=participant_name,
                        is_me=False,
                    )

        return redirect("home")

    # -----------------------------
    # GET request
    # -----------------------------

    return render(
        request,
        "money/edit_chitti.html",
        {
            "chitti": chitti,
            "participants": participants,
        }
    )

def get_regular_paid(
    chitti,
    participant,
    month
):
    total = PaymentTransaction.objects.filter(
        chitti=chitti,
        participant=participant,
        payment_month=month.month,
    ).aggregate(
        total=Sum("amount")
    )["total"]

    return total or Decimal("0.00")


def get_total_paid_until(
    chitti,
    participant,
    month
):
    total = PaymentTransaction.objects.filter(
        chitti=chitti,
        participant=participant,
        payment_month__lte=month.month,
    ).aggregate(
        total=Sum("amount")
    )["total"]

    return total or Decimal("0.00")




def get_required_until_correct(
    chitti,
    participant,
    selected_month
):
    months = ChittiMonth.objects.filter(
        chitti=chitti,
        month__lte=selected_month.month
    ).order_by("month")

    take = ChittiTake.objects.filter(
        chitti=chitti,
        participant=participant
    ).order_by("month__month").first()

    total = Decimal("0.00")

    for month in months:

        if take and month.month > take.month.month:
            total += chitti.amount_after_taking_chitti
        else:
            total += chitti.monthly_amount

    return total


def get_current_due(
    chitti,
    participant,
    selected_month
):
    required = get_required_until_correct(
        chitti,
        participant,
        selected_month
    )

    paid = get_total_paid_until(
        chitti,
        participant,
        selected_month
    )

    due = required - paid

    if due < 0:
        due = Decimal("0.00")

    return due


def get_monthly_due_for_history(
    chitti,
    participant,
    month
):
    take = ChittiTake.objects.filter(
        chitti=chitti,
        participant=participant
    ).order_by(
        "month__month").first()

    if take and month.month > take.month.month:
        return chitti.amount_after_taking_chitti

    return chitti.monthly_amount


def chitti_detail(request, chitti_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    months = ChittiMonth.objects.filter(
        chitti=chitti
    ).order_by("month")

    selected_month_id = request.GET.get(
        "month"
    )

# Find the actual current month of this Chitti
    current_month = next(
        (
            month
            for month in months
            if not month.is_completed
        ),
        months.last()
    )

    if selected_month_id:

        selected_month = get_object_or_404(
            ChittiMonth,
            id=selected_month_id,
            chitti=chitti
        )

    else:

        selected_month = current_month

    regular_members = Participant.objects.filter(
        chitti=chitti,
        is_me=False
    ).order_by("id")

    rows = []

    for participant in regular_members:

        paid = get_regular_paid(
            chitti,
            participant,
            selected_month
        )

        due = get_current_due(
            chitti,
            participant,
            selected_month
        )

        status = (
            "Paid"
            if due == 0
            else "Not Paid"
        )

        obligation = MonthlyObligation.objects.get(
            chitti=chitti,
            participant=participant,
            month=selected_month
        )

        take_this_month = ChittiTake.objects.filter(
            chitti=chitti,
            participant=participant,
            month=selected_month
        ).first()

        previous_take = None

        for take in ChittiTake.objects.filter(
            chitti=chitti,
            participant=participant
        ).select_related("month").order_by("month"):

            if take.month.month < selected_month.month:
                previous_take = take
                break

        any_taker = ChittiTake.objects.filter(
            chitti=chitti,
            month=selected_month
        ).exists()

        rows.append({
            "participant": participant,
            "paid": paid,
            "due": due,
            "status": status,
            "status_confirmed": obligation.status_confirmed,
            "take_this_month": take_this_month,
            "previous_take": previous_take,
            "any_taker": any_taker,
            "has_payment": PaymentTransaction.objects.filter(
                chitti=chitti,
                participant=participant,
                payment_month=selected_month.month
            ).exists(),
        })

    me = Participant.objects.get(
        chitti=chitti,
        is_me=True
    )

    me_take = ChittiTake.objects.filter(
    chitti=chitti,
    participant=me,
    month=selected_month
    ).first()

    me_previous_take = None

    for take in ChittiTake.objects.filter(
        chitti=chitti,
        participant=me
    ).select_related("month").order_by("month"):

        if take.month.month < selected_month.month:
            me_previous_take = take
            break

    any_taker = ChittiTake.objects.filter(
        chitti=chitti,
        month=selected_month
    ).exists()

    all_status_confirmed = all(
    row["has_payment"]
    for row in rows
)

    can_complete = (
        all_status_confirmed
        and any_taker
        and not selected_month.is_completed
    )

    total_pending = Decimal("0.00")

    for row in rows:
        total_pending += row["due"]

    context = {
        "chitti": chitti,
        "months": months,
        "selected_month": selected_month,
        "current_month": current_month,
        "rows": rows,
        "me": me,
        "me_take": me_take,
        "any_taker": any_taker,
        "can_complete": can_complete,
        "total_pending": total_pending,
    }

    return render(
        request,
        "money/chitti_detail.html",
        context
    )


def add_payment(request, chitti_id, participant_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    participant = get_object_or_404(
        Participant,
        id=participant_id,
        chitti=chitti,
        is_me=False
    )

    month_id = request.GET.get("month")

    selected_month = get_object_or_404(
        ChittiMonth,
        id=month_id,
        chitti=chitti
    )

    # Check whether the person has taken Chitti
    take = ChittiTake.objects.filter(
        chitti=chitti,
        participant=participant
    ).order_by("month__month").first()

    # Find the amount required for this month
    if take and selected_month.month > take.month.month:
        current_month_amount = (
            chitti.amount_after_taking_chitti
        )
    else:
        current_month_amount = chitti.monthly_amount

    # Calculate the amount that was required
    # before the selected month
    previous_months = ChittiMonth.objects.filter(
        chitti=chitti,
        month__lt=selected_month.month
    ).order_by("month")

    required_before_month = Decimal("0.00")

    for month in previous_months:

        if take and month.month > take.month.month:
            required_before_month += (
                chitti.amount_after_taking_chitti
            )
        else:
            required_before_month += (
                chitti.monthly_amount
            )

    # Calculate payments made before this month
    payments_before_month = PaymentTransaction.objects.filter(
        chitti=chitti,
        participant=participant,
        payment_month__lt=selected_month.month
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    # Previous outstanding Due
    previous_due = (
        required_before_month
        - payments_before_month
    )

    if previous_due < 0:
        previous_due = Decimal("0.00")

    # Payments already made in this month
    payments_this_month = PaymentTransaction.objects.filter(
        chitti=chitti,
        participant=participant,
        payment_month=selected_month.month
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    # Maximum total payment allowed for this month
    maximum_allowed = (
        current_month_amount
        + previous_due
    )

    # Amount still available for a new payment
    remaining_allowed = (
        maximum_allowed
        - payments_this_month
    )

    if remaining_allowed < 0:
        remaining_allowed = Decimal("0.00")

    if request.method == "POST":

        amount_text = request.POST.get(
            "amount",
            ""
        ).strip()

        try:

            amount = Decimal(amount_text)

            if amount < 0:
                raise ValueError

        except (InvalidOperation, ValueError):

            return render(
                request,
                "money/add_payment.html",
                {
                    "chitti": chitti,
                    "participant": participant,
                    "selected_month": selected_month,
                    "maximum_allowed": remaining_allowed,
                    "error": "Enter a valid amount.",
                }
            )

        if amount > remaining_allowed:

            return render(
                request,
                "money/add_payment.html",
                {
                    "chitti": chitti,
                    "participant": participant,
                    "selected_month": selected_month,
                    "maximum_allowed": remaining_allowed,
                    "error": (
                        f"You cannot enter more than "
                        f"₹{remaining_allowed:.2f}."
                    ),
                }
            )

        PaymentTransaction.objects.create(
            chitti=chitti,
            participant=participant,
            payment_month=selected_month.month,
            amount=amount,
        )

# The member's payment/status for this month
# has now been reviewed and confirmed.
        MonthlyObligation.objects.filter(
            chitti=chitti,
            participant=participant,
            month=selected_month
        ).update(
            status_confirmed=True
        )

        return redirect(
            f"/chitti/{chitti.id}/?month={selected_month.id}"
        )

    return render(
        request,
        "money/add_payment.html",
        {
            "chitti": chitti,
            "participant": participant,
            "selected_month": selected_month,
            "maximum_allowed": remaining_allowed,
        }
    )

def edit_payment(request, payment_id):

    payment = get_object_or_404(
        PaymentTransaction,
        id=payment_id
    )

    chitti = payment.chitti
    participant = payment.participant

    selected_month = get_object_or_404(
        ChittiMonth,
        chitti=chitti,
        month=payment.payment_month
    )

    # Check whether the person has taken Chitti
    take = ChittiTake.objects.filter(
        chitti=chitti,
        participant=participant
    ).order_by("month__month").first()

    # Amount required for this month
    if take and selected_month.month > take.month.month:
        current_month_amount = (
            chitti.amount_after_taking_chitti
        )
    else:
        current_month_amount = chitti.monthly_amount

    # Previous months
    previous_months = ChittiMonth.objects.filter(
        chitti=chitti,
        month__lt=selected_month.month
    ).order_by("month")

    required_before_month = Decimal("0.00")

    for month in previous_months:

        if take and month.month > take.month.month:
            required_before_month += (
                chitti.amount_after_taking_chitti
            )
        else:
            required_before_month += (
                chitti.monthly_amount
            )

    # Payments before selected month
    payments_before_month = PaymentTransaction.objects.filter(
        chitti=chitti,
        participant=participant,
        payment_month__lt=selected_month.month
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    previous_due = (
        required_before_month
        - payments_before_month
    )

    if previous_due < 0:
        previous_due = Decimal("0.00")

    # Other payments in this month
    other_payments_this_month = (
        PaymentTransaction.objects.filter(
            chitti=chitti,
            participant=participant,
            payment_month=selected_month.month
        )
        .exclude(id=payment.id)
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # Maximum total allowed for this month
    maximum_allowed = (
        current_month_amount
        + previous_due
    )

    # Maximum value this particular payment can be changed to
    maximum_for_this_payment = (
        maximum_allowed
        - other_payments_this_month
    )

    if maximum_for_this_payment < 0:
        maximum_for_this_payment = Decimal("0.00")

    if request.method == "POST":

        amount_text = request.POST.get(
            "amount",
            ""
        ).strip()

        try:

            amount = Decimal(amount_text)

            if amount < 0:
                raise ValueError

        except (InvalidOperation, ValueError):

            return render(
                request,
                "money/edit_payment.html",
                {
                    "payment": payment,
                    "chitti": chitti,
                    "participant": participant,
                    "selected_month": selected_month,
                    "maximum_allowed": maximum_for_this_payment,
                    "error": "Enter a valid amount.",
                }
            )

        if amount > maximum_for_this_payment:

            return render(
                request,
                "money/edit_payment.html",
                {
                    "payment": payment,
                    "chitti": chitti,
                    "participant": participant,
                    "selected_month": selected_month,
                    "maximum_allowed": maximum_for_this_payment,
                    "error": (
                        f"You cannot enter more than "
                        f"₹{maximum_for_this_payment:.2f}."
                    ),
                }
            )

        payment.amount = amount

        payment.save(
            update_fields=["amount"]
        )

        return redirect(
            f"/chitti/{chitti.id}/?month={selected_month.id}"
        )

    return render(
        request,
        "money/edit_payment.html",
        {
            "payment": payment,
            "chitti": chitti,
            "participant": participant,
            "selected_month": selected_month,
            "maximum_allowed": maximum_for_this_payment,
        }
    )
def confirm_status(request, chitti_id, participant_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    participant = get_object_or_404(
        Participant,
        id=participant_id,
        chitti=chitti,
        is_me=False
    )

    month_id = request.GET.get("month")

    selected_month = get_object_or_404(
        ChittiMonth,
        id=month_id,
        chitti=chitti
    )

    obligation = get_object_or_404(
        MonthlyObligation,
        chitti=chitti,
        participant=participant,
        month=selected_month
    )

    obligation.status_confirmed = True
    obligation.save(
        update_fields=["status_confirmed"]
    )

    return redirect(
        f"/chitti/{chitti.id}/?month={selected_month.id}"
    )


def take_chitti(request, chitti_id, participant_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    participant = get_object_or_404(
        Participant,
        id=participant_id,
        chitti=chitti
    )

    month_id = request.GET.get("month")

    selected_month = get_object_or_404(
        ChittiMonth,
        id=month_id,
        chitti=chitti
    )

    # A completed month cannot be changed.
    if selected_month.is_completed:
        return redirect(
            f"/chitti/{chitti.id}/?month={selected_month.id}"
        )

    with transaction.atomic():

        # Check whether this person is already Taken
        # in the CURRENT month.
        current_take = ChittiTake.objects.select_for_update().filter(
            chitti=chitti,
            participant=participant,
            month=selected_month
        ).first()

        # If current person is already Taken,
        # clicking Taken again cancels that Take.
        if current_take:

            current_take.delete()

            # Restore this person's future obligations
            # to the normal monthly amount.
            future_months = ChittiMonth.objects.filter(
                chitti=chitti,
                month__gt=selected_month.month
            )

            MonthlyObligation.objects.filter(
                chitti=chitti,
                participant=participant,
                month__in=future_months
            ).update(
                amount_due=chitti.monthly_amount
            )

            return redirect(
                f"/chitti/{chitti.id}/?month={selected_month.id}"
            )

        # Only ONE person can take Chitti in this month.
        month_already_taken = ChittiTake.objects.filter(
            chitti=chitti,
            month=selected_month
        ).exists()

        if month_already_taken:
            return redirect(
                f"/chitti/{chitti.id}/?month={selected_month.id}"
            )

        # A person can take Chitti ONLY ONCE
        # during the entire Chitti.
        person_already_took = ChittiTake.objects.filter(
            chitti=chitti,
            participant=participant
        ).exists()

        if person_already_took:
            return redirect(
                f"/chitti/{chitti.id}/?month={selected_month.id}"
            )

        # Create the Chitti Take.
        ChittiTake.objects.create(
            chitti=chitti,
            participant=participant,
            month=selected_month,
            taken_amount=selected_month.chitti_amount,
        )

        # From the NEXT month onward,
        # use Amount After Taking Chitti.
        future_months = ChittiMonth.objects.filter(
            chitti=chitti,
            month__gt=selected_month.month
        )

        MonthlyObligation.objects.filter(
            chitti=chitti,
            participant=participant,
            month__in=future_months
        ).update(
            amount_due=chitti.amount_after_taking_chitti
        )

    return redirect(
        f"/chitti/{chitti.id}/?month={selected_month.id}"
    )
def take_me_chitti(request, chitti_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    me = get_object_or_404(
        Participant,
        chitti=chitti,
        is_me=True
    )

    month_id = request.GET.get("month")

    selected_month = get_object_or_404(
        ChittiMonth,
        id=month_id,
        chitti=chitti
    )

    # A completed month cannot be changed.
    if selected_month.is_completed:
        return redirect(
            f"/chitti/{chitti.id}/?month={selected_month.id}"
        )

    with transaction.atomic():

        # Check whether ME is already Taken
        # in the CURRENT month.
        current_take = ChittiTake.objects.select_for_update().filter(
            chitti=chitti,
            participant=me,
            month=selected_month
        ).first()

        # If ME is already Taken,
        # clicking Taken again cancels the Take.
        if current_take:

            current_take.delete()

            return redirect(
                f"/chitti/{chitti.id}/?month={selected_month.id}"
            )

        # Only ONE person can take Chitti in this month.
        month_already_taken = ChittiTake.objects.filter(
            chitti=chitti,
            month=selected_month
        ).exists()

        if month_already_taken:
            return redirect(
                f"/chitti/{chitti.id}/?month={selected_month.id}"
            )

        # ME can take Chitti ONLY ONCE
        # during the entire Chitti.
        me_already_took = ChittiTake.objects.filter(
            chitti=chitti,
            participant=me
        ).exists()

        if me_already_took:
            return redirect(
                f"/chitti/{chitti.id}/?month={selected_month.id}"
            )

        # Create ME's Chitti Take.
        ChittiTake.objects.create(
            chitti=chitti,
            participant=me,
            month=selected_month,
            taken_amount=selected_month.chitti_amount,
        )

    return redirect(
        f"/chitti/{chitti.id}/?month={selected_month.id}"
    )
def complete_month(request, chitti_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    month_id = request.GET.get("month")

    selected_month = get_object_or_404(
        ChittiMonth,
        id=month_id,
        chitti=chitti
    )

    regular_members = Participant.objects.filter(
        chitti=chitti,
        is_me=False
    )

    obligations = MonthlyObligation.objects.filter(
        chitti=chitti,
        month=selected_month,
        participant__is_me=False
    )

    all_confirmed = (
        obligations.count()
        == regular_members.count()
        and not obligations.filter(
            status_confirmed=False
        ).exists()
    )

    has_taker = ChittiTake.objects.filter(
        chitti=chitti,
        month=selected_month
    ).exists()

    if (
        all_confirmed
        and has_taker
        and not selected_month.is_completed
    ):

        selected_month.is_completed = True
        selected_month.save(
            update_fields=["is_completed"]
        )

    return redirect(
        f"/chitti/{chitti.id}/"
    )


def person_view(request, chitti_id, participant_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    participant = get_object_or_404(
        Participant,
        id=participant_id,
        chitti=chitti,
        is_me=False
    )

    months = ChittiMonth.objects.filter(
        chitti=chitti
    ).order_by("month")

    history = []

    for month in months:

        paid = get_regular_paid(
            chitti,
            participant,
            month
        )

        required = get_monthly_due_for_history(
            chitti,
            participant,
            month
        )

        month_due = required - paid

        if month_due < 0:
            month_due = Decimal("0.00")

        history.append({
            "month": month,
            "paid": paid,
            "due": month_due,
        })

    payments = PaymentTransaction.objects.filter(
        chitti=chitti,
        participant=participant
    ).order_by(
        "payment_month",
        "created_at"
    )

    return render(
        request,
        "money/person_view.html",
        {
            "chitti": chitti,
            "participant": participant,
            "history": history,
            "payments": payments,
        }
    )


def me_view(request, chitti_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    me = get_object_or_404(
        Participant,
        chitti=chitti,
        is_me=True
    )

    months = ChittiMonth.objects.filter(
        chitti=chitti
    ).order_by("month")

    payments = PaymentTransaction.objects.filter(
        chitti=chitti,
        participant=me
    ).order_by(
        "payment_month",
        "created_at"
    )

    payment_totals = {}

    for payment in payments:

        payment_totals[payment.payment_month] = (
            payment_totals.get(
                payment.payment_month,
                Decimal("0.00")
            )
            + payment.amount
        )

    history = []

    me_take = ChittiTake.objects.filter(
        chitti=chitti,
        participant=me
    ).first()

    for month in months:

        amount = payment_totals.get(
            month.month,
            Decimal("0.00")
        )

        history.append({
            "month": month,
            "amount": amount,
            "taken": (
                me_take is not None
                and me_take.month_id == month.id
            ),
        })

    return render(
        request,
        "money/me_view.html",
        {
            "chitti": chitti,
            "me": me,
            "history": history,
            "me_take": me_take,
        }
    )

def delete_chitti(request, chitti_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    if request.method == "POST":
        chitti.delete()

        return redirect("home")

    return render(
        request,
        "money/delete_chitti.html",
        {
            "chitti": chitti
        }
    )

def add_me_amount(request, chitti_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    me = get_object_or_404(
        Participant,
        chitti=chitti,
        is_me=True
    )

    month_id = request.GET.get("month")

    selected_month = get_object_or_404(
        ChittiMonth,
        id=month_id,
        chitti=chitti
    )

    if request.method == "POST":

        amount_text = request.POST.get(
            "amount",
            ""
        ).strip()

        try:
            amount = Decimal(amount_text)

            if amount <= 0:
                raise ValueError

        except (InvalidOperation, ValueError):

            return render(
                request,
                "money/add_me_amount.html",
                {
                    "chitti": chitti,
                    "selected_month": selected_month,
                    "error": "Enter a valid amount."
                }
            )

        PaymentTransaction.objects.create(
            chitti=chitti,
            participant=me,
            payment_month=selected_month.month,
            amount=amount,
        )

        return redirect(
            f"/chitti/{chitti.id}/?month={selected_month.id}"
        )

    return render(
        request,
        "money/add_me_amount.html",
        {
            "chitti": chitti,
            "selected_month": selected_month,
        }
    )
def payment_history(request, chitti_id, participant_id):

    chitti = get_object_or_404(
        Chitti,
        id=chitti_id
    )

    participant = get_object_or_404(
        Participant,
        id=participant_id,
        chitti=chitti,
        is_me=False
    )

    month_id = request.GET.get("month")

    selected_month = get_object_or_404(
        ChittiMonth,
        id=month_id,
        chitti=chitti
    )

    payments = PaymentTransaction.objects.filter(
        chitti=chitti,
        participant=participant,
        payment_month=selected_month.month
    ).order_by("created_at")

    return render(
        request,
        "money/payment_history.html",
        {
            "chitti": chitti,
            "participant": participant,
            "selected_month": selected_month,
            "payments": payments,
        }
    )