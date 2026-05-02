import resend

cfg = {}
for line in open('resend_config.txt').readlines():
    if '=' in line:
        k, v = line.strip().split('=', 1)
        cfg[k.strip()] = v.strip()

resend.api_key = cfg['RESEND_API_KEY']

html = "<h2>Chao Phuong!</h2><p>Email tu dong chay thanh cong.</p>"

params = {
    "from": "onboarding@resend.dev",
    "to": [cfg['RESEND_TO_TEST']],
    "subject": "Test - He Thong Email Chay!",
    "html": html,
}
r = resend.Emails.send(params)
print("Ket qua:", r)
