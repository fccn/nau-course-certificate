import logging
import logging.config
import datetime
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms
import tempfile
import os.path
from os import path

logger = logging.getLogger(__name__)

def digital_sign_pdf(pdf_data_in: bytes, config : dict, language : str) -> bytes:
    """Create a digital signature of a PDF file byte array.

    Args:
        pdf_data_in (bytes): The byte array of the PDF file to be digital sign
        config (dict): A configuration dictionary like:
            {
                CERTIFICATE_P12: ./digital_signature_dev/sign-pdf.dev.nau.fccn.pt.p12
                SIGNATURE_BOX: 742,30,810,60
                CONTACT: ajuda@nau.edu.pt
                LOCATION: Lisboa
                REASON: 
                    pt-pt: Certificado de curso assinado digitalmente por NAU
                    en: Digitally signed course certificate by NAU
            }
        language (str): The language code 'pt-pt' or 'en'

    Returns:
        bytes: The PDF byte array digital signed
    """
    def _signature_img_path(language : str):
        signature_img_base_path = "./static/images/digital_sign/digital_signature_"
        signature_img_path = signature_img_base_path + language + ".png"
        signature_img_path = signature_img_path if path.exists(signature_img_base_path + language + ".png") else (signature_img_base_path + "_en.png")
        return signature_img_path

    def _get_config_value(config, language: str, default_value):       
        if type(config) is str:
            return config
        if type(config) is dict:
            by_lang = config.get(language)
            if type(by_lang) is not str:
                logger.warn("Incorrect configuration on the digital signature configuration")
                return default_value
            return by_lang
        return default_value

    def _signaturebox(config):
        signature_box_config_value = _get_config_value(config, language, "50,50,100,100")
        signature_box_strs = signature_box_config_value.split(",")
        signature_box_ints = [int(i) for i in signature_box_strs]
        return tuple(signature_box_ints)

    signature_img_path = _signature_img_path(language)
    signaturebox = _signaturebox(config.get("signaturebox"))
    contact = _get_config_value(config.get("contact"), language, "contact@exaple.com")
    location = _get_config_value(config.get("location"), language, "Some city")
    reason = _get_config_value(config.get("reason"), language, "Digitally signed course certificate")
    date = (datetime.datetime.utcnow() - datetime.timedelta(hours=12)).strftime('%Y%m%d%H%M%S+00\'00\'')

    dct = {
        "sigflags": 3,
        "sigpage": 0,
        "signaturebox": signaturebox,
        "signature_img": signature_img_path,
        "contact": contact,
        "location": location,
        "reason": reason,
        "signingdate": date,
    }

    p12_certificate_path = config.get('CERTIFICATE_P12_PATH')
    p12_password_as_bytes = str.encode(config.get("CERTIFICATE_P12_PASSWORD"))
    algorithm = config.get('SIGNATURE_ALGORITHM', "sha256")

    with open(p12_certificate_path, "rb") as fp:
        p12 = pkcs12.load_key_and_certificates(
            fp.read(), p12_password_as_bytes, backends.default_backend()
        )

    certificate_private_key = p12[0]
    certificate = p12[1]
    othercerts = p12[2]

    pdf_signature = cms.sign(pdf_data_in, dct, certificate_private_key, certificate, othercerts, algorithm)
    pdf = pdf_data_in + pdf_signature
    return pdf

