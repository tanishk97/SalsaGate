import os, json, hashlib, tempfile, subprocess, boto3

S3 = boto3.client("s3")
DDB = boto3.resource("dynamodb")
TABLE = os.getenv("LEDGER_TABLE", "")
ISSUER = os.getenv("OIDC_ISSUER", "https://token.actions.githubusercontent.com")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()

def cosign_verify_sig(file_path, cert_path, sig_path):
    cmd = [
        "cosign","verify-blob",
        "--certificate-oidc-issuer", ISSUER,
        "--certificate-identity-regexp","https://github.com/.+",
        "--signature", sig_path,
        "--certificate", cert_path,
        file_path
    ]
    return run(cmd)

def cosign_verify_att(file_path):
    cmd = [
        "cosign","verify-blob-attestation",
        "--type","slsaprovenance",
        "--certificate-oidc-issuer", ISSUER,
        "--certificate-identity-regexp","https://github.com/.+",
        file_path
    ]
    return run(cmd)

def run(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return True, out
    except subprocess.CalledProcessError as e:
        return False, e.output

def tag_object(bucket,key,tags):
    S3.put_object_tagging(Bucket=bucket, Key=key,
        Tagging={"TagSet":[{"Key":k,"Value":v} for k,v in tags.items()]})

def put_ledger(uri,status,details):
    if not TABLE: return
    DDB.Table(TABLE).put_item(Item={"object_key":uri,"status":status,"details":details[:3000]})

def handler(event, _):
    # Supports: { "bucket": "...", "key": "..." } OR S3 ObjectCreated event
    if isinstance(event, dict) and "bucket" in event and "key" in event:
        bucket, key = event["bucket"], event["key"]
    else:
        rec = event["Records"][0]
        bucket = rec["s3"]["bucket"]["name"]
        key = rec["s3"]["object"]["key"]

    base = key.rsplit("/",1)[-1]
    sig = base + ".sig"
    pem = base + ".pem"

    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, base); s = os.path.join(d, sig); p = os.path.join(d, pem)
        S3.download_file(bucket, key, f)
        S3.download_file(bucket, sig, s)
        S3.download_file(bucket, pem, p)
        digest = sha256(f)
        ok1, out1 = cosign_verify_sig(f,p,s)
        ok2, out2 = cosign_verify_att(f)

    uri = f"s3://{bucket}/{key}"
    if ok1 and ok2:
        tag_object(bucket,key,{"trust":"verified","digest":digest})
        put_ledger(uri,"verified", out1+"\n"+out2)
        return {"verified": True, "digest": digest}
    else:
        put_ledger(uri,"failed", (out1 if not ok1 else "") + (out2 if not ok2 else ""))
        raise Exception(f"Verification failed for {uri}")
