from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import User
from .models import Listing

from .forms import ListingForm
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404

from .models import Listing, Bid, Comment
from .forms import BidForm, CommentForm

from .models import Category

from django.contrib.auth.decorators import login_required

def index(request):
    listings = Listing.objects.filter(is_active=True)

    return render(request, "auctions/index.html", {
        "listings": listings
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    

@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)

        if form.is_valid():
            listing = form.save(commit=False)

            listing.created_by = request.user
            listing.current_price = listing.starting_bid
            listing.is_active = True

            listing.save()
            form.save_m2m()

            return redirect("index")

    else:
        form = ListingForm()

    return render(request, "auctions/create_listing.html", {
        "form": form
    })


def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    bid_form = BidForm()
    comment_form = CommentForm()

    message = None

    if request.method == "POST":

        # 🔥 BIDDING
        if "bid_submit" in request.POST:
            bid_form = BidForm(request.POST)

            if bid_form.is_valid():
                bid_amount = bid_form.cleaned_data["amount"]

                if bid_amount < listing.starting_bid:
                    message = "Bid must be at least the starting bid."

                elif bid_amount <= listing.current_price:
                    message = "Bid must be higher than current price."

                else:
                    bid = bid_form.save(commit=False)
                    bid.user = request.user
                    bid.listing = listing
                    bid.save()

                    listing.current_price = bid_amount
                    listing.save()

                    message = "Bid placed successfully!"

        # 💬 COMMENTS
        elif "comment_submit" in request.POST:
            comment_form = CommentForm(request.POST)

            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.listing = listing
                comment.save()

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid_form": bid_form,
        "comment_form": comment_form,
        "message": message,
        "comments": listing.comments.all()
    })

@login_required
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if request.user in listing.watchlist.all():
        listing.watchlist.remove(request.user)
    else:
        listing.watchlist.add(request.user)

    return HttpResponseRedirect(reverse("listing_detail", args=[listing_id]))


@login_required
def watchlist(request):
    listings = request.user.watchlist.all()

    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def categories(request):
    categories = Category.objects.all()

    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = Listing.objects.filter(category=category, is_active=True)

    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings
    })


@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    # only creator can close
    if request.user == listing.created_by:

        # get highest bid
        highest_bid = listing.bids.order_by('-amount').first()

        if highest_bid:
            listing.winner = highest_bid.user

        listing.is_active = False
        listing.save()

    return HttpResponseRedirect(reverse("listing_detail", args=[listing_id]))