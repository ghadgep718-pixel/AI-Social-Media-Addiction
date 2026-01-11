import requests

BASE = 'http://127.0.0.1:5000'

s = requests.Session()

# Test signup
signup_data = {'name':'Test User','email':'testuser@example.com','password':'pass123'}
r = s.post(BASE + '/signup', data=signup_data, allow_redirects=True)
print('Signup status:', r.status_code)
print('Signup page contains success:', 'Successfully signed up' in r.text)

# Test analyze GET
r = s.get(BASE + '/analyze')
print('Analyze GET status (should be 200):', r.status_code)

# Test posting usage
post_data = {
    'name':'Test User',
    'instagram':'1.5',
    'youtube':'2.3',
    'whatsapp':'0.7',
    # screen_time should be auto-summed by frontend; include it as sum
    'screen_time':'4.5',
    'sleep_hours':'7'
}
r = s.post(BASE + '/add', data=post_data, allow_redirects=True)
print('Add POST status:', r.status_code)
# If redirected to result, check result page for total_social and screen_time
if r.status_code == 200:
    print('Result contains Total Screen Time:', 'Total Screen Time' in r.text or 'Screen Time' in r.text)
else:
    print('Add response length:', len(r.text))

# Sign out
r = s.get(BASE + '/signout')
print('Signed out, status:', r.status_code)
