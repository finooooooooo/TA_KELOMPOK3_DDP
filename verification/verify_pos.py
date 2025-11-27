from playwright.sync_api import Page, expect, sync_playwright

def verify_pos_flow(page: Page):
    # 1. Login as Cashier
    page.goto("http://127.0.0.1:5000/auth/login")
    page.fill('input[name="username"]', 'cashier')
    page.fill('input[name="password"]', 'cashier123')
    page.click('button[type="submit"]')

    # 2. Verify Redirect to POS
    expect(page).to_have_url("http://127.0.0.1:5000/pos/")

    # 3. Wait for products to load (dynamic fetch)
    page.wait_for_selector('h3', state='visible')

    # 4. Add items to cart
    # Click first product (Latte - Unmanaged)
    page.locator('.bg-white.p-4').first.click()

    # 5. Check Cart Update
    expect(page.locator('#cart-total')).not_to_have_text("$0.00")

    # 6. Take Screenshot of POS with items
    page.screenshot(path="verification/pos_cart.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_pos_flow(page)
        finally:
            browser.close()
