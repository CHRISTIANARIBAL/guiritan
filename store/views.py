from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Order, OrderItem, CartItem, ShoeSize
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

def home(request):
    products = Product.objects.all()
    return render(request, 'store/home.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})

# --- Cart functionalities ---
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('home')

def cart(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())
    cart_items = []
    total = 0

    for product in products:
        quantity = cart[str(product.id)]
        total_price = product.price * quantity
        cart_items.append({'product': product, 'quantity': quantity, 'total_price': total_price})
        total += total_price

    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
    request.session['cart'] = cart
    return redirect('cart')

def increase_quantity(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    request.session['cart'] = cart
    return redirect('cart')

def decrease_quantity(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        if cart[str(product_id)] > 1:
            cart[str(product_id)] -= 1
        else:
            del cart[str(product_id)]
    request.session['cart'] = cart
    return redirect('cart')

def login_view(request):
    # If user is already logged in as admin in admin session, redirect them
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        messages.info(request, "You are logged in as admin. Please log out from admin first.")
        return redirect('admin_login')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Prevent admin/staff users from logging in on frontend with regular session
            if user.is_staff or user.is_superuser:
                messages.error(request, "Admin accounts cannot log in through the user site. Please use admin login.")
                return redirect('login')

            # Normal user login
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'store/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')

        User.objects.create_user(username=username, password=password)
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')

    return render(request, 'store/register.html')

@login_required
def checkout(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_items')

        if not selected_ids:
            messages.error(request, "Please select at least one item to checkout.")
            return redirect('cart')

        cart = request.session.get('cart', {})
        selected_products = Product.objects.filter(id__in=selected_ids)

        total_price = 0
        order = Order.objects.create(user=request.user, total_price=0)
        order_items = []

        for product in selected_products:
            quantity = cart.get(str(product.id), 0)
            if quantity > 0:
                item_total = product.price * quantity
                total_price += item_total

                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
                order_items.append(order_item)
                cart.pop(str(product.id), None)

        order.total_price = total_price
        order.save()
        request.session['cart'] = cart

        return render(request, 'store/order_confirmation.html', {
            'order': order,
            'order_items': order_items
        })

    return redirect('cart')

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})

def admin_login(request):
    # If a user is logged in but not admin, log them out
    if request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
        logout(request)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            messages.success(request, "Admin login successful!")
            return redirect('myadmin')
        else:
            messages.error(request, "Invalid admin credentials.")
            return redirect('admin_login')

    return render(request, 'store/admin_login.html')


def admin_logout(request):
    logout(request)
    messages.success(request, "Admin logout successful!")
    return redirect('admin_login')

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin)
@login_required
def admin_dashboard(request):
    return render(request, "store/myadmin.html")

@user_passes_test(is_admin)
@login_required
def myadmin(request):
    from .models import Product, Category, Order

    products = Product.objects.all().order_by('-id')
    categories = Category.objects.all().order_by('name')
    orders = Order.objects.all().order_by('-id')

    context = {
        'products': products,
        'categories': categories,
        'orders': orders,
    }
    return render(request, 'store/myadmin.html', context)

def add_product(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')

    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        # Handle category
        category_id = request.POST.get('category')
        new_category = request.POST.get('new_category').strip() if request.POST.get('new_category') else ""

        if new_category:
            category, _ = Category.objects.get_or_create(name=new_category)
        elif category_id:
            category = Category.objects.get(id=category_id)
        else:
            messages.error(request, "Please select or create a category.")
            return redirect('add_product')

        # Handle size
        size_id = request.POST.get('size')
        new_size = request.POST.get('new_size').strip() if request.POST.get('new_size') else ""

        if new_size:
            shoe_size, _ = ShoeSize.objects.get_or_create(size=new_size)
        elif size_id:
            shoe_size = ShoeSize.objects.get(id=size_id)
        else:
            shoe_size = None  # Optional — depending on your Product model

        # ✅ Create the product
        Product.objects.create(
            name=name,
            price=price,
            stock=stock,
            description=description,
            image=image,
            category=category,
            size=shoe_size
        )

        messages.success(request, "✅ Product added successfully!")
        return redirect('myadmin')

    # GET request — load form
    categories = Category.objects.all()
    sizes = ShoeSize.objects.all()
    return render(request, 'store/add_product.html', {'categories': categories, 'sizes': sizes})


from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category

def edit_product(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')

    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    sizes = ShoeSize.objects.all()  # ✅ FIXED

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        new_category = request.POST.get('new_category')
        size_id = request.POST.get('size')
        new_size = request.POST.get('new_size')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        # ✅ Category handling
        if new_category:
            category, _ = Category.objects.get_or_create(name=new_category)
        elif category_id:
            category = get_object_or_404(Category, id=category_id)
        else:
            category = product.category  # keep existing

        # ✅ Size handling (ShoeSize)
        if new_size:
            size, _ = ShoeSize.objects.get_or_create(size=new_size)
        elif size_id:
            size = get_object_or_404(ShoeSize, id=size_id)
        else:
            size = product.size  # keep existing

        # ✅ Update product fields
        product.name = name
        product.category = category
        product.size = size
        product.price = price
        product.stock = stock
        product.description = description
        if image:
            product.image = image
        product.save()

        return redirect('myadmin')

    return render(request, 'store/edit_product.html', {
        'product': product,
        'categories': categories,
        'sizes': sizes
    })

def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.delete()
        return redirect('myadmin')  # ✅ always return after deleting

    # ✅ If it's a GET request, show a confirmation page
    return render(request, 'store/confirm_delete.html', {'product': product})

def orders_page(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')

    query = request.GET.get('q', '')

    # ✅ Filter orders if there's a search query
    if query:
        orders = Order.objects.filter(
            user__username__icontains=query
        ) | Order.objects.filter(
            items__product__name__icontains=query
        )
        orders = orders.distinct()
    else:
        orders = Order.objects.all()

    # ✅ Render the template with context
    return render(request, 'store/orders.html', {
        'orders': orders,
        'query': query,
    })
def add_category(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')
    # Your add category implementation
    pass


def edit_category(request, category_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')

    # ✅ Get the category or show 404 if not found
    category = get_object_or_404(Category, id=category_id)

    # ✅ If form is submitted, update the name
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category.name = name
            category.save()
            # Redirect to admin page after saving
            return redirect('myadmin')

    # ✅ If GET request, show edit form
    return render(request, 'store/edit_category.html', {'category': category})


def delete_category(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')

    try:
        category = Category.objects.get(pk=pk)
        category.delete()
        messages.success(request, "Category deleted successfully.")
    except Category.DoesNotExist:
        messages.error(request, "Category not found.")

    return redirect('myadmin')

def delete_order(request, order_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')

    # Only allow POST requests for safety
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.delete()
        # Redirect back to orders page after deleting
        return redirect('orders_page')

    # If someone tries to access via GET, redirect back safely
    return redirect('orders_page')

def delete_all_orders(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')

    # Only allow POST requests for safety
    if request.method == 'POST':
        Order.objects.all().delete()
        # Redirect back to the orders page after deleting
        return redirect('orders_page')

    # If someone tries to access via GET, just redirect safely
    return redirect('orders_page')