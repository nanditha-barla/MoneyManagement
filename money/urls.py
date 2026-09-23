from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "create-chitti/",
        views.create_chitti,
        name="create_chitti"
    ),

    path(
        "chitti/<int:chitti_id>/",
        views.chitti_detail,
        name="chitti_detail"
    ),

    path(
        "chitti/<int:chitti_id>/person/<int:participant_id>/",
        views.person_view,
        name="person_view"
    ),

    path(
        "chitti/<int:chitti_id>/me/",
        views.me_view,
        name="me_view"
    ),

    path(
        "chitti/<int:chitti_id>/payment/<int:participant_id>/",
        views.add_payment,
        name="add_payment"
    ),

    path(
        "chitti/<int:chitti_id>/confirm/<int:participant_id>/",
        views.confirm_status,
        name="confirm_status"
    ),

    path(
        "chitti/<int:chitti_id>/take/<int:participant_id>/",
        views.take_chitti,
        name="take_chitti"
    ),

    path(
        "chitti/<int:chitti_id>/take-me/",
        views.take_me_chitti,
        name="take_me_chitti"
    ),

    path(
        "chitti/<int:chitti_id>/complete/",
        views.complete_month,
        name="complete_month"
    ),

    path(
        "chitti/<int:chitti_id>/me/add/",
        views.add_me_amount,
        name="add_me_amount"
    ),
    path(
    "payment/<int:payment_id>/edit/",
    views.edit_payment,
    name="edit_payment"
),
path(
    "chitti/<int:chitti_id>/delete/",
    views.delete_chitti,
    name="delete_chitti"
),
path(
    "chitti/<int:chitti_id>/person/<int:participant_id>/payments/",
    views.payment_history,
    name="payment_history"
),
path(
    "chitti/<int:chitti_id>/edit/",
    views.edit_chitti,
    name="edit_chitti"
),
]