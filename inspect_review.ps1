from app import create_app
app=create_app('development')
c=app.test_client()
print('login', c.post('/auth/login', data={'username':'admin','password':'admin123'}, follow_redirects=False).status_code)
steps=[('/backup/create-step-1', {'vms':['1']}),('/backup/create-step-2', {'storageType':'local','server_address':'C:/temp/backups','username':'u','password':'p'}),('/backup/create-step-3', {'compression':'standard','deduplication':'on'}),('/backup/create-step-4', {'passphrase':'123456789012','confirm_passphrase':'123456789012'})]
for path, data in steps:
    r=c.post(path, data=data, follow_redirects=False)
    with c.session_transaction() as s:
        print(path, r.status_code, r.headers.get('Location'))
        print('job=', s.get('backup_job'))
rv=c.get('/backup/review')
text=rv.get_data(as_text=True)
print('review', rv.status_code)
print('selected count block:', text[text.find('Selected VMs'):text.find('Target Location')])
print('destination block:', text[text.find('Target Location'):text.find('Compression Level')])
print('compression block:', text[text.find('Compression Level'):text.find('Encryption Status')])
print('encryption block:', text[text.find('Encryption Status'):text.find('Review these settings')])
