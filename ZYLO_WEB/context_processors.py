from .models import UserProfilepictures
from ZYLO_SELLER.models import SellerProfile, storelogo

def global_context(request):
    if request.user.is_authenticated:
        user = request.user
        context = {
            'user': user,
            'profile_picture': None,
            'is_superuser': user.is_superuser,
            'is_store_approved': False,
            'logo': None,
            'store_name': None,
        }

        try:
            # Get or create profile picture
            profile_picture, created = UserProfilepictures.objects.get_or_create(user=user)
            context['profile_picture'] = profile_picture

            # Get seller profile
            seller_profile = SellerProfile.objects.get(user=user)
            context['is_store_approved'] = seller_profile.status == SellerProfile.SellerStatus.APPROVED

            # Fetch the store logo
            logo = storelogo.objects.get(store__user=user)
            context['logo'] = logo

            # Store name from the seller profile
            context['store_name'] = seller_profile.store_name  # Assuming store_name is a field in SellerProfile
        except SellerProfile.DoesNotExist:
            context['is_store_approved'] = False
        except storelogo.DoesNotExist:
            context['logo'] = None

        return context

    return {}