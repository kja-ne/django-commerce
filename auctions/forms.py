from django import forms
from .models import Listing
from .models import Bid



class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            "title",
            "description",
            "starting_bid",
            "image_url",
            "category"
        ]

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ["amount"]