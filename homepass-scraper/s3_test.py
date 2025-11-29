import os, io, requests, boto3

BUCKET = os.environ.get("BUCKET", "inha-capstone-10-s3") 
REGION = os.environ.get("AWS_REGION", "us-west-2")

s3 = boto3.client("s3", region_name=REGION)

def download_pdf(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def upload_pdf(key: str, data: bytes):
    s3.upload_fileobj(io.BytesIO(data), BUCKET, key, ExtraArgs={"ContentType": "application/pdf"})

def get_pdf(key: str) -> bytes:
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    return obj["Body"].read()

if __name__ == "__main__":
    url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    key = "raw/sample.pdf"

    blob = download_pdf(url)
    upload_pdf(key, blob)
    print(f"uploaded s3://{BUCKET}/{key}")

    data = get_pdf(key)
    print(f"downloaded bytes {len(data)}")
