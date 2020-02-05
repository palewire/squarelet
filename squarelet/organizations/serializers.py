# Third Party
import stripe
from oidc_provider.models import Client
from rest_framework import serializers, status
from rest_framework.exceptions import APIException

# Squarelet
from squarelet.organizations.choices import StripeAccounts
from squarelet.organizations.models import (
    Charge,
    Entitlement,
    Invitation,
    Membership,
    Organization,
    Plan,
    Subscription,
)


class OrganizationSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    # XXX remove plan ??
    plan = serializers.SerializerMethodField()
    entitlements = serializers.SerializerMethodField()
    card = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "uuid",
            "name",
            "slug",
            "plan",
            "entitlements",
            "card",
            "max_users",
            "individual",
            "private",
            "update_on",
            "updated_at",
            "payment_failed",
            "avatar_url",
        )

    def get_plan(self, obj):
        return obj.plan.slug if obj.plan else "free"

    def get_entitlements(self, obj):
        # XXX performance
        request = self.context.get("request")
        if request and hasattr(request, "auth") and request.auth:
            return request.auth.client.entitlements.filter(
                plans__organization=obj
            ).values_list("slug", flat=True)
        return []

    def get_card(self, obj):
        # this can be slow - goes to stripe for customer/card info - cache this
        return obj.customer(StripeAccounts.muckrock).card_display


class MembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()

    class Meta:
        model = Membership
        fields = ("organization", "admin")

    def to_representation(self, instance):
        """Move fields from organization to membership representation."""
        # https://stackoverflow.com/questions/21381700/django-rest-framework-how-do-you-flatten-nested-data
        representation = super().to_representation(instance)
        organization_representation = representation.pop("organization")
        for key in organization_representation:
            representation[key] = organization_representation[key]

        return representation


class StripeError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Stripe error"


class ChargeSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True, required=False)
    save_card = serializers.BooleanField(write_only=True, required=False)
    organization = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Organization.objects.all()
    )

    class Meta:
        model = Charge
        fields = (
            "amount",
            "charge_id",
            "created_at",
            "description",
            "fee_amount",
            "organization",
            "save_card",
            "token",
        )
        read_only_fields = ("created_at", "charge_id")

    def create(self, validated_data):
        """Create the charge object locally and on stripe"""
        organization = validated_data["organization"]
        try:
            charge = organization.charge(
                validated_data["amount"],
                validated_data["description"],
                validated_data.get("fee_amount", 0),
                validated_data.get("token"),
                validated_data.get("save_card"),
            )
        except stripe.error.StripeError as exc:
            raise StripeError(exc.user_message)
        # add the card display to the response, so the client has immediate access
        # to the newly saved card
        data = {"card": organization.customer(StripeAccounts.muckrock).card_display}
        data.update(self.data)
        self._data = data
        return charge

    def validate(self, attrs):
        """Must supply token if saving card"""
        if attrs.get("save_card") and not attrs.get("token"):
            raise serializers.ValidationError(
                "Must supply a token if save card is true"
            )
        return attrs


# PressPass


class PressPassOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "uuid",
            "name",
            "slug",
            "max_users",
            "individual",
            "private",
            "update_on",
            "updated_at",
            "payment_failed",
            "avatar",
        )
        extra_kwargs = {
            "uuid": {"read_only": True},
            "slug": {"read_only": True},
            "max_users": {"required": False},
            "individual": {"read_only": True},
            "private": {"required": False},
            "update_on": {"read_only": True},
            "updated_at": {"read_only": True},
            "payment_failed": {"read_only": True},
            "avatar": {"required": False},
        }


class PressPassMembershipSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = Membership
        fields = ("user", "admin")
        extra_kwargs = {"admin": {"default": False}}


class PressPassNestedInvitationSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = Invitation
        fields = (
            "email",
            "user",
            "request",
            "created_at",
            "accepted_at",
            "rejected_at",
        )
        extra_kwargs = {
            "email": {"required": False},
            "request": {"read_only": True},
            "created_at": {"read_only": True},
            "accepted_at": {"read_only": True},
            "rejected_at": {"read_only": True},
        }

    def validate_email(self, value):
        request = self.context.get("request")
        view = self.context.get("view")
        organization = Organization.objects.get(uuid=view.kwargs["organization_uuid"])
        if organization.has_admin(request.user) and not value:
            raise serializers.ValidationError("You must supply en email")
        elif not organization.has_admin(request.user) and value:
            raise serializers.ValidationError("You must not supply en email")
        return value


class PressPassInvitationSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(slug_field="uuid", read_only=True)
    user = serializers.SlugRelatedField(slug_field="uuid", read_only=True)
    accept = serializers.BooleanField(write_only=True)
    reject = serializers.BooleanField(write_only=True)

    class Meta:
        model = Invitation
        fields = (
            "organization",
            "email",
            "user",
            "request",
            "created_at",
            "accepted_at",
            "rejected_at",
            "accept",
            "reject",
        )
        extra_kwargs = {
            "created_at": {"read_only": True},
            "accepted_at": {"read_only": True},
            "rejected_at": {"read_only": True},
            "email": {"read_only": True},
        }

    def validate(self, attrs):
        """Must not try to accept and reject"""
        if attrs.get("accept") and attrs.get("reject"):
            raise serializers.ValidationError(
                "May not accept and reject the invitation"
            )
        return attrs


class PressPassPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "name",
            "slug",
            "minimum_users",
            "base_price",
            "price_per_user",
            "public",
            "annual",
            "for_individuals",
            "for_groups",
            "entitlements",
        )


class PressPassEntitlmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entitlement
        fields = ("name", "slug", "client", "description")
        extra_kwargs = {"slug": {"read_only": True}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs.get("context", {})
        request = context.get("request")
        # may only create entitlements for your own clients
        if request and request.user and request.user.is_authenticated:
            self.fields["client"].queryset = Client.objects.filter(owner=request.user)
        else:
            self.fields["client"].queryset = Client.objects.none()


class PressPassSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("plan", "update_on", "cancelled")
        extra_kwargs = {
            "update_on": {"read_only": True},
            "cancelled": {"read_only": True},
        }
