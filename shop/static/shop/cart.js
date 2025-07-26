// Cart functionality
// Initialize cart from localStorage or create empty cart

// Function to validate and clean cart data
function validateCart(cartData) {
    var validCart = {};
    for (var itemId in cartData) {
        var item = cartData[itemId];
        if (Array.isArray(item) &&
            item.length === 3 &&
            typeof item[0] === 'number' &&
            typeof item[1] === 'string' &&
            typeof item[2] === 'number' &&
            !isNaN(item[2])) {
            validCart[itemId] = item;
        }
    }
    return validCart;
}

// Get cart key based on user ID
function getCartKey() {
    return USER_ID && USER_ID !== 0 ? 'cart_' + USER_ID : 'cart_anonymous';
}
var cart = localStorage.getItem(getCartKey()) ? validateCart(JSON.parse(localStorage.getItem(getCartKey()))) : {};


// Function to save cart to localStorage and update UI
function saveCart() {
    localStorage.setItem(getCartKey(), JSON.stringify(cart));
    // updateCartCount();
    updateCartPopover();
}

// Function to add item to cart
function addItem(itemId, name, price, quantity = 1) {
    // Remove currency symbols and parse price
    price = parseFloat(String(price).replace(/[^0-9.]/g, ''));
    if (isNaN(price)) {
        console.error('Invalid price for item:', name);
        return;
    }
    if (cart[itemId]) {
        cart[itemId][0] += quantity; // Update quantity
        cart[itemId][2] += price * quantity; // Update total price
    } else {
        cart[itemId] = [quantity, name, price * quantity]; // [quantity, name, total_price]
    }
    saveCart();
    showToast(`Added ${quantity} ${quantity > 1 ? 'items' : 'item'} to your cart!`);
}

// Function to update cart count in navbar
function updateCartCount() {
    var count = 0;
    for (var itemId in cart) {
        count += cart[itemId][0]; // Sum quantities
    }
    $('.cart-count').text(count);
}

function updateCartPopover() {
    var cartString = '<h5>Your Cart</h5>';
    if (Object.keys(cart).length === 0) {
        cartString += '<p>Your cart is empty</p>';
    } else {
        var cartIndex = 1;
        var total = 0;
        for (var itemId in cart) {
            var item = cart[itemId];
            if (!item || typeof item[2] !== 'number' || isNaN(item[2])) {
                console.warn('Skipping invalid cart item:', itemId);
                continue;
            }
            cartString += `
                <div class="cart-item" >
                    <span class="item-details">${cartIndex}. ${item[1]} × ${item[0]}</span>
                    <span class="item-price" >Rs ${item[2].toFixed(2)}</span>
                    <div class="item-actions">
                        <button class="btn-decrease" data-id="${itemId}" >-</button>
                        <button class="btn-increase" data-id="${itemId}" >+</button>
                    </div>
                </div>`;
            total += item[2];
            cartIndex++;
        }
        cartString += `
            <div class="cart-total mt-2 pt-2 border-top">
                <strong>Total: Rs ${total.toFixed(2)}</strong>
            </div>`;
    }
    cartString += '<a href="/checkout" class="btn btn-success btn-block mt-2">Checkout</a>';

    $('#cart').popover('dispose');
    $('#cart').popover({
        html: true,
        placement: 'bottom',
        trigger: 'click',
        content: cartString, 
        sanitize: false // Allow HTML content
    });

    // Update cart count
    var count = 0;
    for (var itemId in cart) {
        count += cart[itemId][0];
    }
    $('.cart-count').text(count);
}
$(document).on('click', '.btn-increase', function (e) {
    e.stopPropagation();
    const id = $(this).data('id');
    if (cart[id]) {
        const unitPrice = cart[id][2] / cart[id][0]; // calculate price per item
        cart[id][0] += 1;
        cart[id][2] += unitPrice;
        saveCart();  // IMPORTANT: Save and refresh popover
    }
});

$(document).on('click', '.btn-decrease', function (e) {
    e.stopPropagation();
    const id = $(this).data('id');
    if (cart[id]) {
        const unitPrice = cart[id][2] / cart[id][0];
        if (cart[id][0] > 1) {
            cart[id][0] -= 1;
            cart[id][2] -= unitPrice;
        } else {
            delete cart[id];
        }
        saveCart();  // IMPORTANT: Save and refresh popover
    }
});



// Function to show toast notification
function showToast(message) {
    var toast = $(`
<div class="toast" role="alert"
     style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000;
            background-color: #333; color: white; padding: 20px; border-radius: 8px;">

            <div class="toast-header bg-success text-white">
                <strong class="mr-auto">Success</strong>
                <button type="button" class="ml-2 mb-1 close text-white" data-dismiss="toast">×</button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `);
    $('body').append(toast);
    toast.toast({ delay: 3000 }).toast('show');
    toast.on('hidden.bs.toast', function () { $(this).remove(); });
}

// Initialize cart on page load
$(document).ready(function () {
    updateCartCount();
    updateCartPopover();

    // Close popover when clicking outside
    $('body').on('click', function (e) {
        if ($(e.target).data('toggle') !== 'popover' &&
            $(e.target).parents('[data-toggle="popover"]').length === 0 &&
            $(e.target).parents('.popover.show').length === 0) {
            $('#cart').popover('hide');
        }
    });
});

// Make cart and functions globally available
window.cart = cart;
window.addItem = addItem;
window.showToast = showToast;