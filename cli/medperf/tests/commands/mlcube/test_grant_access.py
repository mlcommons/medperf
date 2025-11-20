import pytest
import base64
from medperf.exceptions import CleanExit, InvalidCertificateError
from medperf.commands.mlcube.grant_access import GrantAccess
from medperf.tests.mocks.certificate import TestCertificate
from medperf.tests.mocks.ca import TestCA
from medperf.tests.mocks.encrypted_key import TestEncryptedKey

PATCH_GRANTACCESS = "medperf.commands.mlcube.grant_access.{}"
BENCHMARK_ID = 1
MODEL_ID = 1
ALLOWED_EMAILS = "alice@example.com bob@example.com"


@pytest.fixture
def grantaccess(mocker, fs):
    mocker.patch(PATCH_GRANTACCESS.format("CA.get"), return_value=TestCA())
    mocker.patch(
        PATCH_GRANTACCESS.format("Certificate.get_benchmark_datasets_certificates"),
        return_value=(
            [TestCertificate(id=1), TestCertificate(id=2)],
            {1: {"email": "alice@example.com"}, 2: {"email": "charlie@example.com"}},
        ),
    )
    mocker.patch(
        PATCH_GRANTACCESS.format("EncryptedKey.get_container_keys"), return_value=[]
    )
    mocker.patch(
        PATCH_GRANTACCESS.format("AsymmetricEncryption.encrypt"),
        return_value=b"encrypted",
    )
    mocker.patch(PATCH_GRANTACCESS.format("EncryptedKey.upload_many"))
    mocker.patch(PATCH_GRANTACCESS.format("verify_certificate_authority"))
    mocker.patch(PATCH_GRANTACCESS.format("verify_certificate"))
    key_path = "keyfile"
    mocker.patch(
        PATCH_GRANTACCESS.format("get_decryption_key_path"), return_value="keyfile"
    )

    fs.create_file(key_path, contents=b"container_key_bytes")

    return GrantAccess(BENCHMARK_ID, MODEL_ID)


def test_get_approval_skips_if_preapproved(grantaccess):
    # Arrange
    grantaccess.approved = True

    # Act & Assert (Should not raise)
    grantaccess.get_approval()


def test_get_approval_raises_if_not_approved(mocker):
    # Arrange
    mocker.patch(PATCH_GRANTACCESS.format("approval_prompt"), return_value=False)
    ga = GrantAccess(BENCHMARK_ID, MODEL_ID, approved=False)

    # Act & Assert
    with pytest.raises(CleanExit):
        ga.get_approval()


@pytest.mark.parametrize(
    "emails,expected",
    [
        (
            "Alice@example.com  bob@example.com",
            ["alice@example.com", "bob@example.com"],
        ),
        (
            "BOB@example.com",
            ["bob@example.com"],
        ),
        (
            "",
            [],
        ),
    ],
)
def test_validate_allowed_emails_normalizes(mocker, grantaccess, emails, expected):
    # Arrange
    grantaccess.allowed_emails = emails

    # Act
    grantaccess.validate_allowed_emails()

    # Assert
    assert grantaccess.allowed_emails == expected


def test_validate_allowed_emails_does_nothing_if_emails_are_none(mocker, grantaccess):
    # Arrange
    grantaccess.allowed_emails = None

    # Act
    grantaccess.validate_allowed_emails()

    # Assert
    assert grantaccess.allowed_emails is None


def test_verify_certificate_authority_calls_verify(mocker, grantaccess):
    # Arrange
    spy = mocker.patch(PATCH_GRANTACCESS.format("verify_certificate_authority"))

    # Act
    grantaccess.verify_certificate_authority()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize(
    "existing,expected",
    [
        (
            [1, 2],
            [3],
        ),
        (
            [],
            [1, 2, 3],
        ),
        (
            [2],
            [1, 3],
        ),
    ],
)
def test_prepare_certificates_list_filters_existing_keys(mocker, existing, expected):
    # Arrange
    mocker.patch(
        PATCH_GRANTACCESS.format("EncryptedKey.get_container_keys"),
        return_value=[TestEncryptedKey(certificate=keyid) for keyid in existing],
    )
    mocker.patch(
        PATCH_GRANTACCESS.format("Certificate.get_benchmark_datasets_certificates"),
        return_value=(
            [
                TestCertificate(id=1),
                TestCertificate(id=2),
                TestCertificate(id=3),
            ],
            {
                1: {"email": "alice@example.com"},
                2: {"email": "bob@example.com"},
                3: {"email": "bob2@example.com"},
            },
        ),
    )

    ga = GrantAccess(BENCHMARK_ID, MODEL_ID)

    # Act
    ga.prepare_certificates_list()

    # Assert
    assert set([cert.id for cert in ga.certificates]) == set(expected)


