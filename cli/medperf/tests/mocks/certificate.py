from typing import Optional
from medperf.entities.certificate import Certificate


class TestCertificate(Certificate):
    id: Optional[int] = 1
    name: str = "name"
    certificate_content_base64: str = "Y29udGVudA=="
    ca: int = 1
