import re, subprocess, json
since='"'"'2026-01-25'"'"'
commits=subprocess.check_output(['"'"'git'"'"','"'"'log'"'"',f'"'"'--since={since}'"'"','"'"'--pretty=format:%H'"'"'],text=True).splitlines()
rows=[]
for c in commits:
    date=subprocess.check_output(['"'"'git'"'"','"'"'show'"'"','"'"'-s'"'"','"'"'--format=%ad'"'"','"'"'--date=short'"'"',c],text=True).strip()
    subject=subprocess.check_output(['"'"'git'"'"','"'"'show'"'"','"'"'-s'"'"','"'"'--format=%s'"'"',c],text=True).strip()
    diff=subprocess.check_output(['"'"'git'"'"','"'"'show'"'"','"'"'--unified=0'"'"','"'"'--pretty=format:'"'"',c,'"'"'--'"'"','"'"'*.sql'"'"','"'"'*.py'"'"','"'"'*.js'"'"','"'"'*.ts'"'"'],text=True,errors='"'"'ignore'"'"')
    current='"'"''"'"'
    for line in diff.splitlines():
        m=re.match(r'"'"'^\+\+\+ b/(.+)$'"'"',line)
        if m:
            current=m.group(1)
            continue
        m=re.match(r'"'"'^\+\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"\[]?[A-Za-z0-9_\.]+[`"\]]?)\s*\('"'"',line,re.I)
        if m:
            name=m.group(1).strip('"'"'`"[]'"'"')
            rows.append({'"'"'table'"'"':name,'"'"'commit'"'"':c,'"'"'date'"'"':date,'"'"'file'"'"':current,'"'"'subject'"'"':subject})
seen=set(); out=[]
for r in sorted(rows,key=lambda x:(x['"'"'table'"'"'],x['"'"'date'"'"'],x['"'"'commit'"'"'],x['"'"'file'"'"'])):
    k=(r['"'"'table'"'"'],r['"'"'commit'"'"'],r['"'"'file'"'"'])
    if k in seen:
        continue
    seen.add(k)
    out.append(r)
print(json.dumps(out,indent=2))