@pytest.mark.parametrize(
    "existing_keys,existing_certs",
    [
        (
            [1, 2],
            [1, 2],
        ),
        (
            [],
            [],
        ),
    ],
)
def test_prepare_certificates_empty(mocker, existing_keys, existing_certs):
    # Arrange
    mocker.patch(
        PATCH_GRANTACCESS.format("EncryptedKey.get_container_keys"),
        return_value=[TestEncryptedKey(certificate=keyid) for keyid in existing_keys],
    )
    mocker.patch(
        PATCH_GRANTACCESS.format("Certificate.get_benchmark_datasets_certificates"),
        return_value=(
            [TestCertificate(id=cid) for cid in existing_certs],
            {cid: "email" for cid in existing_certs},
        ),
    )

    ga = GrantAccess(BENCHMARK_ID, MODEL_ID)

    # Act & Assert
    with pytest.raises(CleanExit):
        ga.prepare_certificates_list()


def test_filter_certificates_filters_by_allowed_emails(grantaccess):
    # Arrange
    grantaccess.certificates = [TestCertificate(id=1), TestCertificate(id=2)]
    grantaccess.cert_user_info = {
        1: {"email": "alice@example.com"},
        2: {"email": "charlie@example.com"},
    }
    grantaccess.allowed_emails = ["alice@example.com"]

    # Act
    grantaccess.filter_certificates()

    # Assert
    assert [cert.id for cert in grantaccess.certificates] == [1]


def test_filter_certificates_when_empty(grantaccess):
    # Arrange
    grantaccess.certificates = [TestCertificate(id=1), TestCertificate(id=2)]
    grantaccess.cert_user_info = {
        1: {"email": "alice@example.com"},
        2: {"email": "charlie@example.com"},
    }
    grantaccess.allowed_emails = []

    # Act & Assert
    with pytest.raises(CleanExit):
        grantaccess.filter_certificates()


def test_verify_certificates_filters_invalid_certs(mocker, grantaccess):
    # Arrange
    def verify_side_effect(cert, **kwargs):
        if cert.id == 2:
            raise InvalidCertificateError()

    mocker.patch(
        PATCH_GRANTACCESS.format("verify_certificate"), side_effect=verify_side_effect
    )
    grantaccess.certificates = [TestCertificate(id=1), TestCertificate(id=2)]
    grantaccess.cert_user_info = {
        1: {"email": "alice@example.com"},
        2: {"email": "bob@example.com"},
    }

    # Act
    grantaccess.verify_certificates()

    # Assert
    assert [cert.id for cert in grantaccess.certificates] == [1]


def test_verify_certificates_when_empty(mocker, grantaccess):
    # Arrange
    def verify_side_effect(cert, **kwargs):
        raise InvalidCertificateError()

    mocker.patch(
        PATCH_GRANTACCESS.format("verify_certificate"), side_effect=verify_side_effect
    )
    grantaccess.certificates = [TestCertificate(id=1), TestCertificate(id=2)]
    grantaccess.cert_user_info = {
        1: {"email": "alice@example.com"},
        2: {"email": "bob@example.com"},
    }

    # Act & Assert
    with pytest.raises(CleanExit):
        grantaccess.verify_certificates()


def test_generate_encrypted_keys_list_returns_keys(grantaccess):
    # Arrange
    grantaccess.certificates = [TestCertificate(id=1)]

    # Act
    keys = grantaccess.generate_encrypted_keys_list()

    # Assert
    assert len(keys) == 1
    key = keys[0]
    assert key.container == MODEL_ID
    assert key.certificate == 1
    assert key.encrypted_key_base64 == base64.b64encode("encrypted".encode()).decode()


def test_upload_calls_upload_many(mocker, grantaccess):
    # Arrange
    spy = mocker.patch(PATCH_GRANTACCESS.format("EncryptedKey.upload_many"))
    keys = [TestEncryptedKey()]

    # Act
    grantaccess.upload(keys)

    # Assert
    spy.assert_called_once_with(keys)
