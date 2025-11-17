const { chromium } = require('playwright')

async function run() {
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()

  page.on('console', (msg) => {
    console.log('[browser]', msg.type(), msg.text())
  })
  page.on('requestfailed', (req) => {
    console.log('[browser][requestfailed]', req.url(), req.failure()?.errorText)
  })

  console.log('Opening login page...')
  await page.goto('http://localhost:3020/login', { waitUntil: 'networkidle' })

  console.log('Filling credentials...')
  await page.fill('#email', 'customer@platepal.com')
  await page.fill('#password', 'customer123')

  console.log('Submitting form...')
  await Promise.all([
    page.waitForTimeout(3000),
    page.click('button[type="submit"]'),
  ])

  console.log('Login redirect URL:', page.url())

  console.log('Navigating to /restaurants ...')
  await page.goto('http://localhost:3020/restaurants', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)

  console.log('Restaurants page URL:', page.url())
  await browser.close()
}

run().catch((error) => {
  console.error('Playwright run failed:', error)
  process.exit(1)
})

