import asyncio
import json
import requests
from pyppeteer import launch

site_details = {
    'sitekey': '6Le85FEkAAAAADRO-TcaDLFZBymeeA3wBen2sMlG',  # Your site's reCAPTCHA sitekey
    'pageurl': 'https://foreternia.com/wp-login.php'  # The URL where the reCAPTCHA is located
}

api_key = '4f4796c7c4782b0d8954dfghh500818c7d58e'  # Your 2Captcha API key

async def login():
    browser = await launch(headless=False, slowMo=10, args=['--no-sandbox', '--disable-setuid-sandbox'])
    page = await browser.newPage()

    await page.goto(site_details['pageurl'], {'waitUntil': 'networkidle2'})

    # Mimic human typing for login credentials
    await page.type('input#user_login', 'shahz@gmail.com', options={'delay': 100})
    await page.type('input#user_pass', 'testing_place_holder', options={'delay': 100})

    # Initiate captcha-solving request
    requestId = initiate_captcha_request(api_key)
    response = await poll_for_request_results(api_key, requestId)

    # Properly inject the captcha response and trigger any necessary JavaScript events
    await page.evaluate(f'''document.getElementById("g-recaptcha-response").innerHTML="{response}";''')
    await page.evaluate('''document.querySelector('.g-recaptcha').dispatchEvent(new Event('submit'));''')

    # Now remove the disabled attribute from the login button
    await page.evaluate('''document.getElementById('wp-submit').removeAttribute('disabled');''')

    # Click the login button
    await page.click('input#wp-submit')

    await page.waitForNavigation({'waitUntil': 'networkidle0'})

    print('Login successful')
    await browser.close()

def initiate_captcha_request(api_key):
    formData = {
        'method': 'userrecaptcha',
        'googlekey': site_details['sitekey'],
        'key': api_key,
        'pageurl': site_details['pageurl'],
        'json': 1
    }
    response = requests.post('http://2captcha.com/in.php', data=formData)
    return json.loads(response.text)['request']

async def poll_for_request_results(key, requestId, retries=60, interval=5, delay=15):
    print("Polling for response...")
    await asyncio.sleep(delay)
    for attempt in range(retries):
        response = requests.get(f'http://2captcha.com/res.php?key={key}&action=get&id={requestId}&json=1')
        resp = json.loads(response.text)
        if resp['status'] == 1:
            print(f"Response received: {resp['request']}")
            return resp['request']
        else:
            print(f"At attempt {attempt + 1}: {resp.get('request', 'Captcha not ready')}")
        await asyncio.sleep(interval)
    raise Exception('Captcha not solved within retry limit')

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(login())
