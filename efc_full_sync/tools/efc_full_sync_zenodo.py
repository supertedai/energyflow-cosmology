import requests

ZENODO_API = "https://zenodo.org/api/deposit/depositions"


class ZenodoError(Exception):
    pass


def publish_pdf_to_zenodo(pdf_path, metadata):
    token = metadata["token"]
    meta = metadata["zenodo"]

    # 1. Create deposition
    r = requests.post(
        f"{ZENODO_API}?access_token={token}",
        json={}
    )
    if r.status_code not in (200, 201):
        raise ZenodoError(f"Create deposition failed: {r.status_code} {r.text}")

    dep = r.json()
    dep_id = dep["id"]
    bucket_url = dep["links"]["bucket"]

    # 2. Upload file
    with open(pdf_path, "rb") as fp:
        r = requests.put(
            f"{bucket_url}/paper.pdf",
            data=fp,
            headers={"Content-Type": "application/pdf"}
        )
        if r.status_code not in (200, 201):
            raise ZenodoError(f"File upload failed: {r.status_code} {r.text}")

    # 3. Update metadata
    r = requests.put(
        f"{ZENODO_API}/{dep_id}?access_token={token}",
        json={"metadata": meta}
    )
    if r.status_code not in (200, 201):
        raise ZenodoError(f"Metadata update failed: {r.status_code} {r.text}")

    # 4. Publish
    r = requests.post(
        f"{ZENODO_API}/{dep_id}/actions/publish?access_token={token}"
    )
    if r.status_code not in (200, 201, 202):
        raise ZenodoError(f"Publish failed: {r.status_code} {r.text}")

    return dep["links"]["record_html"]
