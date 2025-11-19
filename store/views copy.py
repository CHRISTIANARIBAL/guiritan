from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, ShoeSize, Order, OrderItem, CartItem, ShoeSize
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ProductForm 
from django.db.models import Q

# 🏠 Home
def home(request):
    products = Product.objects.all()
    return render(request, 'store/home.html', {'products': products})

# 🧾 Product detail
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})

# 🛒 Cart
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('home')

def cart(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())
    cart_items, total = [], 0
    for product in products:
        quantity = cart[str(product.id)]
        total_price = product.price * quantity
        cart_items.append({'product': product, 'quantity': quantity, 'total_price': total_price})
        total += total_price
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})

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
            # Optional: remove the item completely if it hits 0
            cart.pop(str(product_id))
    request.session['cart'] = cart
    return redirect('cart')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    return redirect('cart')

# 👤 User Login / Logout / Register
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser or user.is_staff:
                messages.error(request, "Admin accounts cannot log in through user site.")
                return redirect('login')
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

# 🧾 Checkout
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

        for product in selected_products:
            quantity = cart.get(str(product.id), 0)
            if quantity > 0:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
                total_price += product.price * quantity
                cart.pop(str(product.id), None)

        order.total_price = total_price
        order.save()
        request.session['cart'] = cart

        # ✅ Add this line to include order items in the template
        order_items = OrderItem.objects.filter(order=order)

        return render(request, 'store/order_confirmation.html', {
            'order': order,
            'order_items': order_items,  # <-- important
        })
    
    return redirect('cart')


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})

# 👑 Admin Login
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        print("🔐 Attempting admin login for:", username)
        if user is not None and user.is_superuser:
            login(request, user)
            print("✅ Authenticated admin:", user.username)
            return redirect('myadmin')
        else:
            messages.error(request, "Invalid credentials or not a superuser.")
            print("❌ Failed admin login")
            return redirect('admin_login')

    return render(request, 'store/admin_login.html')

# ✅ Admin Views
def is_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin)
def myadmin(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    sizes = ShoeSize.objects.all()
    orders = Order.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'sizes': sizes,
        'orders': orders,
    }
    return render(request, 'store/myadmin.html', context)

@user_passes_test(lambda u: u.is_superuser)
@login_required
def add_product(request):
    categories = Category.objects.all()
    sizes = ShoeSize.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        new_category = request.POST.get("new_category")
        size_id = request.POST.get("size")
        new_size = request.POST.get("new_size")
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        # ✅ Create new category if typed
        if new_category:
            category, created = Category.objects.get_or_create(name=new_category)
        else:
            category = Category.objects.get(id=category_id)

        # ✅ Create new size if typed
        # ✅ Size handling (allow only integers)
        if new_size:
            if not new_size.isdigit():  # <-- This checks if input is all numbers
                messages.error(request, "❌ Size must be an integer (e.g. 38, 42).")
                return redirect("add_product")

            size_value = int(new_size)
            size, _ = ShoeSize.objects.get_or_create(size=size_value)
        else:
            size = ShoeSize.objects.get(id=size_id)

        # ✅ Save product
        Product.objects.create(
            name=name,
            category=category,
            size=size,
            price=price,
            stock=stock,
            description=description,
            image=image
        )

        messages.success(request, "✅ Product added successfully!")
        return redirect("myadmin")

    return render(request, "store/add_product.html", {
        "categories": categories,
        "sizes": sizes
    })

@user_passes_test(is_admin)
@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    sizes = ShoeSize.objects.all()

    if request.method == 'POST':
        # Basic fields
        name = request.POST.get('name', product.name).strip()
        price = request.POST.get('price', product.price)
        stock = request.POST.get('stock', product.stock)
        description = request.POST.get('description', product.description)

        # Category: either chosen existing id or typed new_category
        category_id = request.POST.get('category')
        new_category = request.POST.get('new_category', '').strip()

        try:
            if new_category:
                category, _ = Category.objects.get_or_create(name=new_category)
            elif category_id:
                category = Category.objects.get(id=category_id)
            else:
                category = product.category
        except Category.DoesNotExist:
            messages.error(request, "Selected category does not exist.")
            return redirect('edit_product', pk=product.pk)

        # Size: either chosen existing id or typed new_size
        size_id = request.POST.get('size')
        new_size = request.POST.get('new_size', '').strip()

        try:
            if new_size:
                size, _ = ShoeSize.objects.get_or_create(size=new_size)
            elif size_id:
                size = ShoeSize.objects.get(id=size_id)
            else:
                size = product.size
        except ShoeSize.DoesNotExist:
            messages.error(request, "Selected size does not exist.")
            return redirect('edit_product', pk=product.pk)

        # Assign values to product
        product.name = name
        # price and stock cast (keep existing value if casting fails)
        try:
            product.price = float(price)
        except Exception:
            pass
        try:
            product.stock = int(stock)
        except Exception:
            pass

        product.description = description
        product.category = category
        product.size = size

        # Image: replace only if a file was uploaded
        if 'image' in request.FILES and request.FILES['image']:
            product.image = request.FILES['image']

        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect('myadmin')

    # GET -> render form with context
    return render(request, 'store/edit_product.html', {
        'product': product,
        'categories': categories,
        'sizes': sizes,
    })

@user_passes_test(is_admin)
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "🗑️ Product deleted successfully!")
        return redirect('myadmin')
    return render(request, 'store/delete_product.html', {'product': product})

def admin_products(request):
    products = Product.objects.all()  # fetch all products
    return render(request, 'admin/products.html', {'products': products})


# ✅ Add new category
@login_required
@user_passes_test(is_admin)
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if not name.strip():
            messages.error(request, "❌ Category name cannot be empty.")
            return redirect("myadmin")

        Category.objects.get_or_create(name=name.strip())
        messages.success(request, f"✅ Category '{name}' added successfully!")
        return redirect("myadmin")

    return redirect("myadmin")

# ✅ Edit category
@login_required
@user_passes_test(is_admin)
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        new_name = request.POST.get("name")
        if not new_name.strip():
            messages.error(request, "❌ Category name cannot be empty.")
            return redirect("myadmin")

        category.name = new_name.strip()
        category.save()
        messages.success(request, "✅ Category updated successfully!")
        return redirect("myadmin")

    return render(request, "store/edit_category.html", {"category": category})


# ✅ Delete category
@login_required
@user_passes_test(is_admin)
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, "🗑️ Category deleted successfully!")
        return redirect("myadmin")

    return render(request, "store/confirm_delete_category.html", {"category": category})

@login_required
def orders_page(request):
    query = request.GET.get('q', '')
    orders = Order.objects.all().order_by('-created_at')

    if query:
        orders = orders.filter(
            Q(user__username__icontains=query) |
            Q(id__icontains=query) |
            Q(orderitem__product__name__icontains=query)
        ).distinct()

    return render(request, 'store/orders.html', {'orders': orders, 'query': query})

def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, f"Order #{order_id} deleted successfully.")
    return redirect('orders_page')

def delete_all_orders(request):
    Order.objects.all().delete()
    messages.success(request, "All orders deleted successfully.")
    return redirect('orders_page')